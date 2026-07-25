from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python versions before 3.9
    ZoneInfo = None


MALAYSIA_TZ_LABEL = "MYT"


def malaysia_now() -> datetime:
    if ZoneInfo is not None:
        return datetime.now(ZoneInfo("Asia/Kuala_Lumpur"))
    return datetime.now(timezone(timedelta(hours=8), MALAYSIA_TZ_LABEL))
