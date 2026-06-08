# Survey Agent for AI Detection Research

## Introduction
The agent is built to fill in surveys published on Qualdric automatically. It can parse survey pages, classify question types, generate answers, fill responses, verify completion, and store execution results.

It has passed all tests, dry run and two versions of survey (https://chicagobooth.az1.qualtrics.com/jfe/form/SV_b45QVOdJ2RUaiZ8) (https://chicagobooth.az1.qualtrics.com/jfe/form/SV_diBKdZgvVeZVDkG).

## How To Run
Get started with setup as below.
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install
```
Then set the survey URL in scripts/run.py.
```bash
URL = "https://chicagobooth.az1.qualtrics.com/jfe/form/SV_b45QVOdJ2RUaiZ8"
```
Next run the project.
```bash
python -m scripts.run
```

Regarding reCAPTCHA or visual math/verification questions, the agent will pause and wait for a human to complete the question and press Enter in Command Line to continue with the agent.

Screenshots are stored in `logs/screenshots`. Results are stored in `logs/survey.db`.
