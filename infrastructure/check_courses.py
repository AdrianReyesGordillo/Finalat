import psycopg2
c = psycopg2.connect(host='finalat-db.ci3qcku0a9m0.us-east-1.rds.amazonaws.com', port=5432, dbname='finalat', user='finalat_admin', password='Finalat2024Prd', sslmode='require')
cur = c.cursor()
cur.execute("SELECT id, title FROM courses ORDER BY sort_order")
for r in cur.fetchall():
    print(f"\nCourse: {r[1]} (id={r[0]})")
    cur2 = c.cursor()
    cur2.execute("SELECT id, title, sort_order FROM lessons WHERE course_id = %s ORDER BY sort_order", (r[0],))
    for l in cur2.fetchall():
        print(f"  {l[2]}. {l[1]} (id={l[0]})")
c.close()
