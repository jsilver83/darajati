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
    re_path(r'^login/$', views.login, {'template_name': 'login.html', 'redirect_authenticated_user': True},
            name='login'),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^impersonate/', include('impersonate.urls')),
    path('logout/', views.logout, {'next_page': settings.LOGOUT_REDIRECT_URL}, name='logout'),
)

urlpatterns += i18n_patterns(
    re_path(r'', include('enrollment.urls', namespace='enrollment')),
    re_path(r'attendance/', include('attendance.urls', namespace='attendance')),
    re_path(r'grade/', include('grade.urls', namespace='grade')),
    re_path(r'banner-integration/',
            include('banner_integration.urls', namespace='banner_integration')),
)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
                      re_path(r'^debug/', include(debug_toolbar.urls)),
                  ] + urlpatterns
