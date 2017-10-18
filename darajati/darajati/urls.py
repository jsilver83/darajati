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

from django.conf.urls import url, include
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.auth import views

urlpatterns = i18n_patterns(
    url(r'^login/$', views.login, {'template_name': 'login.html', 'redirect_authenticated_user': True}, name='login'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^impersonate/', include('impersonate.urls')),
    url(r'^logout/$', views.logout, {'template_name': 'logout.html'}, name='logout'),
)

urlpatterns += i18n_patterns(
    url(r'', include('enrollment.urls', namespace='enrollment', app_name='enrollment')),
    url(r'attendance/', include('attendance.urls', namespace='attendance', app_name='attendance')),
    url(r'grade/', include('grade.urls', namespace='grade', app_name='grade')),
    url(r'banner-integration/', include('banner_integration.urls', namespace='banner_integration', app_name='banner_integration')),
)