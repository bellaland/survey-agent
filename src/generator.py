import re
from src.config import AppConfig
from src.models.question import Question
from src.models.answer_plan import AnswerPlan
from src.tool_router import ToolRouter


class Generator:
    def __init__(self, config: AppConfig):
        self.config = config
        self.tool_router = ToolRouter()

    def generate(self, question: Question, plan: AnswerPlan) -> AnswerPlan:
        if plan.action in {"continue", "skip"}:
            return plan
        tool = self.tool_router.route(question, plan)
        plan.tool_used = tool
        if question.type in {"multiple_choice", "dropdown"}:
            plan.answer = self._choose_single_option(question)
            return plan
        elif question.type == "checkbox":
            plan.answer = self._choose_checkbox_options(question)
            return plan
        elif question.type == "slider":
            plan.answer = self._generate_slider_answer(question)
            return plan
        elif question.type == "text":
            plan.answer = self._generate_text_answer(question, plan)
            return plan
        return plan

    def _choose_single_option(self, question: Question) -> str | None:
        if not question.options:
            return None
        text = question.text.lower()
        for key, value in self.config.profile.demographic.items():
            if key.lower() in text:
                matched = self._match_option(question, value)
                if matched is not None:
                    return matched
        for preferred in ["neutral", "neither", "no preference", "prefer not"]:
            matched = self._match_option(question, preferred)
            if matched is not None:
                return matched
        return question.options[0].value

    def _choose_checkbox_options(self, question: Question) -> list[str]:
        if not question.options:
            return []
        first_value = question.options[0].value
        return [first_value] if first_value is not None else []

    def _generate_slider_answer(self, question: Question) -> int:
        numbers = re.findall(r"\d+", question.text)
        if numbers:
            return int(numbers[-1])
        return 50

    def _generate_text_answer(self, question: Question, plan: AnswerPlan) -> str:
        text = question.text.lower()
        if plan.policy == "factual":
            return self.config.profile.text_answers.get(
                "default_factual_fallback",
                "Unable to answer from available information.",
            )
        for key, value in self.config.profile.demographic.items():
            if key.lower() in text:
                return value
        if "programming" in text or "language" in text:
            return self.config.profile.preferences.get("default_language", "Python")
        return self.config.profile.text_answers.get(
            "default_opinion",
            "I do not have a strong preference.",
        )

    def _match_option(self, question: Question, target: str) -> str | None:
        target_lower = target.lower()
        for option in question.options:
            label = option.label.lower()
            value = str(option.value).lower() if option.value is not None else ""
            if target_lower in label or target_lower in value:
                return option.value
        return None
