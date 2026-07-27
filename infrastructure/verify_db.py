import psycopg2

c = psycopg2.connect(
    host="finalat-db.ci3qcku0a9m0.us-east-1.rds.amazonaws.com",
    port=5432, dbname="finalat", user="finalat_admin",
    password="Finalat2024Prd", sslmode="require"
)
cur = c.cursor()
tables = [
    "users", "categories", "courses", "lessons", "instruments",
    "gastos_ingresos", "ahorro", "creditos", "deudas", "afore",
    "gbm_portfolio", "aportaciones", "lesson_progress"
]
for t in tables:
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    print(f"{t}: {cur.fetchone()[0]}")
c.close()
