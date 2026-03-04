from django.shortcuts import render
from datetime import timedelta
from django.shortcuts import render
from django.utils import timezone
from accounts.models import Role, ClinicianPatient
from sensors.models import PressureFrame
from dashboards.decorators import role_required

def _summary(patient, start, end):
    qs = PressureFrame.objects.filter(patient=patient, timestamp__gte=start, timestamp__lt=end)
    count = qs.count()
    alerts = qs.filter(high_pressure_detected=True).count()
    avg_area = qs.aggregate(a=models.Avg("contact_area_pct"))["a"] if count else 0
    avg_peak = qs.aggregate(a=models.Avg("peak_pressure_index"))["a"] if count else 0
    return {"count": count, "alerts": alerts, "avg_area": avg_area or 0, "avg_peak": avg_peak or 0}

@role_required(Role.PATIENT, Role.CLINICIAN)
def daily_report(request):
    # patient sees self; clinician sees selected patient via ?patient_id=
    patient = request.user
    if request.user.role == Role.CLINICIAN:
        pid = request.GET.get("patient_id")
        if not pid or not ClinicianPatient.objects.filter(clinician=request.user, patient_id=pid).exists():
            return render(request, "reports/report.html", {"error": "Select an assigned patient."})
        from accounts.models import User
        patient = User.objects.get(id=pid)

    today = timezone.now().date()
    start_today = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
    start_yday = start_today - timedelta(days=1)

    today_sum = _summary(patient, start_today, start_today + timedelta(days=1))
    yday_sum = _summary(patient, start_yday, start_today)

    return render(request, "reports/report.html", {
        "patient": patient,
        "today_sum": today_sum,
        "yday_sum": yday_sum,
    })
# Create your views here.
