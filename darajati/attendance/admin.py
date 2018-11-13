from django.contrib import admin

from .models import *


class ScheduledPeriodAdmin(admin.ModelAdmin):
    list_filter = (
        'section__course_offering',
        'section__course_offering__course',
        'day',
        'title',
        'instructor_assigned',
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


# TODO: Implement History
class AttendanceAdmin(admin.ModelAdmin):
    readonly_fields = ('updated_by',)
    date_hierarchy = 'attendance_instance__date'
    list_filter = ('attendance_instance__period__section__course_offering', 'status',)
    list_display = ('attendance_instance', 'enrollment', 'status')
    search_fields = ('attendance_instance', 'enrollment', 'status')


admin.site.register(ScheduledPeriod, ScheduledPeriodAdmin)
admin.site.register(AttendanceInstance, AttendanceInstanceAdmin)
admin.site.register(Attendance, AttendanceAdmin)
