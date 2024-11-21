from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CertificateUploadForm, UserInformationForm, CustomUserCreationForm
from .models import Certificate
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import LoginForm
import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from .utils import extract_text_from_pdf, extract_information


def home(request):
    steps = [
        {"icon": "✏️", "title": "Upload Certificates", "description": "Upload your certificates.", "details": "Securely upload your certificates."},
        {"icon": "📄", "title": "Choose Template", "description": "Select a professional template.", "details": "Customizable templates to suit your style."},
        {"icon": "🔄", "title": "Preview Resume", "description": "View your resume in real-time.", "details": "Preview your resume before downloading."},
        {"icon": "📥", "title": "Download", "description": "Export your resume as a PDF.", "details": "Download your resume instantly."},
    ]

    features = [
        {'icon': 'fas fa-file-alt', 'title': 'OCR-Powered Resume Creation', 'description': 'Our advanced OCR analyzes your certificates and creates tailored, professional resumes in minutes.', 'details': 'Seamless, efficient resume creation.'},
        {'icon': 'fas fa-cloud-upload-alt', 'title': 'OCR-Powered Data Extraction', 'description': 'Our cutting-edge OCR accurately extracts certificate information, saving you time.', 'details': 'Fast and reliable OCR extraction!'},
        {'icon': 'fas fa-sync-alt', 'title': 'Technology Highlighting', 'description': 'Automatically identify and highlight key technologies to match job requirements.', 'details': 'Emphasize essential technologies effortlessly!'},
        {'icon': 'fas fa-download', 'title': 'Quick Turnaround', 'description': 'Generates your professional resume in less than 15 minutes.', 'details': 'Perfect for last-minute applications!'}
    ]

    return render(request, 'resume_app/home.html', {'steps': steps, 'features': features})


@login_required
def upload_certificate(request):
    if request.method == 'POST':
        form = CertificateUploadForm(request.POST, request.FILES)
        if form.is_valid():
            certificate = form.save(commit=False)
            certificate.user = request.user
            certificate.save()
            return redirect('certificate_list')
    else:
        form = CertificateUploadForm()
    return render(request, 'resume_app/upload_certificate.html', {'form': form})


@login_required
def certificate_list(request):
    certificates = Certificate.objects.filter(user=request.user)
    return render(request, 'resume_app/certificate_list.html', {'certificates': certificates})


def clean_text(text):
    text = re.sub(r'■+', ' ', text)  # Replace repeated ■ with space
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with a single space
    return text.strip()


def wrap_text(text, p, font, font_size, width):
    lines = []
    words = text.split(' ')
    current_line = []

    for word in words:
        current_line.append(word)
        line = ' '.join(current_line)

        if p.stringWidth(line, font, font_size) > width:  # Check if line exceeds width
            lines.append(' '.join(current_line[:-1]))
            current_line = [word]

    lines.append(' '.join(current_line))
    return lines


@login_required
def generate_resume(request):
    certificates = Certificate.objects.filter(user=request.user)

    if not certificates:
        return redirect('upload_certificate')

    extracted_data = []

    for certificate in certificates:
        text = extract_text_from_pdf(certificate.certificate_file.path)
        clean_description = clean_text(text)
        extracted_info = extract_information(clean_description)

        extracted_data.append({
            'certificate': certificate,
            'des': clean_description,
            'institution': extracted_info.get('institution', 'Not Found'),
            'date': extracted_info.get('date', 'Not Found'),
            'email': extracted_info.get('email', 'Not Found'),
            'phone': extracted_info.get('phone', 'Not Found'),
            'skills': extracted_info.get('skills', []),
        })

    if request.GET.get('download') == 'pdf':
        form = UserInformationForm(request.POST or None)
        if request.method == 'POST' and form.is_valid():
            user_data = form.cleaned_data
            name, phone, email = user_data['name'], user_data['phone'], user_data['email']
            linkedin, gmail = user_data.get('linkedin', ''), user_data.get('gmail', '')

            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            y_position = height - 100

            font, font_size = "Helvetica", 12
            p.setFont(font, font_size)

            p.setFont("Helvetica-Bold", 16)
            p.drawString(100, y_position, name)
            y_position -= 20
            p.setFont(font, font_size)
            p.drawString(100, y_position, f"Phone: {phone}")
            y_position -= 20
            p.drawString(100, y_position, f"Email: {email}")
            y_position -= 20
            if linkedin:
                p.drawString(100, y_position, f"LinkedIn: {linkedin}")
                y_position -= 20
            if gmail:
                p.drawString(100, y_position, f"Gmail: {gmail}")
                y_position -= 20

            y_position -= 40

            for idx, data in enumerate(extracted_data, 1):
                p.setFont("Helvetica-Bold", 14)
                p.drawString(100, y_position, f"Certificate {idx}:")
                y_position -= 20

                description_lines = wrap_text(data['des'], p, font, font_size, width - 200)
                p.setFont(font, font_size)
                for line in description_lines:
                    p.drawString(100, y_position, line)
                    y_position -= 14

                y_position -= 20

                if y_position < 100:
                    p.showPage()
                    p.setFont(font, font_size)
                    y_position = height - 100

            p.showPage()
            p.save()

            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="generated_resume.pdf"'
            return response

        return render(request, 'resume_app/generate_resume_form.html', {'form': form, 'extracted_data': extracted_data})

    return render(request, 'resume_app/generated_resume.html', {'extracted_data': extracted_data})


def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'resume_app/signup.html', {'form': form})


@login_required
def profile(request):
    return redirect('upload_certificate')


def about(request):
    return render(request, 'resume_app/about.html')


def contact(request):
    return render(request, 'resume_app/contact.html')


@login_required
def delete_certificate(request, cert_id):
    certificate = get_object_or_404(Certificate, id=cert_id, user=request.user)
    if request.method == 'POST':
        certificate.delete()
        return redirect('certificate_list')
    return render(request, 'resume_app/confirm_delete.html', {'certificate': certificate})


def logout_view(request):
    logout(request)
    return redirect("/")

def custom_login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')  # Replace 'home' with your desired redirect page
            else:
                form.add_error(None, "Invalid username or password")
    else:
        form = LoginForm()

    return render(request, "resume_app/login.html", {'form': form})
