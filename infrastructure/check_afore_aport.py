import psycopg2
c = psycopg2.connect(host='finalat-db.ci3qcku0a9m0.us-east-1.rds.amazonaws.com', port=5432, dbname='finalat', user='finalat_admin', password='Finalat2024Prd', sslmode='require')
cur = c.cursor()

# Check all users and if they have Afore aportacion
cur.execute("SELECT user_id, email FROM users")
users = cur.fetchall()
print(f"Total users: {len(users)}")

for uid, email in users:
    cur.execute("SELECT id, target_name FROM aportaciones WHERE user_id = %s AND LOWER(target_name) = 'afore'", (uid,))
    afore = cur.fetchone()
    print(f"  {email}: Afore aportacion = {'YES (' + afore[0][:8] + '...)' if afore else 'MISSING'}")

c.close()
