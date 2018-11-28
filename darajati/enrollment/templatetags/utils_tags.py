from django import template


register = template.Library()


@register.simple_tag
def modulo(num, val):
    return num % val


# NOTE: this is used in parallel formsets like in the markers page (3 markers in one row).
# It can be used in the attendance entry page too (4 forms in one row for ENGL courses).
@register.simple_tag
def counter_for_parallel_formsets(counter_based_1, columns):
    return int(counter_based_1 / columns) + 1
