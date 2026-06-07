from src.models.question import Question
from src.models.answer_plan import AnswerPlan


class ToolRouter:
    def route(self, question: Question, plan: AnswerPlan) -> str | None:
        if plan.policy == "factual":
            return "calculator_or_context"
        if plan.policy == "demographic":
            return "profile"
        if plan.policy == "identity_disclosure":
            return "identity_policy"
        if plan.policy in {"default_text", "default_multiple_choice"}:
            return "profile"
        return None
