from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class Role(models.TextChoices):
    ADMIN = "ADMIN", _("Admin")
    CLINICIAN = "CLINICIAN", _("Clinician")
    PATIENT = "PATIENT", _("Patient")

class User(AbstractUser):
    role = models.CharField(max_length=20, choices=Role.choices)

    def is_admin(self): return self.role == Role.ADMIN
    def is_clinician(self): return self.role == Role.CLINICIAN
    def is_patient(self): return self.role == Role.PATIENT

class ClinicianPatient(models.Model):
    clinician = models.ForeignKey(
        "User", on_delete=models.CASCADE, related_name="assigned_patients",
        limit_choices_to={"role": Role.CLINICIAN},
    )
    patient = models.ForeignKey(
        "User", on_delete=models.CASCADE, related_name="assigned_clinicians",
        limit_choices_to={"role": Role.PATIENT},
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("clinician", "patient")


# Create your models here.
