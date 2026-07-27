import psycopg2
c = psycopg2.connect(host='finalat-db.ci3qcku0a9m0.us-east-1.rds.amazonaws.com', port=5432, dbname='finalat', user='finalat_admin', password='Finalat2024Prd', sslmode='require')
cur = c.cursor()
cur.execute("SELECT user_id, email FROM users")
for r in cur.fetchall():
    print(f"  {r[0]} | {r[1]}")
c.close()
