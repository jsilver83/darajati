from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from django.utils.translation import ugettext_lazy as _

from .utils import if_null
from .models import *


class MarkerAdmin(SimpleHistoryAdmin):
    autocomplete_fields = ('instructor', 'exam_room', )
    history_list_display = ['instructor', 'exam_room', 'order', 'generosity_factor', 'is_a_monitor']
    list_filter = ('exam_room__exam_shift__settings__fragment__course_offering__semester',
                   'exam_room__exam_shift__settings__fragment__course_offering__course', 'order', 'is_a_monitor', )
    list_display = ('instructor', 'exam_room', 'order', 'generosity_factor', 'is_a_monitor', 'updated_by', )
    search_fields = ('exam_room__exam_shift__settings__fragment__course_offering__semester',
                     'exam_room__exam_shift__settings__fragment__course_offering__course', 'instructor__english_name',
                     'instructor__arabic_name', 'exam_room__room')
    readonly_fields = ('updated_by', )


class StudentPlacementAdmin(admin.ModelAdmin):
    autocomplete_fields = ('enrollment', 'exam_room', )
    list_filter = ('exam_room__exam_shift__settings__fragment__course_offering__semester',
                   'exam_room__exam_shift__settings__fragment__course_offering__course', 'exam_room__room',
                   'is_present', )
    list_display = ('enrollment', 'exam_room', 'is_present', 'shuffled_by', 'shuffled_on', )
    search_fields = ('enrollment__student__university_id', 'enrollment__student__english_name',
                     'enrollment__student__arabic_name', )
    readonly_fields = ('shuffled_by', 'shuffled_on', )


class StudentMarkAdmin(SimpleHistoryAdmin):
    autocomplete_fields = ('student_placement', 'marker', )
    history_list_display = ['student_placement', 'marker', 'mark']
    list_filter = ('marker__exam_room__exam_shift__settings__fragment__course_offering__semester',
                   'marker__exam_room__exam_shift__settings__fragment__course_offering__course',
                   'marker__exam_room__room', 'marker__order', )
    list_display = ('student_placement', 'marker', 'mark', 'get_generosity_factor', 'show_weighted_mark',
                    'updated_on', 'updated_by')
    search_fields = ('student_placement__enrollment__student__university_id', )
    readonly_fields = ('updated_by', )

    def get_queryset(self, request):
        return super(StudentMarkAdmin,self).get_queryset(request).select_related('marker')

    def show_weighted_mark(self, obj):
        if obj.mark:
            weighted = if_null(obj.mark, Decimal("0")) + if_null(obj.marker.generosity_factor, Decimal("0"))

            if weighted < Decimal("0.00"):
                return Decimal("0.00")
            elif weighted > Decimal("100.00"):
                return Decimal("100.00")
            else:
                return weighted
        else:
            return Decimal("0")

    show_weighted_mark.short_description = _('Weighted Mark')

    def get_generosity_factor(self, obj):
        return obj.marker.generosity_factor

    get_generosity_factor.short_description = _('Generosity Factor')
    get_generosity_factor.admin_order_field = 'marker__generosity_factor'


class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'capacity', 'updated_by', 'updated_on', )
    list_editable = ('location', 'capacity', )
    search_fields = ('name', 'location', )
    readonly_fields = ('updated_by', )


class ExamShiftAdmin(admin.ModelAdmin):
    list_display = ('settings', 'start_date', 'end_date', )
    list_editable = ('start_date', 'end_date', )
    list_filter = ('settings__fragment__course_offering__semester', 'settings__fragment__course_offering__course', )
    search_fields = ('settings__fragment__course_offering__semester', 'settings__fragment__course_offering__course',
                     'start_date', 'end_date', )


class ExamRoomAdmin(admin.ModelAdmin):
    autocomplete_fields = ('exam_shift', 'room', )
    list_display = ('exam_shift', 'room', 'capacity', 'remaining_seats', )
    list_filter = ('exam_shift__settings__fragment__course_offering__semester',
                   'exam_shift__settings__fragment__course_offering__course', 'exam_shift__settings__fragment',
                   'exam_shift', 'room', )
    list_editable = ('capacity', )
    search_fields = ('room', )


admin.site.register(ExamSettings)
admin.site.register(ExamShift, ExamShiftAdmin)
admin.site.register(StudentPlacement, StudentPlacementAdmin)
admin.site.register(Marker, MarkerAdmin)
admin.site.register(StudentMark, StudentMarkAdmin)
admin.site.register(Room, RoomAdmin)
admin.site.register(ExamRoom, ExamRoomAdmin)
