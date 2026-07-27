"""
Migrate data from local SQLite to RDS PostgreSQL.
Run this ON THE EC2 instance.
"""

import sqlite3
import psycopg2

SQLITE_PATH = "/tmp/finalat.db"

PG_HOST = "finalat-db.ci3qcku0a9m0.us-east-1.rds.amazonaws.com"
PG_PORT = 5432
PG_DB = "finalat"
PG_USER = "finalat_admin"
PG_PASS = "Finalat2024Prd"

TABLES = [
    "users",
    "categories",
    "courses",
    "lessons",
    "instruments",
    "ahorro",
    "creditos",
    "deudas",
    "afore",
    "gbm_portfolio",
    "aportaciones",
    "gastos_ingresos",
    "conversation_sessions",
    "update_tracker",
    "lesson_progress",
]


def get_sqlite_data(table):
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    columns = rows[0].keys() if rows else []
    conn.close()
    return columns, [dict(row) for row in rows]


def insert_pg_data(pg_conn, table, columns, rows):
    if not rows:
        print(f"  {table}: 0 rows (empty)")
        return
    cursor = pg_conn.cursor()
    cursor.execute(f"DELETE FROM {table}")
    cols_str = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))
    insert_sql = f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders})"
    count = 0
    for row in rows:
        values = [row[col] for col in columns]
        try:
            cursor.execute(insert_sql, values)
            count += 1
        except Exception as e:
            print(f"  ERROR in {table}: {e}")
            print(f"  Row: {row}")
            pg_conn.rollback()
            cursor = pg_conn.cursor()
            cursor.execute("SET session_replication_role = 'replica';")
            pg_conn.commit()
            continue
    pg_conn.commit()
    print(f"  {table}: {count} rows migrated")


def main():
    print("Connecting to PostgreSQL RDS...")
    pg_conn = psycopg2.connect(
        host=PG_HOST, port=PG_PORT, dbname=PG_DB,
        user=PG_USER, password=PG_PASS, sslmode="require",
    )
    print(f"Reading from SQLite: {SQLITE_PATH}")
    print("=" * 50)

    cursor = pg_conn.cursor()
    cursor.execute("SET session_replication_role = 'replica';")
    pg_conn.commit()

    for table in TABLES:
        columns, rows = get_sqlite_data(table)
        insert_pg_data(pg_conn, table, columns, rows)

    cursor = pg_conn.cursor()
    cursor.execute("SET session_replication_role = 'origin';")
    pg_conn.commit()
    pg_conn.close()
    print("=" * 50)
    print("Migration complete!")


if __name__ == "__main__":
    main()
