from src.handlers.multi_choice import MultipleChoiceHandler
from src.handlers.slider import SliderHandler
from src.handlers.text import TextHandler
from src.handlers.checkbox import CheckboxHandler
from src.handlers.dropdown import DropdownHandler
from src.handlers.form import FormHandler
from src.handlers.matrix import MatrixHandler
from src.handlers.ranking import RankingHandler
from src.handlers.side_by_side import SideBySideHandler


class Registry:
    def __init__(self):
        self.handlers = {
            "multiple_choice": MultipleChoiceHandler(),
            "text": TextHandler(),
            "slider": SliderHandler(),
            "checkbox": CheckboxHandler(),
            "dropdown": DropdownHandler(),
            "form": FormHandler(),
            "matrix": MatrixHandler(),
            "ranking": RankingHandler(),
            "side_by_side": SideBySideHandler(),
        }

    def get(self, question_type: str):
        if question_type not in self.handlers:
            raise ValueError(f"No handler registered for question type:{question_type}")
        return self.handlers[question_type]
