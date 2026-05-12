from datetime import datetime


def compute_order_status(created_at: str, estimated_time: int):
    try:
        created = datetime.fromisoformat(created_at)
        elapsed = int((datetime.now() - created).total_seconds())
        remaining = max(0, estimated_time - elapsed)

        if elapsed < 5:
            status = "pending"
        elif elapsed < estimated_time:
            status = "preparing"
        else:
            status = "ready"

        return status, remaining
    except Exception:
        return "unknown", 0
