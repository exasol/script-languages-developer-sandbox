def get_value_safe(key: str, object) -> str:
    if key in object:
        return object[key]
    else:
        return "n/a"
