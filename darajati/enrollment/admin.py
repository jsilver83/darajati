from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .models import *

from simple_history.admin import SimpleHistoryAdmin


admin.site.site_header = _('Darajati Admin')
admin.site.index_title = _('Darajati Administration')


class SemesterAdmin(admin.ModelAdmin):
    list_display = ('id', 'start_date', 'end_date', 'grade_fragment_deadline', 'code')
    search_fields = ('start_date', 'end_date')


class SectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'course_offering', 'crn', 'code')
    list_filter = ('active', )


class EnrollmentAdmin(SimpleHistoryAdmin):
    history_list_display = ['letter_grade', 'section', 'active', 'comment', 'updated_by']
    list_filter = ('active', 'letter_grade', 'section__code', 'section__course_offering__course__code',
                   'section__course_offering__semester__code')
    list_display = ('id', 'student', 'semester_code', 'course_code', 'section_code', 'register_date',
                    'letter_grade', 'active')
    search_fields = ['student__university_id']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'updated_by':
            field.queryset = field.queryset.filter(Q(instructor__isnull=False) or Q(is_staff=True))
        return field

    def semester_code(self, obj):
        return obj.section.course_offering.semester.code

    def course_code(self, obj):
        return obj.section.course_offering.course.code

    def section_code(self, obj):
        return obj.section.code


class CourseOfferingAdmin(admin.ModelAdmin):
    list_display = ('id', 'semester', 'course', 'attendance_entry_window', 'allow_change', 'formula')
    list_filter = ('coordinated', )
    list_editable = ('attendance_entry_window', 'formula')


class CoordinatorAdmin(admin.ModelAdmin):
    fields = ('course_offering', 'instructor')
    list_display = ('instructor_id', 'instructor', 'semester', 'course')

    def instructor_id(self, obj):
        return obj.instructor.user.id

    def instructor(self, obj):
        return obj.instructor.user.username

    def semester(self, obj):
        return obj.course_offering.semester.code

    def course(self, obj):
        return obj.course_offering.course.code


admin.site.register(Semester, SemesterAdmin)
admin.site.register(Section, SectionAdmin)
admin.site.register(Enrollment, EnrollmentAdmin)
admin.site.register(CourseOffering, CourseOfferingAdmin)

admin.site.register(Student)
admin.site.register(Instructor)
admin.site.register(Department)
admin.site.register(Course)
admin.site.register(Coordinator, CoordinatorAdmin)
