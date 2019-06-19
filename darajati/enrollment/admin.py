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
    autocomplete_fields = ('course_offering', )
    search_fields = ('crn', 'code', 'course_offering__course__code', )
    list_display = ('id', 'course_offering', 'crn', 'code')
    list_filter = ('course_offering__semester', 'course_offering__course', 'active', )


class EnrollmentAdmin(ModelAdminMixin, SimpleHistoryAdmin):
    autocomplete_fields = ('section', 'student', )
    history_list_display = ['letter_grade', 'section', 'active', 'comment', 'updated_by']
    list_filter = ('section__course_offering__semester', 'section__course_offering__course', 'active', 'letter_grade', )
    list_display = ('id', 'student', 'semester_code', 'course_code', 'section_code', 'register_date',
                    'letter_grade', 'active', 'updated_on')
    search_fields = ['student__university_id']
    readonly_fields = ('updated_by', )

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
    search_fields = ('semester__code', 'course__code', )


class CoordinatorAdmin(admin.ModelAdmin):
    autocomplete_fields = ('course_offering', 'instructor', )
    fields = ('course_offering', 'instructor')
    list_filter = ('course_offering__semester', 'course_offering__course', )
    list_display = ('instructor_id', 'instructor', 'semester', 'course')

    def instructor_id(self, obj):
        return obj.instructor.user.id

    def instructor(self, obj):
        return obj.instructor.user.username

    def semester(self, obj):
        return obj.course_offering.semester.code

    def course(self, obj):
        return obj.course_offering.course.code


class InstructorAdmin(admin.ModelAdmin):
    autocomplete_fields = ('user', )
    list_filter = ('active', 'user__is_superuser', 'user__is_staff', )
    list_display = ('english_name', 'arabic_name', 'kfupm_email', 'mobile', 'active', )
    search_fields = ['english_name', 'arabic_name', 'user__username', 'mobile', ]

    def kfupm_email(self, obj):
        try:
            return '%s@kfupm.edu.sa' % obj.user.username
        except AttributeError:
            pass


class StudentAdmin(admin.ModelAdmin):
    autocomplete_fields = ('user', )
    list_filter = ('active', )
    list_display = ('english_name', 'arabic_name', 'university_id', 'kfupm_email', 'mobile', 'active', )
    search_fields = ['english_name', 'arabic_name', 'university_id', 'user__username', 'mobile', ]

    def kfupm_email(self, obj):
        try:
            return '%s@kfupm.edu.sa' % obj.user.username
        except:
            pass


admin.site.register(Semester, SemesterAdmin)
admin.site.register(Section, SectionAdmin)
admin.site.register(Enrollment, EnrollmentAdmin)
admin.site.register(CourseOffering, CourseOfferingAdmin)

admin.site.register(Student, StudentAdmin)
admin.site.register(Instructor, InstructorAdmin)
admin.site.register(Department)
admin.site.register(Course)
admin.site.register(Coordinator, CoordinatorAdmin)
