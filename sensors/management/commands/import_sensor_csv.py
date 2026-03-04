import csv
import re
from pathlib import Path
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User, Role
from sensors.models import PressureFrame


def infer_date_from_filename(path: Path):
    """
    Extract YYYYMMDD from filenames like:
    1c0fd777_20251011.csv
    """
    m = re.search(r"_(\d{8})\.csv$", path.name)
    if not m:
        return None
    yyyymmdd = m.group(1)
    return datetime.strptime(yyyymmdd, "%Y%m%d").date()


class Command(BaseCommand):
    help = "Import Sensore 32x32 frames from CSV (no timestamp column supported)."

    def add_arguments(self, parser):
        parser.add_argument("--patient_username", required=True)
        parser.add_argument("--file", required=True)

        # optional controls
        parser.add_argument(
            "--fps",
            type=float,
            default=1.0,
            help="Frames per second. Default=1.0 (1 frame per second)."
        )
        parser.add_argument(
            "--start_time",
            default=None,
            help='Optional start datetime like "2025-10-11 09:00:00" (local timezone). If not given, uses midnight from filename date.'
        )

    def handle(self, *args, **opts):
        patient = User.objects.get(username=opts["patient_username"], role=Role.PATIENT)
        file_path = Path(opts["file"])

        fps = float(opts["fps"])
        if fps <= 0:
            raise ValueError("--fps must be > 0")
        frame_delta = timedelta(seconds=1.0 / fps)

        # Determine start timestamp
        if opts["start_time"]:
            # parse "YYYY-MM-DD HH:MM:SS"
            start_naive = datetime.strptime(opts["start_time"], "%Y-%m-%d %H:%M:%S")
            start_ts = timezone.make_aware(start_naive, timezone.get_current_timezone())
        else:
            file_date = infer_date_from_filename(file_path)
            if not file_date:
                raise ValueError(
                    "Could not infer date from filename. "
                    "Rename like user_YYYYMMDD.csv or provide --start_time."
                )
            start_ts = timezone.make_aware(
                datetime.combine(file_date, datetime.min.time()),
                timezone.get_current_timezone()
            )

        # Read rows (each row should have 32 integers)
        rows = []
        with file_path.open("r", newline="", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            for r in reader:
                if not r:
                    continue
                # some CSVs may have extra whitespace
                r = [x.strip() for x in r if x.strip() != ""]
                # Expect exactly 32 values per row (no timestamp)
                if len(r) != 32:
                    raise ValueError(
                        f"Expected 32 columns per row, got {len(r)}. "
                        f"First bad row sample: {r[:5]}"
                    )
                rows.append([int(x) for x in r])

        if len(rows) % 32 != 0:
            raise ValueError(
                f"Row count {len(rows)} is not divisible by 32. "
                "CSV must contain 32 rows per frame."
            )

        total_frames = len(rows) // 32
        created = 0

        for frame_idx in range(total_frames):
            block = rows[frame_idx * 32: (frame_idx + 1) * 32]  # 32 rows
            ts = start_ts + (frame_delta * frame_idx)

            PressureFrame.objects.create(
                patient=patient,
                timestamp=ts,
                frame=block,
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Imported {created} frames for {patient.username} "
            f"starting {start_ts.isoformat()} at {fps} fps."
        ))
