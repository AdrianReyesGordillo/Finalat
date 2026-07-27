import psycopg2
c = psycopg2.connect(host='finalat-db.ci3qcku0a9m0.us-east-1.rds.amazonaws.com', port=5432, dbname='finalat', user='finalat_admin', password='Finalat2024Prd', sslmode='require')
cur = c.cursor()
cur.execute("SELECT * FROM account_metadata WHERE table_name = 'creditos' ORDER BY record_id, meta_key")
rows = cur.fetchall()
print(f"Total rows: {len(rows)}")
for r in rows:
    print(r)
c.close()
