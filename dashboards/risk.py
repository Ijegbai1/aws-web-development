from sensors.models import PressureFrame

def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))

def compute_predicted_risk(patient, current_frame, lookback=10):
    """
    Simple explainable baseline predictor.
    Returns score from 0.0 to 1.0 based on recent trend.
    """

    recent_frames = list(
        PressureFrame.objects
        .filter(patient=patient, timestamp__lte=current_frame.timestamp)
        .order_by("-timestamp")[:lookback]
    )

    if len(recent_frames) < 2:
        return 0.0

    recent_frames.reverse()

    peaks = [f.peak_pressure_index or 0 for f in recent_frames]
    areas = [f.contact_area_pct or 0 for f in recent_frames]
    alerts = [1 if f.high_pressure_detected else 0 for f in recent_frames]

    peak_now = peaks[-1]
    peak_prev = peaks[0]
    area_now = areas[-1]
    area_prev = areas[0]

    peak_rise = max(0.0, peak_now - peak_prev)
    area_rise = max(0.0, area_now - area_prev)
    recent_alert_ratio = sum(alerts) / len(alerts)

    # normalize roughly into 0–1 ranges
    peak_component = clamp(peak_rise / 500.0)
    area_component = clamp(area_rise / 20.0)
    alert_component = clamp(recent_alert_ratio)

    score = (
        0.5 * peak_component +
        0.2 * area_component +
        0.3 * alert_component
    )

    return round(clamp(score), 3)