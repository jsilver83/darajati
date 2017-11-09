from django.contrib import admin
from .models import *


class GradeFragmentAdmin(admin.ModelAdmin):
    list_display = ('course_offering', 'section', 'category', 'description', 'weight', 'entry_start_date',
                    'entry_end_date', 'updated_on')
    list_filter = ('course_offering', 'entry_start_date', 'entry_end_date', 'entry_in_percentages', 'allow_change')


class LetterGradeAdmin(admin.ModelAdmin):
    list_display = ('course_offering', 'section', 'letter_grade', 'cut_off_point', 'updated_on', 'updated_by')


class StudentGradeAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'grade_fragment', 'grade_quantity', 'remarks', 'updated_on', 'updated_by')
    list_filter = ('grade_fragment',)


admin.site.register(GradeFragment, GradeFragmentAdmin)
admin.site.register(LetterGrade, LetterGradeAdmin)
admin.site.register(StudentGrade, StudentGradeAdmin)
