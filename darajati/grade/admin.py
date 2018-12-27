from django.contrib import admin

from darajati.mixin import ModelAdminMixin
from .models import *

from simple_history.admin import SimpleHistoryAdmin


class GradeFragmentAdmin(admin.ModelAdmin):
    list_display = ('course_offering', 'category', 'description', 'weight', 'boundary_type', 'allow_change',
                    'entry_in_percentages', 'entry_start_date', 'entry_end_date', )
    list_filter = ('course_offering', 'boundary_type', 'entry_end_date', 'entry_in_percentages', 'allow_change')


class LetterGradeAdmin(admin.ModelAdmin):
    list_display = ('course_offering', 'section', 'letter_grade', 'cut_off_point', 'updated_on', 'updated_by')


class StudentGradeAdmin(ModelAdminMixin, SimpleHistoryAdmin):
    list_display = ('enrollment', 'grade_fragment', 'grade_quantity', 'remarks', 'updated_on', 'updated_by')
    list_filter = ('grade_fragment__course_offering', 'grade_fragment',)


admin.site.register(GradeFragment, GradeFragmentAdmin)
admin.site.register(LetterGrade, LetterGradeAdmin)
admin.site.register(StudentGrade, StudentGradeAdmin)
