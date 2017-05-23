from django.contrib import admin
from .models import *
from django.utils.translation import ugettext_lazy as _


admin.site.site_header = _('Darajati Admin')
admin.site.index_title = _('Darajati Administration')

admin.site.register(UserProfile)
admin.site.register(Student)
admin.site.register(Instructor)
admin.site.register(Semester)
admin.site.register(Department)
admin.site.register(Course)
admin.site.register(Section)
admin.site.register(Enrollment)