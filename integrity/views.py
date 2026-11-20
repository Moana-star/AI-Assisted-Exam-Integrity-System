import base64
import csv
import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import ExaminationForm, RegistrationForm, StudentForm
from .models import Attendance, AuditLog, BiometricProfile, Examination, ExaminationRegistration, ExaminationRoom, Incident, ManualReview, MonitoringEvent, Notification, SeatAssignment, Student, VerificationLog
from .permissions import role_required
from .services.fingerprint_service import enroll as enroll_fingerprint
from .services.face_service import enroll as enroll_face
from .services.verification_service import verify as verify_biometrics

User = get_user_model()

def login_entry(request):
    """Always start at the login screen when the site root is opened."""
    return redirect('login')

def register(request):
    if request.user.is_authenticated: return redirect('dashboard')
    form = RegistrationForm(request.POST or None)
    if form.is_valid():
        data = form.cleaned_data
        with transaction.atomic():
            user = User.objects.create_user(username=data['username'], email=data['email'], password=data['password'], role=User.Roles.STUDENT, is_active=False)
            Student.objects.create(user=user, admission_number=data['admission_number'], full_name=data['full_name'], course=data['course'], department=data['department'])
        return render(request, 'registration_submitted.html', {'username': user.username})
    return render(request, 'register.html', {'form': form})

@role_required('admin')
def pending_accounts(request):
    pending = User.objects.filter(is_active=False, role__in=[User.Roles.STUDENT, User.Roles.INVIGILATOR]).select_related('student_profile').order_by('date_joined')
    return render(request, 'accounts/pending.html', {'pending_accounts': pending})

@role_required('admin')
def approve_account(request, user_id):
    user = get_object_or_404(User, pk=user_id, is_active=False)
    if request.method == 'POST':
        user.is_active = True; user.save(update_fields=['is_active'])
        AuditLog.objects.create(user=request.user, action='account_approved', description=f'Approved account {user.username}')
        messages.success(request, f'{user.username} can now sign in.')
    return redirect('pending_accounts')

@login_required
def dashboard(request):
    notifications = Notification.objects.filter(recipient__isnull=True)
    if hasattr(request.user, 'invigilator_profile'): notifications = notifications | Notification.objects.filter(recipient=request.user.invigilator_profile)
    context = {'students_count': Student.objects.count(), 'exams_count': Examination.objects.count(), 'verified_count': Attendance.objects.filter(attendance_status='present').count(), 'reviews_count': ManualReview.objects.filter(decision='pending').count(), 'upcoming': Examination.objects.filter(examination_date__gte=timezone.localdate()).order_by('examination_date')[:5], 'recent_logs': VerificationLog.objects.select_related('student','examination').order_by('-timestamp')[:6], 'notifications': notifications.order_by('-created_at')[:6]}
    if request.user.role == 'student': return render(request, 'dashboard/student_dashboard.html', context)
    if request.user.role == 'invigilator': return render(request, 'dashboard/invigilator_dashboard.html', context)
    return render(request, 'dashboard/admin_dashboard.html', context)

@role_required('admin')
def students(request): return render(request, 'students/student_list.html', {'students': Student.objects.select_related('user').order_by('full_name')})

@role_required('admin')
def student_add(request):
    form = StudentForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        student = form.save(); AuditLog.objects.create(user=request.user, action='student_created', description=f'Created {student.admission_number}'); messages.success(request, 'Student account created.'); return redirect('students')
    return render(request, 'students/student_form.html', {'form': form, 'title': 'Register student'})

@role_required('admin')
def examinations(request): return render(request, 'examinations/examination_list.html', {'examinations': Examination.objects.order_by('-examination_date')})

@role_required('admin')
def examination_add(request):
    form = ExaminationForm(request.POST or None)
    if form.is_valid(): form.save(); messages.success(request, 'Examination created.'); return redirect('examinations')
    return render(request, 'examinations/examination_form.html', {'form': form, 'title': 'Create examination'})

