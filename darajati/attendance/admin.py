from django.contrib import admin
from .models import *


class ScheduledPeriodAdmin(admin.ModelAdmin):
    list_filter = ('day',)
    list_display = ('id', 'section', 'day', 'title', 'start_time',
                    'end_time', 'location')
    search_fields = ('id', 'section', 'day', 'title', 'start_time',
                     'end_time', 'location')


class AttendanceInstanceAdmin(admin.ModelAdmin):
    list_display = ('period', 'date', 'comment')
    search_fields = ('period', 'date', 'comment')


class AttendanceAdmin(admin.ModelAdmin):
    readonly_fields = ('updated_by',)
    list_filter = ('status', )
    list_display = ('attendance_instance', 'status')
    search_fields = ('attendance_instance', 'status')

admin.site.register(ScheduledPeriod, ScheduledPeriodAdmin)
admin.site.register(AttendanceInstance, AttendanceInstanceAdmin)
admin.site.register(Attendance, AttendanceAdmin)
