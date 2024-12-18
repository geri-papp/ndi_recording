from datetime import datetime, timezone


def to_utc(dt: datetime) -> datetime:
    """
    Convert a datetime object to UTC.

    - If the datetime is naive, assume it's in UTC.
    - If the datetime is timezone-aware, convert it to UTC with adjustment.

    Args:
        dt (datetime): A timezone-aware or naive datetime object.

    Returns:
        datetime: A timezone-aware datetime object in UTC.
    """
    if dt.tzinfo is None:
        # Naive datetime, assume UTC
        return dt.replace(tzinfo=timezone.utc)
    else:
        # Aware datetime, convert to UTC with proper adjustment
        return dt.astimezone(timezone.utc)
