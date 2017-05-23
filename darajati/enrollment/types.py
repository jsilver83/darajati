from django.utils.translation import ugettext_lazy as _


class RoundTypes:
    CEILING = 'ceil'
    FLOOR = 'floor'
    ROUND = 'round'
    NONE = 'none'

    @classmethod
    def choices(cls):
        return (
            (cls.CEILING, _('Ceiling')),
            (cls.FLOOR, _('Floor')),
            (cls.ROUND, _('Round')),
            (cls.NONE, _('None')),
        )
