from src.handlers.multi_choice import MultipleChoiceHandler
from src.handlers.slider import SliderHandler
from src.handlers.text import TextHandler


class Registry:
    def __init__(self):
        self.handlers = {
            "multiple_choice": MultipleChoiceHandler(),
            "text": TextHandler(),
            "slider": SliderHandler(),
        }

    def get(self, question_type: str):
        return self.handlers[question_type]
