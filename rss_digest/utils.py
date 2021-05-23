"""Miscellaneous helper functions."""
from datetime import datetime, tzinfo
from typing import Union

import pytz


def utc_to_tz(utc: datetime, tz: Union[str, tzinfo]) -> datetime:
    """Convert a :class:`datetime` object in UTC to some other timezone.

    :param utc: The UTC datetime.
    :param tz: A :class:`tzinfo` object, or a string describing the
        desired timezone.

    :return: A new datetime in the desired timezone.

    """
    if not isinstance(tz, tzinfo):
        tz = pytz.timezone(tz)
    return utc.astimezone(tz)