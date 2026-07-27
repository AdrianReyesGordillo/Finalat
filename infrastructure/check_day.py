from datetime import date
d = date.today()
days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
print(f"Today: {d} ({days[d.weekday()]}), weekday index: {d.weekday()}")
print(f"Is Friday: {d.weekday() == 4}")
