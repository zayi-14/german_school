from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import Course, Student, Registration, Feedback
from .forms import UserRegistrationForm, StudentForm, RegistrationForm, FeedbackForm
from django.conf import settings
import os

# --- WhatsApp helper functions ---
def send_whatsapp_via_meta(phone_to_send, message_text):
    """
    Example using Meta WhatsApp Cloud API via requests.
    You must set environment variables:
      WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_ACCESS_TOKEN, OWNER_WHATSAPP_NUMBER
    """
    import requests, json
    phone_id = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')  # e.g. '1234567890'
    token = os.environ.get('WHATSAPP_ACCESS_TOKEN')
    if not phone_id or not token:
        print("WhatsApp Meta credentials missing.")
        return False
    url = f"https://graph.facebook.com/v17.0/{phone_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_to_send,
        "type": "text",
        "text": {"body": message_text}
    }
    resp = requests.post(url, headers=headers, json=payload)
    return resp.status_code in (200, 201)


def send_whatsapp_via_twilio(to_number, message_text):
    # Using Twilio's Python helper
    from twilio.rest import Client
    tw_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    tw_token = os.environ.get('TWILIO_AUTH_TOKEN')
    tw_from = os.environ.get('TWILIO_WHATSAPP_FROM')  # e.g. 'whatsapp:+1415XXXXXXX'
    if not (tw_sid and tw_token and tw_from):
        print("Twilio config missing")
        return False
    client = Client(tw_sid, tw_token)
    msg = client.messages.create(body=message_text, from_=tw_from, to=f"whatsapp:{to_number}")
    return msg.sid is not None

# --- views ---
from .models import Feedback

def home(request):
    latest_courses = Course.objects.all()[:6]   # your existing logic
    enrolled_ids = []  # if you have this

    # Load approved testimonials
    testimonials = Feedback.objects.filter(is_approved=True).order_by('-created_at')[:6]

    levels = [
        ('A1', 'Beginner A1'),
        ('A2', 'Elementary A2'),
        ('B1', 'Intermediate B1'),
        ('B2', 'Upper Intermediate B2'),
    ]

    context = {
        'latest_courses': latest_courses,
        'enrolled_ids': enrolled_ids,
        'levels': levels,
        'testimonials': testimonials,
    }
    return render(request, 'courses/home.html', context)


def courses_list(request):
    selected_level = request.GET.get('level')
    courses = Course.objects.all()

    # Apply level filter
    if selected_level:
        courses = courses.filter(level=selected_level)

    filter_applied = bool(selected_level)

    # Fetch enrolled courses for logged-in student
    enrolled_course_ids = []
    if request.user.is_authenticated:
        student = Student.objects.filter(user=request.user).first()
        if student:
            enrolled_course_ids = list(
                Registration.objects.filter(student=student).values_list('course_id', flat=True)
            )

    # LEVEL TABS for the UI
    levels = [
        ('A1', 'A1 Beginner'),
        ('A2', 'A2 Elementary'),
        ('B1', 'B1 Intermediate'),
        ('B2', 'B2 Upper Intermediate'),
    ]

    return render(request, 'courses/courses.html', {
        'courses': courses,
        'levels': levels,                   # ⭐ Required for the tab buttons
        'selected_level': selected_level,
        'filter_applied': filter_applied,
        'enrolled_course_ids': enrolled_course_ids,
    })





