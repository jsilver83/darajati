from django.utils import timezone
import datetime, calendar


def get_previous_week(date):
    return date + datetime.timedelta(days=-7)


def get_next_week(date):
    return date + datetime.timedelta(days=7)


def get_start_end_dates_of_the_week(date):

    start = date - datetime.timedelta(days=(date.weekday() + 1) % 7)
    end = start + datetime.timedelta(days=4)
    return start, end


def get_dates_in_between(date):
    dates = []
    start, end = get_start_end_dates_of_the_week(date)
    delta = end - start
    for i in range(delta.days + 1):
        dates.append(start + datetime.timedelta(days=i))
    return dates


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


def to_string(*args):
    sentence = ' '
    for arg in args:
        sentence += str(arg) + ' '
    return sentence
