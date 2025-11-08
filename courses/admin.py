from django.contrib import admin
from .models import Course, Student, Registration

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'code', 'level', 'duration_weeks', 'price')
    search_fields = ('title', 'code')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone')

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'registered_at')
    list_filter = ('registered_at',)
