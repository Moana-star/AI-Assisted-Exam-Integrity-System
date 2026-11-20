from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_entry, name='site-entry'), path('dashboard/', views.dashboard, name='dashboard'), path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'), path('register/', views.register, name='register'), path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/pending/', views.pending_accounts, name='pending_accounts'), path('accounts/<int:user_id>/approve/', views.approve_account, name='approve_account'),
    path('students/', views.students, name='students'), path('students/add/', views.student_add, name='student_add'),
    path('examinations/', views.examinations, name='examinations'), path('examinations/add/', views.examination_add, name='examination_add'),
    path('biometrics/enroll/', views.enrollment, name='enrollment'), path('biometrics/verify/', views.verification, name='verification'),
    path('attendance/', views.attendance, name='attendance'), path('reports/', views.reports, name='reports'),
    path('reports/attendance.csv', views.attendance_export, name='attendance_export'),
    path('api/notifications/', views.notifications_api, name='notifications_api'),
    path('api/notifications/<int:notification_id>/read/', views.notification_mark_read, name='notification_mark_read'),
    path('api/monitoring/events/', views.monitoring_event_create, name='monitoring_event_create'),
    path('api/examination-access/check/', views.examination_access_check, name='examination_access_check'),
    path('api/incidents/', views.incident_create, name='incident_create'),
    path('operations/', views.operations, name='operations'),
]
