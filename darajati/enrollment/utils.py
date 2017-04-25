from django.utils import timezone
import datetime, calendar


def get_offset_time(time, offset_hours):
    return time + datetime.timedelta(hours=offset_hours)


def now():
    return timezone.localtime(timezone.now())


def today():
    return now().date()


def current_day():
    return calendar.day_name[today().weekday()]