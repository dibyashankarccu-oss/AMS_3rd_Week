from typing import List, Dict, Any

logs_buffer: List[Dict[str, Any]] = []


def add_log(log: Dict[str, Any]):
    logs_buffer.append(log)

    if len(logs_buffer) > 100:
        logs_buffer.pop(0)


def get_logs():
    return list(reversed(logs_buffer))