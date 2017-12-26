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

class CourseOfferingAdmin(admin.ModelAdmin):
    list_display = ('id', 'semester', 'course', 'attendance_entry_window', 'allow_change')
    list_filter = ('coordinated', )

admin.site.register(Semester, SemesterAdmin)
admin.site.register(Section, SectionAdmin)
admin.site.register(CourseOffering, CourseOfferingAdmin)

admin.site.register(Department)
admin.site.register(Course)
admin.site.register(Coordinator)
