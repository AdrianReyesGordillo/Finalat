import psycopg2
from cryptography.fernet import Fernet

FERNET_KEY = "M8AJqz5YbM_UWYG-q9Hp8_qS4T8STBPBdgHJq2XazOc="
f = Fernet(FERNET_KEY.encode())

c = psycopg2.connect(
    host="finalat-db.ci3qcku0a9m0.us-east-1.rds.amazonaws.com",
    port=5432, dbname="finalat", user="finalat_admin",
    password="Finalat2024Prd", sslmode="require"
)
cur = c.cursor()

print("=== gastos_ingresos sample (decrypted) ===")
cur.execute("SELECT id, type, amount_encrypted, description_encrypted, category_id, entry_date FROM gastos_ingresos LIMIT 5")
for row in cur.fetchall():
    try:
        amount = f.decrypt(row[2].encode()).decode()
        desc = f.decrypt(row[3].encode()).decode()
        print(f"  {row[1]} | ${amount} | {desc} | date={row[5]}")
    except Exception as e:
        print(f"  DECRYPT ERROR: {e}")

print("\n=== ahorro sample (decrypted) ===")
cur.execute("SELECT account_name, amount_encrypted FROM ahorro LIMIT 5")
for row in cur.fetchall():
    try:
        amount = f.decrypt(row[1].encode()).decode()
        print(f"  {row[0]} | ${amount}")
    except Exception as e:
        print(f"  DECRYPT ERROR: {e}")

c.close()
