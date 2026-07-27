import psycopg2
c = psycopg2.connect(host='finalat-db.ci3qcku0a9m0.us-east-1.rds.amazonaws.com', port=5432, dbname='finalat', user='finalat_admin', password='Finalat2024Prd', sslmode='require')
cur = c.cursor()

# Put "domina-tu-dashboard" first (sort_order = 0), rest after
cur.execute("UPDATE courses SET sort_order = 0 WHERE id = 'domina-tu-dashboard'")
cur.execute("UPDATE courses SET sort_order = 1 WHERE id = 'finanzas-personales'")
cur.execute("UPDATE courses SET sort_order = 2 WHERE id = 'renta-fija-variable'")
cur.execute("UPDATE courses SET sort_order = 3 WHERE id = 'fundamentos-trading'")
c.commit()

# Verify
cur.execute("SELECT id, title, sort_order FROM courses ORDER BY sort_order")
for r in cur.fetchall():
    print(f"  {r[2]}. {r[1]}")
c.close()
