from django.contrib import admin
from django.urls import path, include, re_path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('worklist/', include('worklist.urls')),
    path('accounts/', include('accounts.urls')),
    re_path(r'^celery-progress/', include('celery_progress.urls')),
]
