from src.config import load_config
from src.generator import Generator
from src.models.answer_plan import AnswerPlan
from src.models.question import Option, Question


def test_slider_uses_instruction_number():
    config = load_config()
    q = Question(
        qid="q1",
        text="Please move the slider to 73.",
        type="slider",
        selector="#q1",
    )
    plan = AnswerPlan(
        qid="q1", action="set_slider", answer=None, policy="follow_instruction"
    )
    out = Generator(config).generate(q, plan)
    assert out.answer == 73


def test_multiple_choice_selects_requested_option():
    config = load_config()
    q = Question(
        qid="q2",
        text="Please choose B.",
        type="multiple_choice",
        selector="#q2",
        options=[
            Option(label="A", value="A"),
            Option(label="B", value="B"),
        ],
    )
    plan = AnswerPlan(
        qid="q2", action="select", answer=None, policy="default_multiple_choice"
    )
    out = Generator(config).generate(q, plan)
    assert out.answer == "B"


def test_text_uses_profile_default():
    config = load_config()
    q = Question(
        qid="q3",
        text="Type anything you like.",
        type="text",
        selector="#q3",
    )
    plan = AnswerPlan(qid="q3", action="type", answer=None, policy="default_text")
    out = Generator(config).generate(q, plan)
    assert isinstance(out.answer, str)
    assert len(out.answer) > 0
