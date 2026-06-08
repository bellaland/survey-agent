import re


class InstructionParser:
    def extract_number(self, text: str) -> int | None:
        numbers = re.findall(r"\d+", text)
        return int(numbers[-1]) if numbers else None

    def extract_option_label(self, text: str) -> str | None:
        patterns = [
            r'choose ["\']?([A-Z])["\']?',
            r'select ["\']?([^"\'.]+)["\']?',
            r'pick ["\']?([^"\'.]+)["\']?',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
