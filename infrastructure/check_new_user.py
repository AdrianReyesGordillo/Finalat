import psycopg2
from cryptography.fernet import Fernet

FERNET_KEY = "M8AJqz5YbM_UWYG-q9Hp8_qS4T8STBPBdgHJq2XazOc="
f = Fernet(FERNET_KEY.encode())

c = psycopg2.connect(host='finalat-db.ci3qcku0a9m0.us-east-1.rds.amazonaws.com', port=5432, dbname='finalat', user='finalat_admin', password='Finalat2024Prd', sslmode='require')
cur = c.cursor()

# Find the new user's UID
cur.execute("SELECT user_id, email FROM users WHERE email != 'adriax45@gmail.com'")
users = cur.fetchall()
print(f"Non-admin users: {len(users)}")
for uid, email in users:
    print(f"\n  User: {email} (uid={uid[:12]}...)")
    
    # Check aportaciones
    cur.execute("SELECT id, target_name, amount_encrypted, frequency FROM aportaciones WHERE user_id = %s", (uid,))
    aports = cur.fetchall()
    print(f"  Aportaciones: {len(aports)}")
    for a in aports:
        try:
            amount = f.decrypt(a[2].encode()).decode()
        except:
            amount = "DECRYPT_FAIL"
        print(f"    {a[1]} | amount={amount} | freq={a[3]}")

c.close()