def register_view(request):
    if request.method == 'POST':
        # Extract POST data manually (since we are not using Django forms on UI)
        username = request.POST.get('username')
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        course_id = request.POST.get('course')

        # Backend validation
        if not all([username, full_name, email, phone, password, confirm_password]):
            messages.error(request, "All fields are required.")
            return redirect('courses:register')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('courses:register')

        # Create Django user
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('courses:register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect('courses:register')

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email
        )

        # Create Student profile
        student = Student.objects.create(
            user=user,
            full_name=full_name,
            email=email,
            phone=phone,
        )

        # Register for course only if selected
        registration = None
        if course_id:
            try:
                course = Course.objects.get(id=course_id)
                registration = Registration.objects.create(
                    student=student,
                    course=course
                )
            except Course.DoesNotExist:
                pass  # Ignore if invalid course ID

        # WhatsApp notification to owner
        owner_whatsapp = os.environ.get('OWNER_WHATSAPP_NUMBER')

        if registration:
            message_text = (
                f"New registration:\n"
                f"Name: {student.full_name}\n"
                f"Email: {student.email}\n"
                f"Phone: {student.phone}\n"
                f"Course: {registration.course.title} ({registration.course.code})\n"
                f"Registered at: {registration.registered_at}"
            )
        else:
            message_text = (
                f"New registration (no course selected):\n"
                f"Name: {student.full_name}\n"
                f"Email: {student.email}\n"
                f"Phone: {student.phone}"
            )

        sent = False
        if owner_whatsapp:
            if os.environ.get('WHATSAPP_ACCESS_TOKEN'):
                sent = send_whatsapp_via_meta(owner_whatsapp, message_text)
            elif os.environ.get('TWILIO_ACCOUNT_SID'):
                sent = send_whatsapp_via_twilio(owner_whatsapp, message_text)

        messages.success(request, "Registration successful! You can now login.")
        return redirect('courses:login')

    # GET request
    courses = Course.objects.all()  # For dropdown
    return render(request, 'courses/register.html', {
        "courses": courses
    })


from django.contrib.auth.decorators import login_required

def login_view(request):
    if request.method == 'POST':
        uname = request.POST.get('username')
        pw = request.POST.get('password')
        user = authenticate(request, username=uname, password=pw)
        if user:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('courses:home')
        else:
            messages.error(request, "Invalid credentials.")
    return render(request, 'courses/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, "Logged out.")
    return redirect('courses:home')


@login_required
def select_course(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    student = Student.objects.filter(user=request.user).first()
    if not student:
        messages.error(request, "You need to complete your student profile first.")
        return redirect('courses:register')

    Registration.objects.create(student=student, course=course)
    messages.success(request, f"You have successfully selected {course.title}.")
    return redirect('courses:courses')


def about(request):
    return render(request, 'courses/about.html')


def contact(request):
    if request.method == 'POST':
        # handle contact message or send email; keep simple
        messages.success(request, "Thanks for contacting us. We'll reply soon.")
        return redirect('courses:contact')
    return render(request, 'courses/contact.html')

@login_required
def profile_view(request):
    student = Student.objects.filter(user=request.user).first()
    registrations = Registration.objects.filter(student=student)

    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('courses:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = StudentForm(instance=student)

    return render(request, 'courses/profile.html', {
        'student': student,
        'form': form,
        'registrations': registrations,
    })


@login_required
def delete_course(request, course_id):
    student = Student.objects.filter(user=request.user).first()
    registration = Registration.objects.filter(student=student, course_id=course_id).first()
    if registration:
        registration.delete()
        messages.info(request, "Course removed successfully.")
    else:
        messages.error(request, "Course not found or already deleted.")
    return redirect('courses:profile')


@login_required
def give_feedback(request):
    student = Student.objects.filter(user=request.user).first()

    if not student:
        messages.error(request, "You must complete your profile to give feedback.")
        return redirect('courses:profile')

    # Must be enrolled to give feedback
    if not Registration.objects.filter(student=student).exists():
        messages.error(request, "Enroll in a course before giving feedback.")
        return redirect('courses:profile')

    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            fb = form.save(commit=False)
            fb.student = student
            fb.save()
            messages.success(request, "Thank you! Your feedback has been submitted.")
            return redirect('courses:profile')
    else:
        form = FeedbackForm()

    return render(request, 'courses/feedback_form.html', {'form': form})
