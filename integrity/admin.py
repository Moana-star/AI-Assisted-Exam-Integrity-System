from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Attendance, AuditLog, BiometricProfile, Evidence, Examination, ExaminationRegistration, ExaminationRoom, Incident, Invigilator, ManualReview, MonitoringEvent, Notification, ProhibitedObjectRule, Seat, SeatAssignment, Student, User, VerificationLog

@admin.register(BiometricProfile)
class BiometricProfileAdmin(admin.ModelAdmin):
    list_display = ('student', 'enrollment_status', 'enrollment_date', 'facial_capture')
    readonly_fields = ('facial_capture',)

admin.site.register(User, UserAdmin)
admin.site.register([Student, Invigilator, Examination, ExaminationRegistration, ExaminationRoom, Seat, SeatAssignment, Notification, Incident, Evidence, ProhibitedObjectRule, MonitoringEvent, Attendance, VerificationLog, ManualReview, AuditLog])