@role_required('admin','student')
def enrollment(request):
    student = getattr(request.user, 'student_profile', None)
    if request.method == 'POST' and student:
        profile, _ = BiometricProfile.objects.get_or_create(student=student); reference, fp = enroll_fingerprint(student); profile.fingerprint_reference = reference
        try: face_bytes = base64.b64decode(request.POST.get('face_data','').split(',',1)[-1])
        except Exception: face_bytes = b''
        template, face = enroll_face(face_bytes)
        if template:
            profile.facial_template = template
            profile.facial_capture.save(f'{student.admission_number}_capture.jpg', ContentFile(face_bytes), save=False)
        profile.enrollment_status = 'enrolled' if template else 'fingerprint_only'; profile.enrollment_date = timezone.now(); profile.save(); messages.success(request, f'Enrollment saved. {fp.message} {face.message}')
    return render(request, 'biometrics/enrollment.html', {'student': student, 'profile': getattr(student, 'biometric_profile', None)})

@role_required('admin','invigilator')
def verification(request):
    result = None
    if request.method == 'POST':
        examination = get_object_or_404(Examination, pk=request.POST.get('examination_id'), status='active')
        student = get_object_or_404(Student, pk=request.POST.get('student_id'))
        profile = BiometricProfile.objects.filter(student=student).first()
        try: face_bytes = base64.b64decode(request.POST.get('face_data', '').split(',', 1)[-1])
        except Exception: face_bytes = b''
        result = verify_biometrics(profile, profile.facial_template if profile else '', face_bytes)
        VerificationLog.objects.create(student=student, examination=examination, fingerprint_result=result['fingerprint_result'], facial_result=result['facial_result'], overall_result=result['overall_result'], reviewing_invigilator=getattr(request.user, 'invigilator_profile', None))
        if result['overall_result'] != 'verified':
            Notification.objects.create(examination=examination, student=student, category=Notification.Category.VERIFICATION, priority=Notification.Priority.HIGH, title='Biometric verification requires review', message=f"Fingerprint: {result['fingerprint_result']}; face: {result['facial_result']}.")
        else:
            messages.success(request, 'Candidate verified. Attendance may be recorded.')
    return render(request, 'biometrics/verification.html', {'examinations': Examination.objects.filter(status='active'), 'students': Student.objects.all(), 'result': result})

@role_required('admin','invigilator')
def attendance(request): return render(request, 'attendance/attendance_list.html', {'records': Attendance.objects.select_related('student','examination').order_by('-verification_timestamp')})

@role_required('admin','invigilator')
def reports(request): return render(request, 'reports/reports_dashboard.html', {'total': Attendance.objects.count(), 'present': Attendance.objects.filter(attendance_status='present').count(), 'reviews': ManualReview.objects.filter(decision='pending').count()})

