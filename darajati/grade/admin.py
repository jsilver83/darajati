from django.contrib import admin
from .models import *


class GradeFragmentAdmin(admin.ModelAdmin):
    list_display = ('course_offering', 'section', 'category', 'description', 'weight', 'allow_entry', 'updated_on')
    list_filter = ('course_offering', 'allow_entry', 'entry_in_percentages', 'allow_change')
    readonly_fields = ('updated_by',)


class LetterGradeAdmin(admin.ModelAdmin):
    list_display = ('course_offering', 'section', 'letter_grade', 'cut_off_point', 'updated_on', 'updated_by')
    readonly_fields = ('updated_by',)


class StudentGradeAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'grade_fragment', 'grade_quantity', 'remarks', 'updated_on', 'updated_by')
    list_filter = ('grade_fragment',)
    readonly_fields = ('updated_by',)


admin.site.register(GradeFragment, GradeFragmentAdmin)
admin.site.register(LetterGrade, LetterGradeAdmin)
admin.site.register(StudentGrade, StudentGradeAdmin)
