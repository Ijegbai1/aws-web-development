from django.shortcuts import render
from datetime import timedelta
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from accounts.models import Role, ClinicianPatient, User
from sensors.models import PressureFrame, AlertEvent, PatientComment
from .decorators import role_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from accounts.models import Role
from sensors.models import PressureFrame, AlertEvent, PatientComment, ClinicianReply

def home(request):
    if not request.user.is_authenticated:
        return redirect("login")

    if request.user.role == Role.PATIENT:
        return redirect("patient_dashboard")
    if request.user.role == Role.CLINICIAN:
        return redirect("clinician_dashboard")
    return redirect("/admin/")

@role_required(Role.PATIENT)
def patient_dashboard(request):
    return render(request, "dashboards/patient_dashboard.html")

@role_required(Role.PATIENT)
def patient_latest_frame_api(request):
    frame = (PressureFrame.objects
             .filter(patient=request.user)
             .order_by("-timestamp")
             .first())
    if not frame:
        return JsonResponse({"ok": False, "error": "No data"})
    return JsonResponse({
        "ok": True,
        "frame_id": frame.id,
        "timestamp": frame.timestamp.isoformat(),
        "frame": frame.frame,
        "peak_pressure_index": frame.peak_pressure_index,
        "contact_area_pct": frame.contact_area_pct,
        "high_pressure_detected": frame.high_pressure_detected,
    })

@role_required(Role.PATIENT)
def patient_metrics_api(request):
    hours = int(request.GET.get("hours", "1"))
    qs_all = PressureFrame.objects.filter(patient=request.user)
    latest_ts = qs_all.order_by("-timestamp").values_list("timestamp", flat=True).first()
    if not latest_ts:
        return JsonResponse({"ok": True, "points": []})
    end = latest_ts
    start = end - timedelta(hours=hours)
    qs = (
        qs_all
        .filter(timestamp__gte=start, timestamp__lte=end)
        .order_by("timestamp")
        .values("timestamp", "peak_pressure_index", "contact_area_pct", "high_pressure_detected")
    )
    return JsonResponse({"ok": True, "points": list(qs)})

