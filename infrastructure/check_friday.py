from datetime import datetime, timezone, timedelta, date
MX = timezone(timedelta(hours=-6))
mx_now = datetime.now(MX)
mx_today = mx_now.date()
days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
print(f"UTC now: {datetime.now(timezone.utc)}")
print(f"Mexico now: {mx_now}")
print(f"Mexico today: {mx_today} ({days[mx_today.weekday()]})")
print(f"Is Friday: {mx_today.weekday() == 4}")
