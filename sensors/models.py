from django.db import models
from django.conf import settings

class PressureFrame(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="frames")
    timestamp = models.DateTimeField(db_index=True)
    predicted_risk_score = models.FloatField(default=0.0)
    # store raw 32x32 as JSON list-of-lists (easy + works well for 5 users dataset)
    frame = models.JSONField()

    # metrics
    peak_pressure_index = models.IntegerField(null=True, blank=True)
    contact_area_pct = models.FloatField(null=True, blank=True)

    # alert flags
    high_pressure_detected = models.BooleanField(default=False)
    flagged_for_review = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["patient", "timestamp"])]
        ordering = ["timestamp"]

class AlertEvent(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alerts")
    start_ts = models.DateTimeField(db_index=True)
    end_ts = models.DateTimeField(db_index=True)
    max_pressure = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

class PatientComment(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    frame = models.ForeignKey(PressureFrame, on_delete=models.CASCADE, related_name="comments")
    timestamp = models.DateTimeField(db_index=True)  # typically equals frame.timestamp
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class ClinicianReply(models.Model):
    clinician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="replies")
    comment = models.ForeignKey(PatientComment, on_delete=models.CASCADE, related_name="replies")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)



