from src.models.question import Question
from src.policy import Policy


def test_policy_instruction_continue():
    q = Question(qid="q1", text="Press next", type="instruction", selector="#q1")
    plan = Policy().decide(q)
    assert plan.action == "continue"


def test_policy_text_type():
    q = Question(qid="q2", text="Type anything", type="text", selector="#q2")
    plan = Policy().decide(q)
    assert plan.action == "type"


def test_policy_slider_set_slider():
    q = Question(qid="q3", text="Move slider", type="slider", selector="#q3")
    plan = Policy().decide(q)
    assert plan.action == "set_slider"
