import psycopg2
c = psycopg2.connect(host='finalat-db.ci3qcku0a9m0.us-east-1.rds.amazonaws.com', port=5432, dbname='finalat', user='finalat_admin', password='Finalat2024Prd', sslmode='require')
cur = c.cursor()

# USA tickers from the uploaded files
usa_tickers = ['AAPL', 'IBIT', 'KOF', 'LABU', 'MCD', 'QQQ', 'SOXL', 'V', 'VOO']

uid = 'TMti8ciOrQbO2n3soWErc1dILTo1'
cur.execute("SELECT id, ticker FROM gbm_portfolio WHERE user_id = %s", (uid,))
for row in cur.fetchall():
    record_id = row[0]
    ticker = row[1]
    market = 'usa' if ticker in usa_tickers else 'nacional'
    cur.execute(
        """INSERT INTO account_metadata (user_id, table_name, record_id, meta_key, meta_value)
           VALUES (%s, 'gbm', %s, 'market', %s)
           ON CONFLICT (user_id, table_name, record_id, meta_key) DO UPDATE SET meta_value = %s""",
        (uid, record_id, market, market)
    )
    print(f"  {ticker} -> {market}")

c.commit()
print("Done!")
c.close()
