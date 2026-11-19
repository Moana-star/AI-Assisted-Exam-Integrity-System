from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Attendance, AuditLog, BiometricProfile, Evidence, Examination, ExaminationRegistration, ExaminationRoom, Incident, Invigilator, ManualReview, MonitoringEvent, Notification, ProhibitedObjectRule, Seat, SeatAssignment, Student, User, VerificationLog

admin.site.register(User, UserAdmin)
admin.site.register([Student, Invigilator, Examination, ExaminationRegistration, ExaminationRoom, Seat, SeatAssignment, Notification, Incident, Evidence, ProhibitedObjectRule, MonitoringEvent, BiometricProfile, Attendance, VerificationLog, ManualReview, AuditLog])
