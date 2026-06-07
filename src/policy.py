from src.models.answer_plan import AnswerPlan
from src.models.question import Question


class Policy:
    def decide(self, question: Question) -> AnswerPlan:
        if question.type == "instruction":
            return AnswerPlan(
                qid=question.qid, action="continue", answer=None, policy="instruction"
            )
        action_map = {
            "multiple_choice": "select",
            "checkbox": "check",
            "dropdown": "select",
            "slider": "set_slider",
            "text": "type",
        }
        action = action_map.get(question.type, "skip")
        if question.category == "demographic":
            policy_name = "demographic"
        elif question.category == "factual":
            policy_name = "factual"
        elif question.category == "ai_disclosure":
            policy_name = "identity_disclosure"
        elif question.category == "attention_check":
            policy_name = "attention_check"
        elif question.category == "instruction":
            policy_name = "follow_instruction"
        else:
            policy_name = f"default_{question.type}"

        return AnswerPlan(
            qid=question.qid,
            action=action,
            answer=None,
            policy=policy_name,
        )
