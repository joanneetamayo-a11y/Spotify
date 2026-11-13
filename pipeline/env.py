"""Load simple local credentials only for explicit paid execution; never log values."""
import os
from pathlib import Path

NAMES = {"OPENAI_API_KEY", "ANTHROPIC_API_KEY", "TYPESAFE_API_KEY"}

def load_local_env(path):
    path = Path(path)
    if not path.exists():
        return
    values = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"Invalid .env format on line {number}; expected NAME=value")
        name, value = line.split("=", 1)
        name, value = name.strip(), value.strip()
        if name not in NAMES:
            continue
        if name in values:
            raise ValueError(f"Duplicate credential name on line {number}")
        if value[:1] in (chr(34), chr(39)):
            if len(value) < 2 or value[-1] != value[0]:
                raise ValueError(f"Unclosed quote on .env line {number}")
            value = value[1:-1]
        values[name] = value
    for name, value in values.items():
        if value and not os.environ.get(name):
            os.environ[name] = value
