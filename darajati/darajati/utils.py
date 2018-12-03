from decimal import *

from django.conf import settings

"""
 ABOUT: this file is supposed to hold utility functions that are shared across apps
"""


def decimal(value):
    getcontext().prec = settings.MAX_DIGITS
    return round(Decimal(value), settings.MAX_DECIMAL_POINT)


def size_format(b):
    """
    :param b: (file) size in bytes
    :return: humanized file size in terms of KB/MB/GB/TB
    """
    b = float(b)
    if b < 1000:
        return '%i' % b + 'B'
    elif 1000 <= b < 1000000:
        return '%.1f' % float(b / 1000) + ' KB'
    elif 1000000 <= b < 1000000000:
        return '%.1f' % float(b / 1000000) + ' MB'
    elif 1000000000 <= b < 1000000000000:
        return '%.1f' % float(b / 1000000000) + ' GB'
    elif 1000000000000 <= b:
        return '%.1f' % float(b / 1000000000000) + ' TB'
