from django.urls import path
from . import views
from .views import WorkListView, WorklistCreateView
app_name = 'worklist'
urlpatterns = [
    path('', views.WorkListView.as_view(), name='worklist'),
    path('login/', WorklistCreateView.as_view()),
    path('index/', WorkListView.as_view(), name='index'),
    path('export/excel/<int:usage_id>/', views.export_usage_xls, name='export_excel'),
]

