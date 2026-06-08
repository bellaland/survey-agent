from src.config import AppConfig
from src.models.question import Question
from src.models.answer_plan import AnswerPlan
from src.tool_router import ToolRouter
from src.instruction_parser import InstructionParser


class Generator:
    def __init__(self, config: AppConfig):
        self.config = config
        self.tool_router = ToolRouter()
        self.instruction_parser = InstructionParser()

    def generate(self, question: Question, plan: AnswerPlan) -> AnswerPlan:
        if plan.action in {"continue", "skip"}:
            return plan
        plan.tool_used = self.tool_router.route(question, plan)
        if question.type in {"multiple_choice", "dropdown"}:
            plan.answer = self._choose_single_option(question, plan)
        elif question.type == "checkbox":
            plan.answer = self._choose_checkbox_options(question)
        elif question.type == "slider":
            plan.answer = self._generate_slider_answer(question)
        elif question.type == "text":
            plan.answer = self._generate_text_answer(question, plan)
        return plan

    def _choose_single_option(self, question: Question, plan: AnswerPlan) -> str | None:
        if not question.options:
            return None
        if plan.policy == "identity_disclosure":
            for option in question.options:
                if option.label.lower().strip(" .") in {"no", "false"}:
                    return option.value
        if plan.policy == "demographic":
            for key, value in self.config.profile.demographic.items():
                key_lower = key.lower()
                text_lower = question.text.lower()
                if key_lower in text_lower or (
                    key_lower == "age" and "old are you" in text_lower
                ):
                    matched = self._match_option(question, value)
                    if matched is not None:
                        return matched
        target = self.instruction_parser.extract_option_label(question.text)
        if target:
            matched = self._match_option(question, target)
            if matched is not None:
                return matched
        preference_order = self.config.profile.preferences.get(
            "option_preference_order",
            "neutral,neither,no preference,prefer not",
        )
        for preferred in preference_order.split(","):
            matched = self._match_option(question, preferred.strip())
            if matched is not None:
                return matched
        return question.options[0].value

    def _choose_checkbox_options(self, question: Question) -> list[str]:
        if not question.options:
            return []
        raw_max_selected = self.config.profile.preferences.get(
            "checkbox_max_selected",
            "1",
        )
        try:
            max_selected = max(1, int(raw_max_selected))
        except ValueError:
            max_selected = 1
        selected: list[str] = []
        for option in question.options:
            if option.value is not None:
                selected.append(option.value)
            if len(selected) >= max_selected:
                break
        return selected

    def _generate_slider_answer(self, question: Question) -> int:
        target = self.instruction_parser.extract_number(question.text)
        if target is not None:
            return target
        return int(self.config.profile.preferences.get("default_slider_value", "98"))

    def _generate_text_answer(self, question: Question, plan: AnswerPlan) -> str:
        if plan.policy == "identity_disclosure":
            return self.config.profile.text_answers.get(
                "ai_disclosure",
                "No, this response was not completed by an agent.",
            )
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
