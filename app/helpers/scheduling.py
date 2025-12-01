from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any, Optional

def parse_hhmm(s: str) -> time:
    return datetime.strptime(s, "%H:%M").time()

def format_hhmm(t: time) -> str:
    return t.strftime("%H:%M")

def daterange_times(start_t: time, end_t: time, step_minutes: int) -> List[str]:
    base = datetime.combine(date.today(), start_t)
    end = datetime.combine(date.today(), end_t)
    result: List[str] = []
    while base < end:
        result.append(format_hhmm(base.time()))
        base += timedelta(minutes=step_minutes)
    return result

def get_weekly_hours(barber: Dict[str, Any], target_date: date) -> Optional[Dict[str, str]]:
    weekly = barber.get("workingHours", {}).get("weekly", [])
    d = target_date.isoweekday()  # Monday=1 ... Sunday=7
    for w in weekly:
        if w.get("day") == d:
            return w
    return None

def is_slot_booked(barber_id: int, dt_str: str, db: Dict[str, Any]) -> bool:
    for bk in db["bookings"]:
        if bk["barberId"] == barber_id and bk["start"] == dt_str:
            return True
    return False