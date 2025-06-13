from datetime import datetime
import pytz


def now_in_luanda():
    """Returns the current datetime in the Luanda, Angola timezone (WAT, UTC+1)."""
    return datetime.now(pytz.timezone("Africa/Luanda"))
