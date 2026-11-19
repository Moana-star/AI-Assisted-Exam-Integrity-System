from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.core.validators import FileExtensionValidator
from django.db import models

class UserManager(DjangoUserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields['role'] = 'admin'
        user = self.model(username=username, email=email or '', **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = 'admin', 'Administrator'
        INVIGILATOR = 'invigilator', 'Invigilator'
        STUDENT = 'student', 'Student'
    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.STUDENT)
    objects = UserManager()

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    admission_number = models.CharField(max_length=40, unique=True)
    full_name = models.CharField(max_length=160)
    course = models.CharField(max_length=160)
    department = models.CharField(max_length=160)
    profile_photo = models.ImageField(upload_to='student_photos/', blank=True, null=True, validators=[FileExtensionValidator(['jpg','jpeg','png'])])
    registration_date = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f'{self.admission_number} — {self.full_name}'

class Invigilator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='invigilator_profile')
    staff_number = models.CharField(max_length=40, unique=True)
    full_name = models.CharField(max_length=160)
    department = models.CharField(max_length=160)
    def __str__(self): return self.full_name

class Examination(models.Model):
    class Status(models.TextChoices):
        UPCOMING='upcoming','Upcoming'; ACTIVE='active','Active'; COMPLETED='completed','Completed'; ARCHIVED='archived','Archived'
    title = models.CharField(max_length=180)
    code = models.CharField(max_length=40, unique=True)
    course = models.CharField(max_length=160)
    examination_date = models.DateField()
    start_time = models.TimeField(); end_time = models.TimeField()
    venue = models.CharField(max_length=160)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UPCOMING)
    invigilators = models.ManyToManyField(Invigilator, blank=True, related_name='examinations')
    def __str__(self): return f'{self.code} — {self.title}'

class ExaminationRoom(models.Model):
    name = models.CharField(max_length=120, unique=True)
    location = models.CharField(max_length=180, blank=True)
    capacity = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self): return self.name

class Seat(models.Model):
    room = models.ForeignKey(ExaminationRoom, on_delete=models.CASCADE, related_name='seats')
    number = models.CharField(max_length=20)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['room', 'number'], name='unique_seat_number_per_room')]
        ordering = ['room', 'number']

    def __str__(self): return f'{self.room} — {self.number}'

class SeatAssignment(models.Model):
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name='seat_assignments')
    seat = models.ForeignKey(Seat, on_delete=models.PROTECT, related_name='assignments')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='seat_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['examination', 'seat'], name='unique_seat_per_examination'),
            models.UniqueConstraint(fields=['examination', 'student'], name='unique_student_seat_per_examination'),
        ]

    def __str__(self): return f'{self.student} — {self.examination}: {self.seat}'

class Notification(models.Model):
    class Category(models.TextChoices):
        SECURITY = 'security', 'Security event'
        VERIFICATION = 'verification', 'Verification'
        ATTENDANCE = 'attendance', 'Attendance'
        ACCESS = 'access', 'Examination access'
        MONITORING = 'monitoring', 'AI monitoring'
        INCIDENT = 'incident', 'Incident'
        SYSTEM = 'system', 'System'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        NORMAL = 'normal', 'Normal'
        HIGH = 'high', 'High'
        URGENT = 'urgent', 'Urgent'

    examination = models.ForeignKey(Examination, null=True, blank=True, on_delete=models.CASCADE, related_name='notifications')
    student = models.ForeignKey(Student, null=True, blank=True, on_delete=models.SET_NULL, related_name='notifications')
    recipient = models.ForeignKey(Invigilator, null=True, blank=True, on_delete=models.CASCADE, related_name='notifications')
    category = models.CharField(max_length=20, choices=Category.choices)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.NORMAL)
    title = models.CharField(max_length=180)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def is_read(self): return self.read_at is not None

    def __str__(self): return self.title

