import json
from pathlib import Path

FUNC_FILE = Path(__file__).with_name("func_assigne.json")

def load_func_assignments():
    with FUNC_FILE.open("r", encoding="utf-8") as f:
        raw = json.load(f)
        return {entry["hand"]: entry["functions"][0] for entry in raw}
    
assignments = load_func_assignments()
