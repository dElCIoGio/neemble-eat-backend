from datetime import datetime, timezone
from typing import Optional

import pytz


def now_in_luanda() -> datetime:
    """Returns the current datetime in the Luanda, Angola timezone (WAT, UTC+1)."""
    return datetime.now(timezone.utc)


def to_luanda_timezone(value: Optional[datetime]) -> Optional[datetime]:
    """Convert a datetime to the Africa/Luanda timezone.

    If ``value`` is ``None`` the function safely returns ``None`` instead of
    raising an :class:`AttributeError` when attempting to access
    ``value.tzinfo``.  This ensures callers can pass optional datetimes without
    additional ``None`` checks.
    """

    if value is None:
        return None

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(pytz.timezone("Africa/Luanda"))
