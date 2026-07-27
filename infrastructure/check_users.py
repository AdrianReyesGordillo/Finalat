import psycopg2

c = psycopg2.connect(
    host="finalat-db.ci3qcku0a9m0.us-east-1.rds.amazonaws.com",
    port=5432, dbname="finalat", user="finalat_admin",
    password="Finalat2024Prd", sslmode="require"
)
cur = c.cursor()

print("=== USERS ===")
cur.execute("SELECT user_id, email FROM users")
for row in cur.fetchall():
    print(f"  user_id={row[0]}  email={row[1]}")

print("\n=== DATA COUNTS PER user_id ===")
for tbl in ["gastos_ingresos", "ahorro", "creditos", "deudas", "afore", "gbm_portfolio", "aportaciones", "categories"]:
    cur.execute(f"SELECT user_id, COUNT(*) FROM {tbl} GROUP BY user_id")
    rows = cur.fetchall()
    print(f"  {tbl}:")
    for r in rows:
        print(f"     {r[0]} -> {r[1]} rows")

c.close()
