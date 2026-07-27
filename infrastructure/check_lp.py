import psycopg2

c = psycopg2.connect(
    host="finalat-db.ci3qcku0a9m0.us-east-1.rds.amazonaws.com",
    port=5432, dbname="finalat", user="finalat_admin",
    password="Finalat2024Prd", sslmode="require"
)
cur = c.cursor()

print("=== lesson_progress user_ids ===")
cur.execute("SELECT DISTINCT user_id FROM lesson_progress")
for row in cur.fetchall():
    print(f"  {row[0]}")

print("\n=== all distinct user_ids across tables ===")
tables = ["gastos_ingresos", "ahorro", "lesson_progress", "categories"]
uids = set()
for t in tables:
    cur.execute(f"SELECT DISTINCT user_id FROM {t}")
    for r in cur.fetchall():
        uids.add(r[0])
for u in uids:
    print(f"  {u}")

c.close()
