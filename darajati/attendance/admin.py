from django.contrib import admin

from darajati.mixin import ModelAdminMixin
from simple_history.admin import SimpleHistoryAdmin

from .models import *


class ScheduledPeriodAdmin(admin.ModelAdmin):
    list_filter = (
        'section__course_offering',
        'section__course_offering__course',
        'day',
        'title',
    )
    list_display = ('id', 'section', 'instructor_assigned', 'day', 'title', 'start_time',
                    'end_time', 'location')
    search_fields = ('section__code', 'instructor_assigned__user__username',
                     'instructor_assigned__english_name', 'instructor_assigned__arabic_name',
                     'day', 'title', 'start_time', 'end_time', 'location')


class AttendanceInstanceAdmin(admin.ModelAdmin):
    list_filter = ('period__section__course_offering', )
    date_hierarchy = 'date'
    list_display = ('period', 'date', 'comment')
    search_fields = ('period', 'date', 'comment')


class AttendanceAdmin(SimpleHistoryAdmin):
    readonly_fields = ('updated_by', 'attendance_instance', 'enrollment')
    date_hierarchy = 'attendance_instance__date'
    list_filter = ('attendance_instance__period__section__course_offering', 'status',)
    list_display = ('attendance_instance', 'enrollment', 'status')
    search_fields = ('enrollment__student__english_name', 'enrollment__student__arabic_name',
                     'enrollment__student__university_id', 'status')


class ExcuseAdmin(admin.ModelAdmin):
    list_filter = ('excuse_type', 'includes_exams', 'created_by', 'applied_by', )
    date_hierarchy = 'start_date'
    list_display = ('university_id', 'student', 'start_date', 'end_date', 'excuse_type', 'includes_exams',
                    'attachments', 'created_on', 'created_by', 'applied_on', 'applied_by', )
    search_fields = ('university_id', 'description', 'created_by__username', 'applied_by__username', )


admin.site.register(ScheduledPeriod, ScheduledPeriodAdmin)
admin.site.register(AttendanceInstance, AttendanceInstanceAdmin)
admin.site.register(Attendance, AttendanceAdmin)
admin.site.register(Excuse, ExcuseAdmin)
