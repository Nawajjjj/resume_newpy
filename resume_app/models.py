# resume_app/models.py
from django.db import models


class Certificate(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    certificate_file = models.FileField(upload_to='certificates/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Certificate {self.id} by {self.user.username}"
