import json

def sse_event(data, event: str | None = None) -> str:
    """Format a Server-Sent Events frame."""
    out = ""
    if event:
        out += f"event: {event}\n"
    if isinstance(data, (dict, list)):
        data = json.dumps(data, default=str)
    for line in str(data).splitlines():
        out += f"data: {line}\n"
    return out + "\n"
