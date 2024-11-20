from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CertificateUploadForm, UserInformationForm
from .models import Certificate
import pytesseract
import pdfplumber
# import spacy
import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from .utils import extract_text_from_pdf, extract_information

# Load NLP model
# nlp = spacy.load('en_core_web_sm')


def home(request):
    steps = [
        {"icon": "✏️", "title": "Upload Certificates", "description": "Upload your certificates.", "details": "Securely upload your certificates."},
        {"icon": "📄", "title": "Choose Template", "description": "Select a professional template.", "details": "Customizable templates to suit your style."},
        {"icon": "🔄", "title": "Preview Resume", "description": "View your resume in real-time.", "details": "Preview your resume before downloading."},
        {"icon": "📥", "title": "Download", "description": "Export your resume as a PDF.", "details": "Download your resume instantly."},
    ]

    features = [
        {
            'icon': 'fas fa-file-alt',
            'title': 'OCR- Powered Resume Ceration',
            'description': 'Our advanced OCR analyzes your certificates and creates tailored, professional resumes in minutes.',
            'details': 'Our OCR feature provides a seamless, efficient experience in resume creation.'
        },
        {
            'icon': 'fas fa-cloud-upload-alt',
            'title': 'OCR-Powered Data Extraction',
            'description': 'Our cutting-edge OCR technology accurately extracts information from your certificates, saving your time and effort',
            'details': 'Fast and reliable OCR extraction for your certificates!'
        },
        {
            'icon': 'fas fa-sync-alt',
            'title': 'Technology Highlighting ',
            'description': 'Automatically identify and highlight key Technology from your uploaded certificates to match job requirements ',
            'details': 'Identify and emphasize essential technology effortlessly!'
        },
        {
            'icon': 'fas fa-download',
            'title': 'Quick Turnaround ',
            'description': 'Generates your professional resume in less than 15 minutes, perfect for last-minute applications',
            'details': 'Get a professional resume ready in no time!'
        }
    ]

    return render(request, 'resume_app/home.html', {'steps': steps, 'features': features})



@login_required
def upload_certificate(request):
    if request.method == 'POST':
        form = CertificateUploadForm(request.POST, request.FILES)
        if form.is_valid():
            certificate = form.save(commit=False)
            certificate.user = request.user  # Ensure the logged-in user is assigned to the certificate
            certificate.save()
            return redirect('certificate_list')  # Redirect to certificate list or any other page
    else:
        form = CertificateUploadForm()
    return render(request, 'resume_app/upload_certificate.html', {'form': form})


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


