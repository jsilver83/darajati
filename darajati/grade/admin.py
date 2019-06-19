from django.contrib import admin

from darajati.mixin import ModelAdminMixin
from .models import *

from simple_history.admin import SimpleHistoryAdmin


class GradeFragmentAdmin(admin.ModelAdmin):
    autocomplete_fields = ('course_offering', 'section', )
    list_display = ('course_offering', 'category', 'description', 'weight',
                    'boundary_type',  'allow_change', 'entry_in_percentages', 'entry_start_date', 'entry_end_date', )
    list_filter = ('course_offering__semester', 'course_offering__course', 'boundary_type', 'entry_end_date',
                   'entry_in_percentages', 'allow_change')
    search_fields = ('category', 'description', )
    readonly_fields = ('updated_by', )


class LetterGradeAdmin(admin.ModelAdmin):
    autocomplete_fields = ('course_offering', 'section', )
    list_display = ('course_offering', 'section', 'letter_grade', 'cut_off_point', 'updated_on', 'updated_by')
    list_filter = ('course_offering__semester', 'course_offering__course', 'letter_grade', )
    readonly_fields = ('updated_by', )


class StudentGradeAdmin(ModelAdminMixin, SimpleHistoryAdmin):
    autocomplete_fields = ('enrollment', 'grade_fragment', )
    list_display = ('enrollment', 'grade_fragment', 'grade_quantity', 'remarks', 'updated_on', 'updated_by')
    list_filter = ('grade_fragment__course_offering__semester', 'grade_fragment__course_offering__course',
                   'grade_fragment__category',)
    search_fields = ('enrollment__student__university_id', 'enrollment__section__code', 'grade_fragment__description')
    readonly_fields = ('updated_by', )


admin.site.register(GradeFragment, GradeFragmentAdmin)
admin.site.register(LetterGrade, LetterGradeAdmin)
admin.site.register(StudentGrade, StudentGradeAdmin)
