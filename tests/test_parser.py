from src.instruction_parser import InstructionParser


def test_extract_number():
    parser = InstructionParser()
    assert parser.extract_number('Move slider to "50"') == 50
    assert parser.extract_number("Please set the value to 73.") == 73
    assert parser.extract_number("No number here") is None


def test_extract_option_label():
    parser = InstructionParser()
    assert parser.extract_option_label("Choose A.") == "A"
    assert parser.extract_option_label('Select "Strongly Agree".') == "Strongly Agree"
