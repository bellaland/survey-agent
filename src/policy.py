from src.models.answer_plan import AnswerPlan
from src.models.question import Question


class Policy:
    def decide(self, question: Question) -> AnswerPlan:
        if question.type == "instruction":
            return AnswerPlan(
                qid=question.qid, action="continue", answer=None, policy="instruction"
            )
        if question.type == "multiple_choice":
            return AnswerPlan(
                qid=question.qid,
                action="select",
                answer=question.options[0].value,
                policy="default_multiple_choice",
            )
        if question.type == "slider":
            return AnswerPlan(
                qid=question.qid,
                action="set_slider",
                answer=50,
                policy="default_slider",
            )
        if question.type == "text":
            return AnswerPlan(
                qid=question.qid,
                action="type",
                answer="Test response.",
                policy="default_text",
            )
        return AnswerPlan(
            qid=question.qid,
            action="skip",
            answer=None,
            policy="unsupported_question_type",
            confidence=0.0,
        )
