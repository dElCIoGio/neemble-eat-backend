from datetime import datetime, timezone
import pytz


def now_in_luanda():
    """Returns the current datetime in the Luanda, Angola timezone (WAT, UTC+1)."""
    return datetime.now(timezone.utc)


def to_luanda_timezone(value: datetime):
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(pytz.timezone("Africa/Luanda"))