class Incident(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        UNDER_REVIEW = 'under_review', 'Under review'
        RESOLVED = 'resolved', 'Resolved'

    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name='incidents')
    student = models.ForeignKey(Student, null=True, blank=True, on_delete=models.SET_NULL, related_name='incidents')
    reported_by = models.ForeignKey(Invigilator, null=True, blank=True, on_delete=models.SET_NULL, related_name='reported_incidents')
    title = models.CharField(max_length=180)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    review_reason = models.TextField(blank=True)
    review_outcome = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(Invigilator, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_incidents')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self): return self.title

class Evidence(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='evidence')
    file = models.FileField(upload_to='incident_evidence/', validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'pdf'])])
    description = models.CharField(max_length=240, blank=True)
    uploaded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='uploaded_evidence')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self): return f'Evidence for {self.incident}'

class ProhibitedObjectRule(models.Model):
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name='object_rules')
    object_class = models.CharField(max_length=80)
    minimum_confidence = models.DecimalField(max_digits=4, decimal_places=3, default=0.500)
    enabled = models.BooleanField(default=True)
    interaction_threshold = models.PositiveIntegerField(default=3)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['examination', 'object_class'], name='unique_object_rule_per_exam')]

class MonitoringEvent(models.Model):
    class EventType(models.TextChoices):
        OBJECT_DETECTED = 'object_detected', 'Object detected'
        OBJECT_INTERACTION = 'object_interaction', 'Object interaction'
        MULTIPLE_FACES = 'multiple_faces', 'Multiple faces'
        NO_FACE = 'no_face', 'No face'
        CAMERA_DISCONNECTED = 'camera_disconnected', 'Camera disconnected'

    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name='monitoring_events')
    student = models.ForeignKey(Student, null=True, blank=True, on_delete=models.SET_NULL, related_name='monitoring_events')
    event_type = models.CharField(max_length=30, choices=EventType.choices)
    detected_class = models.CharField(max_length=80, blank=True)
    confidence = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    observed_at = models.DateTimeField(auto_now_add=True)
    reviewed = models.BooleanField(default=False)
    review_outcome = models.CharField(max_length=40, blank=True)

    class Meta:
        ordering = ['-observed_at']

class ExaminationRegistration(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_registrations')
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name='registrations')
    registration_date = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['student','examination'], name='unique_exam_registration')]

class BiometricProfile(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='biometric_profile')
    fingerprint_reference = models.CharField(max_length=128, blank=True)
    facial_template = models.TextField(blank=True)
    enrollment_status = models.CharField(max_length=30, default='not_enrolled')
    enrollment_date = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

class Attendance(models.Model):
    class Status(models.TextChoices): PRESENT='present','Present'; MANUAL='manual','Manual review'; ABSENT='absent','Absent'
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name='attendance_records')
    attendance_status = models.CharField(max_length=20, choices=Status.choices, default=Status.PRESENT)
    verification_timestamp = models.DateTimeField(auto_now_add=True)
    verification_method = models.CharField(max_length=40, default='biometric')
    class Meta:
        constraints = [models.UniqueConstraint(fields=['student','examination'], name='unique_attendance')]

class VerificationLog(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='verification_logs')
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name='verification_logs')
    fingerprint_result = models.CharField(max_length=20)
    facial_result = models.CharField(max_length=20)
    overall_result = models.CharField(max_length=30)
    timestamp = models.DateTimeField(auto_now_add=True)
    reviewing_invigilator = models.ForeignKey(Invigilator, null=True, blank=True, on_delete=models.SET_NULL)

class ManualReview(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='manual_reviews')
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name='manual_reviews')
    reason = models.TextField(); invigilator = models.ForeignKey(Invigilator, null=True, blank=True, on_delete=models.SET_NULL)
    decision = models.CharField(max_length=30, default='pending'); notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

class AuditLog(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=80); description = models.TextField(); timestamp = models.DateTimeField(auto_now_add=True)