def generate_resume(request):
    # Get all certificates related to the user
    certificates = Certificate.objects.filter(user=request.user)

    # Redirect if no certificates exist
    if not certificates:
        return redirect('upload_certificate')

        # Initialize a list to hold extracted data for the resume
    extracted_data = []

    for certificate in certificates:
        # Extract and clean text from certificate PDF
        text = extract_text_from_pdf(certificate.certificate_file.path)
        clean_description = clean_text(text)
        extracted_info = extract_information(clean_description)

        # Append data for each certificate
        extracted_data.append({
            'certificate': certificate,
            'des': clean_description,
            'institution': extracted_info.get('institution', 'Not Found'),
            'date': extracted_info.get('date', 'Not Found'),
            'email': extracted_info.get('email', 'Not Found'),
            'phone': extracted_info.get('phone', 'Not Found'),
            'skills': extracted_info.get('skills', []),
        })

    # Check if the user wants to download the resume as PDF
    if request.GET.get('download') == 'pdf':
        if request.method == 'POST':
            form = UserInformationForm(request.POST)
            if form.is_valid():
                user_data = form.cleaned_data
                name = user_data['name']
                phone = user_data['phone']
                email = user_data['email']
                linkedin = user_data.get('linkedin', '')
                gmail = user_data.get('gmail', '')

                # Create a PDF buffer in memory
                buffer = BytesIO()
                p = canvas.Canvas(buffer, pagesize=letter)
                width, height = letter
                y_position = height - 100  # Starting position from top

                # Set up the font for the PDF
                font = "Helvetica"
                font_size = 12
                p.setFont(font, font_size)

                # Add personal information to the PDF
                p.setFont("Helvetica-Bold", 16)
                p.drawString(100, y_position, f"{name}")  # Name in larger font
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

                y_position -= 40  # Add some space before certificates section

                # Add certificate details
                for idx, data in enumerate(extracted_data, 1):
                    certificate_name = os.path.basename(data['certificate'].certificate_file.name)
                    p.setFont("Helvetica-Bold", 14)
                    p.drawString(100, y_position, f"Certificate {idx}:")
                    y_position -= 20

                    # Wrap description text and print it
                    description_lines = wrap_text(data['des'], p, font, font_size, width - 200)
                    p.setFont(font, font_size)  # Reset font size for description
                    for line in description_lines:
                        p.drawString(100, y_position, f"{line}")
                        y_position -= 14

                    y_position -= 20  # Add space after each certificate

                    # Create a new page if content exceeds bounds
                    if y_position < 100:
                        p.showPage()  # Create a new page
                        p.setFont(font, font_size)
                        y_position = height - 100  # Reset position for new page

                # Finalize the PDF
                p.showPage()  # End the document
                p.save()

                # Create the response to download the PDF
                buffer.seek(0)
                response = HttpResponse(buffer, content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="generated_resume.pdf"'
                return response
        else:
            form = UserInformationForm()  # Initialize the form if GET request

        context = {
            'form': form,
            'extracted_data': extracted_data
        }
        return render(request, 'resume_app/generate_resume_form.html', context)

    # If not downloading PDF, render the resume page
    context = {'extracted_data': extracted_data}
    return render(request, 'resume_app/generated_resume.html', context)


def extract_text_from_certificate(certificate):
    # Open the certificate file and extract text using OCR
    if certificate.certificate_file.name.endswith('.pdf'):
        with pdfplumber.open(certificate.certificate_file) as pdf:
            text = ''
            for page in pdf.pages:
                text += page.extract_text()
            return text
    else:
        # Use OCR for image files
        text = pytesseract.image_to_string(certificate.certificate_file.path)
        return text


def extract_course_name(doc):
    # You can improve this to specifically extract the course name
    for ent in doc.ents:
        if ent.label_ == 'ORG':  # Course might be treated as a proper noun or organization
            return ent.text
    return "Not Found"


def extract_institution_name(doc):
    # You can improve this to specifically extract the institution name
    for ent in doc.ents:
        if ent.label_ == 'ORG':  # Likely the institution is identified as an organization
            return ent.text
    return "Not Found"


def extract_date(doc):
    # Extract date (if any)
    for ent in doc.ents:
        if ent.label_ == 'DATE':
            return ent.text
    return "Not Found"


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # After successful signup, redirect to login page
    else:
        form = UserCreationForm()
    return render(request, 'resume_app/signup.html', {'form': form})


@login_required
def profile(request):
    return redirect('upload_certificate')  # Redirect to your desired page after login


def about(request):
    return render(request, 'resume_app/about.html')


def contact(request):
    return render(request, 'resume_app/contact.html')


@login_required
def delete_certificate(request, cert_id):
    # Ensure the certificate exists and is owned by the current user
    certificate = get_object_or_404(Certificate, id=cert_id, user=request.user)

    # Handle the deletion only if the request method is POST
    if request.method == 'POST':
        certificate.delete()  # Delete the certificate
        return redirect('certificate_list')  # Redirect to the certificate list page after deletion

    # If the method is GET, render the confirmation page
    return render(request, 'resume_app/confirm_delete.html', {'certificate': certificate})


def logout_view(request):
    logout(request)
    return redirect("/")
