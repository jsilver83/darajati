from django.db.models import Q


"""
 ABOUT: this file is supposed to hold mixins that are shared across apps
"""


class ModelAdminMixin:
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'updated_by':
            field.queryset = field.queryset.filter(Q(instructor__isnull=False) or Q(is_staff=True))
        return field