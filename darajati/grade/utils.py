from decimal import *


def display_average_of_value(average):
    FourPLACES = Decimal(10) ** -4
    return average.quantize(FourPLACES)