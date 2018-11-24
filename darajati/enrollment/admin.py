from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from darajati.mixin import ModelAdminMixin
from .models import *

from simple_history.admin import SimpleHistoryAdmin


admin.site.site_header = _('Darajati Admin')
admin.site.index_title = _('Darajati Administration')


class SemesterAdmin(admin.ModelAdmin):
    list_display = ('code', 'start_date', 'end_date', 'grade_fragment_deadline', 'id', )
    search_fields = ('start_date', 'end_date')


class SectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'course_offering', 'crn', 'code')
    list_filter = ('course_offering', 'active', )


class EnrollmentAdmin(ModelAdminMixin, SimpleHistoryAdmin):
    history_list_display = ['letter_grade', 'section', 'active', 'comment', 'updated_by']
    list_filter = ('section__course_offering', 'active', 'letter_grade', 'section__course_offering__course',)
    list_display = ('id', 'student', 'semester_code', 'course_code', 'section_code', 'register_date',
                    'letter_grade', 'active')
    search_fields = ['student__university_id']

    def semester_code(self, obj):
        return obj.section.course_offering.semester.code

    def course_code(self, obj):
        return obj.section.course_offering.course.code

    def section_code(self, obj):
        return obj.section.code


class CourseOfferingAdmin(admin.ModelAdmin):
    list_display = ('id', 'semester', 'course', 'attendance_entry_window', 'allow_change', 'formula')
    list_filter = ('semester', 'course', 'coordinated', )
    list_editable = ('attendance_entry_window', 'formula')


class CoordinatorAdmin(admin.ModelAdmin):
    fields = ('course_offering', 'instructor')
    list_filter = ('course_offering', 'course_offering__course', )
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
