import re

def get_str_from_food_dict(food_dict: dict):
    return ", ".join([f"{int(value)} {key}" for key, value in food_dict.items()])

def extract_session_id(session_str: str):
    match = re.search(r"sessions/(.*?)(/|$)", session_str)
    if match:
        return match.group(1)
    return ""