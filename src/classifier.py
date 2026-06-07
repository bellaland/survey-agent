from src.models.question import Question, QuestionType, QuestionCategory


class Classifier:
    def classify(self, question: Question) -> Question:
        question.type = self._classify_type(question)
        question.category = self._classify_category(question)
        return question

    def classify_all(self, questions: list[Question]) -> list[Question]:
        return [self.classify(q) for q in questions]

    def _classify_type(self, question: Question) -> QuestionType:
        s = question.input_summary

        if s.range_count > 0 or s.slider_count > 0:
            return "slider"

        if s.textarea_count > 0 or s.text_input_count > 0:
            return "text"

        if s.select_count > 0:
            return "dropdown"

        if s.checkbox_count > 0:
            return "checkbox"

        if s.radio_count > 0:
            return "multiple_choice"

        if len(question.options) > 0:
            return "multiple_choice"

        return "instruction"

    def _classify_category(self, question: Question) -> QuestionCategory:
        text = question.text.lower()

        if "press 'next'" in text or "press next" in text:
            return "instruction"

        if any(
            k in text
            for k in [
                "bot",
                "ai",
                "artificial intelligence",
                "automated agent",
                "chatgpt",
            ]
        ):
            return "ai_disclosure"

        if any(
            k in text
            for k in ["age", "gender", "income", "education", "race", "ethnicity"]
        ):
            return "demographic"

        if any(k in text for k in ["calculate", "what is", "according to", "based on"]):
            return "factual"

        if question.type == "slider" and any(
            k in text for k in ["navigate", "set", "number"]
        ):
            return "instruction"

        if question.type == "instruction":
            return "instruction"

        return "opinion"