from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
@role_required(Role.PATIENT)
def patient_add_comment(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST only"})
    frame_id = request.POST.get("frame_id")
    text = (request.POST.get("text") or "").strip()
    if not text:
        return JsonResponse({"ok": False, "error": "Empty comment"})
    frame = get_object_or_404(PressureFrame, id=frame_id, patient=request.user)
    PatientComment.objects.create(patient=request.user, frame=frame, timestamp=frame.timestamp, text=text)
    return JsonResponse({"ok": True})
# Create your views here.
from sensors.models import PatientComment, ClinicianReply

@role_required(Role.PATIENT)
def patient_comments_api(request):
    qs = (
        PatientComment.objects
        .filter(frame__patient=request.user)
        .select_related("frame")
        .order_by("-frame__timestamp")[:200]
    )
    data = []
    for c in qs:
        data.append({
            "id": c.id,
            "timestamp": c.frame.timestamp.isoformat(),
            "text": c.text,
            "frame_id": c.frame_id,
            "replies": [
                {"text": r.text, "created_at": r.created_at.isoformat()}
                for r in c.replies.all().order_by("created_at")
            ]
        })

    return JsonResponse({"ok": True, "comments": data})

@role_required(Role.PATIENT)
def patient_alerts_api(request):
    hours = int(request.GET.get("hours", "24"))

    qs_all = PressureFrame.objects.filter(patient=request.user)
    latest_ts = qs_all.order_by("-timestamp").values_list("timestamp", flat=True).first()
    if not latest_ts:
        return JsonResponse({"ok": True, "alerts": []})

    end = latest_ts
    start = end - timedelta(hours=hours)

    qs = (
        qs_all.filter(timestamp__gte=start, timestamp__lte=end, high_pressure_detected=True)
        .order_by("-timestamp")
        .values("id", "timestamp", "peak_pressure_index", "contact_area_pct", "flagged_for_review")
    )
    return JsonResponse({"ok": True, "alerts": list(qs)})

@role_required(Role.CLINICIAN)
def clinician_dashboard(request):
    patient_ids = ClinicianPatient.objects.filter(clinician=request.user).values_list("patient_id", flat=True)
    patients = User.objects.filter(id__in=patient_ids).order_by("username")
    return render(request, "dashboards/clinician_dashboard.html", {"patients": patients})

from datetime import timedelta
from django.shortcuts import get_object_or_404

@role_required(Role.CLINICIAN)
def clinician_patient_timeline_api(request, patient_id):

    # only allow assigned patients
    if not ClinicianPatient.objects.filter(
        clinician=request.user,
        patient_id=patient_id
    ).exists():
        return JsonResponse({"ok": False, "error": "Not assigned"})

    hours = int(request.GET.get("hours", 24))

    # Get all frames for patient
    qs_all = PressureFrame.objects.filter(patient_id=patient_id)

    # Get latest timestamp in dataset
    latest_ts = qs_all.order_by("-timestamp").values_list("timestamp", flat=True).first()

    if not latest_ts:
        return JsonResponse({"ok": True, "points": []})

    # Use latest timestamp as end (NOT timezone.now())
    end = latest_ts
    start = end - timedelta(hours=hours)

    frames = (
        qs_all
        .filter(timestamp__gte=start, timestamp__lte=end)
        .order_by("timestamp")
    )

    points = [{
        "timestamp": f.timestamp.isoformat(),
        "peak_pressure_index": f.peak_pressure_index,
        "contact_area_pct": f.contact_area_pct,
        "high_pressure_detected": f.high_pressure_detected,
        "flagged_for_review": f.flagged_for_review,
    } for f in frames]

    return JsonResponse({"ok": True, "points": points})

from django.views.decorators.csrf import csrf_exempt
@csrf_exempt

@role_required(Role.CLINICIAN)
def clinician_comments_api(request, patient_id):

    # only allow assigned patients
    if not ClinicianPatient.objects.filter(
        clinician=request.user,
        patient_id=patient_id
    ).exists():
        return JsonResponse({"ok": False, "error": "Not assigned"})

    comments = (
        PatientComment.objects
        .filter(frame__patient_id=patient_id)
        .select_related("frame")
        .order_by("-frame__timestamp")
    )

    out = []
    for c in comments:
        out.append({
            "id": c.id,
            "timestamp": c.frame.timestamp.isoformat(),
            "text": c.text,
            "frame_id": c.frame_id,
            "replies": [
                {
                    "text": r.text,
                    "created_at": r.created_at.isoformat()
                }
                for r in c.replies.all().order_by("created_at")
            ],
        })

    return JsonResponse({"ok": True, "comments": out})

@csrf_exempt
@role_required(Role.CLINICIAN)
def clinician_reply(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST only"})
    comment_id = request.POST.get("comment_id")
    text = (request.POST.get("text") or "").strip()
    if not text:
        return JsonResponse({"ok": False, "error": "Empty reply"})
    comment = get_object_or_404(PatientComment, id=comment_id)
    # must be assigned
    if not ClinicianPatient.objects.filter(clinician=request.user, patient=comment.patient).exists():
        return JsonResponse({"ok": False, "error": "Not assigned"})
    ClinicianReply.objects.create(clinician=request.user, comment=comment, text=text)
    return JsonResponse({"ok": True})

@role_required(Role.CLINICIAN)
def clinician_patient_alerts_api(request, patient_id):
    if not ClinicianPatient.objects.filter(clinician=request.user, patient_id=patient_id).exists():
        return JsonResponse({"ok": False, "error": "Not assigned"})

    hours = int(request.GET.get("hours", "24"))

    qs_all = PressureFrame.objects.filter(patient_id=patient_id)
    latest_ts = qs_all.order_by("-timestamp").values_list("timestamp", flat=True).first()
    if not latest_ts:
        return JsonResponse({"ok": True, "alerts": []})

    end = latest_ts
    start = end - timedelta(hours=hours)

    qs = (
        qs_all.filter(timestamp__gte=start, timestamp__lte=end, high_pressure_detected=True)
        .order_by("-timestamp")
        .values("id", "timestamp", "peak_pressure_index", "contact_area_pct", "flagged_for_review")
    )
    return JsonResponse({"ok": True, "alerts": list(qs)})

@csrf_exempt
@role_required(Role.CLINICIAN)
def clinician_flag_frame(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST only"})

    frame_id = request.POST.get("frame_id")
    flag = request.POST.get("flag")  # "1" or "0"

    if frame_id is None or flag is None:
        return JsonResponse({"ok": False, "error": "frame_id and flag required"})

    frame = get_object_or_404(PressureFrame, id=frame_id)

    # must be assigned to this patient
    if not ClinicianPatient.objects.filter(clinician=request.user, patient=frame.patient).exists():
        return JsonResponse({"ok": False, "error": "Not assigned"})

    frame.flagged_for_review = (flag == "1")
    frame.save(update_fields=["flagged_for_review"])

    return JsonResponse({"ok": True, "flagged_for_review": frame.flagged_for_review})