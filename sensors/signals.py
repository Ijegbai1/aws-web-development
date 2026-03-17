from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import PressureFrame
from .services import peak_pressure_index, contact_area_pct, high_pressure
from dashboards.risk import compute_predicted_risk

@receiver(pre_save, sender=PressureFrame)
def compute_metrics(sender, instance: PressureFrame, **kwargs):

    if not instance.frame:
        return

    instance.contact_area_pct = contact_area_pct(instance.frame, lower_threshold=20)

    instance.peak_pressure_index = peak_pressure_index(
        instance.frame,
        min_region_pixels=10,
        lower_threshold=20
    )

    hp = high_pressure(
        instance.frame,
        high_threshold=120,
        hotspot_pixels=5
    )

    instance.high_pressure_detected = hp
    instance.flagged_for_review = hp

    if instance.patient:
        instance.predicted_risk_score = compute_predicted_risk(instance.patient, instance)