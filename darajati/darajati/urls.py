"""darajati URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
    """

from django.urls import re_path, include, path
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.auth import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = i18n_patterns(
    path('login/', views.LoginView.as_view(template_name='login.html', redirect_authenticated_user=True), name='login'),
    path('admin/', admin.site.urls),
    re_path(r'^impersonate/', include('impersonate.urls')),
    path('logout/', views.LogoutView.as_view(next_page=settings.LOGOUT_REDIRECT_URL), name='logout'),
)

urlpatterns += i18n_patterns(
    # Enrollment
    re_path(r'', include('enrollment.urls', namespace='enrollment')),
    re_path(r'attendance/', include('attendance.urls', namespace='attendance')),
    re_path(r'grade/', include('grade.urls', namespace='grade')),
    re_path(r'banner-integration/', include('banner_integration.urls', namespace='banner_integration')),

    # Exams
    re_path(r'exam/', include('exam.urls', namespace='exam')),
)

urlpatterns += [
    path('explorer/', include('explorer.urls')),
    path('session_security/', include('session_security.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
                      path('__debug__/', include(debug_toolbar.urls)),
                  ] + urlpatterns
