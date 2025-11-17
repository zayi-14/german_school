from django.db import models
from django.contrib.auth.models import User

class Course(models.Model):
    LEVELS = (
        ('A1', 'A1 - Beginner'),
        ('A2', 'A2 - Elementary'),
        ('B1', 'B1 - Intermediate'),
        ('B2', 'B2 - Upper-Intermediate'),
    )
    title = models.CharField(max_length=200)
    code = models.CharField(max_length=10, unique=True)
    level = models.CharField(max_length=3, choices=LEVELS)
    duration_weeks = models.PositiveIntegerField()
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.title} ({self.level})"


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    def __str__(self):
        return self.full_name


class Registration(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    registered_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.student.full_name} -> {self.course.code}"
class Feedback(models.Model):
    RATING_CHOICES = [
        (1, "1 ★"),
        (2, "2 ★"),
        (3, "3 ★"),
        (4, "4 ★"),
        (5, "5 ★"),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=5)
    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)  # Admin approves for homepage

    def __str__(self):
        return f"{self.student.full_name} — {self.rating}★"

