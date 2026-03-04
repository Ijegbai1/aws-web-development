from django.urls import path
from . import views

urlpatterns = [

    # ----------- DASHBOARD PAGES -----------
    path("", views.home, name="home"),
    path("patient/", views.patient_dashboard, name="patient_dashboard"),
    path("clinician/", views.clinician_dashboard, name="clinician_dashboard"),

    # ----------- PATIENT APIs -----------
    path("api/patient/comments/", views.patient_comments_api),
    path("api/patient/latest-frame/", views.patient_latest_frame_api),
    path("api/patient/metrics/", views.patient_metrics_api),
    path("api/patient/comment/", views.patient_add_comment),
    path("api/patient/alerts/", views.patient_alerts_api),

    # ----------- CLINICIAN APIs -----------
    path("api/clinician/<int:patient_id>/timeline/", views.clinician_patient_timeline_api),
    path("api/clinician/<int:patient_id>/comments/", views.clinician_comments_api),
    path("api/clinician/reply/", views.clinician_reply),
    path("api/clinician/<int:patient_id>/alerts/", views.clinician_patient_alerts_api),
    path("api/clinician/flag-frame/", views.clinician_flag_frame),
]