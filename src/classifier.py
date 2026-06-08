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
        text = question.text.lower()

        if "side by side" in text:
            return "side_by_side"

        if (
            "rank order" in text
            or "please rank" in text
            or "rank the following" in text
        ):
            return "ranking"

        if "matrix table" in text or "rate the following" in text:
            return "matrix"

        if "form field" in text or "name and contact information" in text:
            return "form"

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
        if question.type == "instruction":
            return "instruction"

        if "press 'next'" in text or "press next" in text:
            return "instruction"

        if question.type == "slider" and any(
            k in text for k in ["navigate", "set", "number", "move"]
        ):
            return "instruction"

        if any(
            k in text
            for k in [
                "are you a bot",
                "are you an ai",
                "artificial intelligence",
                "automated agent",
                "chatgpt",
                "large language model",
                "did you use ai",
            ]
        ):
            return "ai_disclosure"

        demographic_keywords = [
            "how old are you",
            "what is your age",
            "your age",
            "age range",
            "gender",
            "income",
            "education level",
            "highest level of education",
            "race",
            "ethnicity",
        ]

        if any(k in text for k in demographic_keywords):
            return "demographic"

        if any(
            k in text
            for k in ["calculate", "what is 2", "what is 3", "based on the passage"]
        ):
            return "factual"

        return "opinion"
