from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.home, name='home'),
    path('courses/', views.courses_list, name='courses'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('select-course/<int:course_id>/', views.select_course, name='select_course'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/delete-course/<int:course_id>/', views.delete_course, name='delete_course'),

]
