import psycopg2
c = psycopg2.connect(host='finalat-db.ci3qcku0a9m0.us-east-1.rds.amazonaws.com', port=5432, dbname='finalat', user='finalat_admin', password='Finalat2024Prd', sslmode='require')
cur = c.cursor()
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'instruments' ORDER BY ordinal_position")
print([r[0] for r in cur.fetchall()])
c.close()