@role_required('admin', 'invigilator')
def attendance_export(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance-report.csv"'
    writer = csv.writer(response); writer.writerow(['Admission number', 'Student', 'Examination', 'Status', 'Timestamp'])
    for row in Attendance.objects.select_related('student', 'examination').order_by('-verification_timestamp'):
        writer.writerow([row.student.admission_number, row.student.full_name, row.examination.code, row.attendance_status, row.verification_timestamp.isoformat()])
    return response

@role_required('admin', 'invigilator')
def notifications_api(request):
    qs = Notification.objects.select_related('examination', 'student').filter(recipient__isnull=True) | Notification.objects.select_related('examination', 'student').filter(recipient__user=request.user)
    unread_only = request.GET.get('unread') == '1'
    if unread_only: qs = qs.filter(read_at__isnull=True)
    data = [{'id': n.id, 'title': n.title, 'message': n.message, 'category': n.category, 'priority': n.priority, 'read': n.is_read, 'created_at': n.created_at.isoformat()} for n in qs.order_by('-created_at')[:50]]
    return JsonResponse({'notifications': data})

@role_required('admin', 'invigilator')
def notification_mark_read(request, notification_id):
    notification = get_object_or_404(Notification, pk=notification_id)
    if notification.recipient and notification.recipient.user_id != request.user.id and request.user.role != 'admin':
        return JsonResponse({'error': 'Not allowed.'}, status=403)
    if request.method != 'POST': return JsonResponse({'error': 'POST required.'}, status=405)
    notification.read_at = timezone.now(); notification.save(update_fields=['read_at'])
    return JsonResponse({'id': notification.id, 'read': True})

@role_required('admin', 'invigilator')
def monitoring_event_create(request):
    if request.method != 'POST': return JsonResponse({'error': 'POST required.'}, status=405)
    try: payload = json.loads(request.body or '{}')
    except json.JSONDecodeError: return JsonResponse({'error': 'Invalid JSON.'}, status=400)
    examination = get_object_or_404(Examination, pk=payload.get('examination_id'))
    event = MonitoringEvent.objects.create(examination=examination, student_id=payload.get('student_id') or None, event_type=payload.get('event_type', MonitoringEvent.EventType.OBJECT_DETECTED), detected_class=payload.get('detected_class', ''), confidence=payload.get('confidence'), metadata=payload.get('metadata', {}))
    Notification.objects.create(examination=examination, student=event.student, category=Notification.Category.MONITORING, priority=Notification.Priority.HIGH, title='Monitoring event requires review', message=f'{event.get_event_type_display()}: {event.detected_class or "observable event"}.')
    return JsonResponse({'id': event.id, 'review_required': True}, status=201)

@role_required('admin', 'invigilator')
def examination_access_check(request):
    if request.method != 'POST': return JsonResponse({'error': 'POST required.'}, status=405)
    try: payload = json.loads(request.body or '{}')
    except json.JSONDecodeError: return JsonResponse({'error': 'Invalid JSON.'}, status=400)
    examination = get_object_or_404(Examination, pk=payload.get('examination_id'))
    student = get_object_or_404(Student, pk=payload.get('student_id'))
    registered = ExaminationRegistration.objects.filter(examination=examination, student=student).exists()
    assignment = SeatAssignment.objects.filter(examination=examination, student=student).select_related('seat').first()
    allowed = registered and assignment is not None
    if not allowed:
        Notification.objects.create(examination=examination, student=student, category=Notification.Category.ACCESS, priority=Notification.Priority.HIGH, title='Examination access requires review', message='The candidate is not registered or has no assigned seat.')
    return JsonResponse({'allowed': allowed, 'registered': registered, 'seat': assignment.seat.number if assignment else None, 'review_required': not allowed})

@role_required('admin', 'invigilator')
def incident_create(request):
    if request.method != 'POST': return JsonResponse({'error': 'POST required.'}, status=405)
    try: payload = json.loads(request.body or '{}')
    except json.JSONDecodeError: return JsonResponse({'error': 'Invalid JSON.'}, status=400)
    examination = get_object_or_404(Examination, pk=payload.get('examination_id'))
    invigilator = getattr(request.user, 'invigilator_profile', None)
    incident = Incident.objects.create(examination=examination, student_id=payload.get('student_id') or None, reported_by=invigilator, title=payload.get('title', 'Manual review required'), description=payload.get('description', ''))
    return JsonResponse({'id': incident.id, 'status': incident.status}, status=201)

@role_required('admin', 'invigilator')
def operations(request):
    notifications = Notification.objects.filter(recipient__isnull=True)
    if hasattr(request.user, 'invigilator_profile'): notifications = notifications | Notification.objects.filter(recipient=request.user.invigilator_profile)
    return render(request, 'monitoring/operations.html', {
        'notifications': notifications.order_by('-created_at')[:20],
        'events': MonitoringEvent.objects.select_related('examination', 'student')[:30],
        'incidents': Incident.objects.select_related('examination', 'student')[:20],
        'rooms': ExaminationRoom.objects.prefetch_related('seats')[:20],
        'examinations': Examination.objects.filter(status__in=['active', 'upcoming'])[:20],
    })
