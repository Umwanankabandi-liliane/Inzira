"""Background schedulers — deadline alerts + recurring opportunity harvest."""

from __future__ import annotations

import os
import threading
import time
from typing import Callable, Optional


_alert_started = False
_harvest_started = False


def start_alert_scheduler(entity_extractor=None) -> None:
    global _alert_started
    if _alert_started or os.getenv("INZIRA_DISABLE_ALERT_SCHEDULER", "").strip() == "1":
        return
    _alert_started = True

    def _loop() -> None:
        time.sleep(45)
        interval_min = max(5, int(os.getenv("ALERT_SCAN_INTERVAL_MINUTES", "30")))
        while True:
            try:
                from alert_service import run_background_alert_scan
                run_background_alert_scan(entity_extractor=entity_extractor)
            except Exception as e:
                print(f"Alert scheduler error: {e}")
            time.sleep(interval_min * 60)

    thread = threading.Thread(target=_loop, name="inzira-alert-scheduler", daemon=True)
    thread.start()
    print(f"Alert scheduler started (every {os.getenv('ALERT_SCAN_INTERVAL_MINUTES', '30')} min)")


def start_harvest_scheduler(
    *,
    is_stale_fn: Callable[[int], bool],
    is_running_fn: Callable[[], bool],
    run_harvest_fn: Callable[[str], None],
    stale_hours: Optional[int] = None,
) -> None:
    """
    Re-check every N hours while the server is awake; run harvest when data is stale.
    On Hugging Face this fires whenever the Space stays up (not a true OS cron).
    """
    global _harvest_started
    if _harvest_started or os.getenv("INZIRA_DISABLE_HARVEST_SCHEDULER", "").strip() == "1":
        return
    _harvest_started = True
    hours = stale_hours or max(6, int(os.getenv("INZIRA_HARVEST_STALE_HOURS", "24")))
    check_every_h = max(1, int(os.getenv("INZIRA_HARVEST_CHECK_INTERVAL_HOURS", "6")))

    def _loop() -> None:
        # Startup handler may already have kicked off a harvest
        time.sleep(180)
        while True:
            try:
                if is_stale_fn(hours) and not is_running_fn():
                    print(f"Harvest scheduler: data older than {hours}h — starting refresh")
                    run_harvest_fn("scheduled_loop")
            except Exception as exc:
                print(f"Harvest scheduler error: {exc}")
            time.sleep(check_every_h * 3600)

    thread = threading.Thread(target=_loop, name="inzira-harvest-scheduler", daemon=True)
    thread.start()
    print(f"Harvest scheduler started (check every {check_every_h}h, refresh if older than {hours}h)")
