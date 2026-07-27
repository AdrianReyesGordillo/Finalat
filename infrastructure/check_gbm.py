import psycopg2
c = psycopg2.connect(host='finalat-db.ci3qcku0a9m0.us-east-1.rds.amazonaws.com', port=5432, dbname='finalat', user='finalat_admin', password='Finalat2024Prd', sslmode='require')
cur = c.cursor()
print("=== GBM positions ===")
cur.execute("SELECT id, ticker, shares FROM gbm_portfolio WHERE user_id = 'TMti8ciOrQbO2n3soWErc1dILTo1'")
for r in cur.fetchall():
    print(f"  {r[0][:8]}... | {r[1]} | {r[2]}")
print("\n=== GBM metadata ===")
cur.execute("SELECT record_id, meta_key, meta_value FROM account_metadata WHERE user_id = 'TMti8ciOrQbO2n3soWErc1dILTo1' AND table_name = 'gbm'")
rows = cur.fetchall()
print(f"  Total: {len(rows)}")
for r in rows:
    print(f"  {r[0][:8]}... | {r[1]} = {r[2]}")
c.close()
