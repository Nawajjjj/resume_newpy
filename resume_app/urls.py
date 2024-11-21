# resume_app/urls.py
from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path('', views.home, name='home'),  # Root URL mapped to home view
    path("logout/", views.logout_view, name='logout'),
    path('signup/', views.signup, name='signup'),  # Add this line
    path('upload/', views.upload_certificate, name='upload_certificate'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('certificates/', views.certificate_list, name='certificate_list'),
    path('delete_certificate/<int:cert_id>/', views.delete_certificate, name='delete_certificate'),
    path('generate_resume/', views.generate_resume, name='generate_resume'),
    path('profile/', views.profile, name='profile'),  # Add this line for profile view
    path('generate_resume/', views.generate_resume, name='generate_resume'),
    path('login/', views.custom_login_view, name='login'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
