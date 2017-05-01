from django.utils import timezone
import datetime, calendar


def get_offset_day(date, offset_days):
    return date + datetime.timedelta(days=offset_days), day_string(date + datetime.timedelta(days=offset_days))


def get_offset_time(time, offset_hours):
    return time + datetime.timedelta(hours=offset_hours)


def now():
    return timezone.localtime(timezone.now())


def today():
    return now().date()


def current_day():
    return calendar.day_name[today().weekday()]


def current_day_number():
    today().weekday()


def number_of_days(start_date, end_date):
    return (start_date - end_date).days


def day_string(date):
    return calendar.day_name[date.weekday()]