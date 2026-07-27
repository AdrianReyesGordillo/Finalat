"""
Migrate data from local SQLite (codigos/finalat/finalat.db) to RDS PostgreSQL.
Reads all rows from each table and inserts them into the production database.
"""

import sqlite3
import psycopg2
import sys

# Source: SQLite
SQLITE_PATH = r"C:\Codigofacilito\finalat\finalat.db"

# Target: RDS PostgreSQL
PG_HOST = "finalat-db.ci3qcku0a9m0.us-east-1.rds.amazonaws.com"
PG_PORT = 5432
PG_DB = "finalat"
PG_USER = "finalat_admin"
PG_PASS = "Finalat2024Prd"

# Tables to migrate in dependency order (parents first)
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


def get_sqlite_data(sqlite_path, table):
    """Read all rows from a SQLite table."""
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    if rows:
        columns = rows[0].keys()
    else:
        columns = []
    conn.close()
    return columns, [dict(row) for row in rows]


def insert_pg_data(pg_conn, table, columns, rows):
    """Insert rows into PostgreSQL table."""
    if not rows:
        print(f"  {table}: 0 rows (empty)")
        return

    cursor = pg_conn.cursor()

    # Clear existing data
    cursor.execute(f"DELETE FROM {table}")

    # Build INSERT statement
    cols_str = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))
    insert_sql = f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders})"

    # Insert each row
    count = 0
    for row in rows:
        values = [row[col] for col in columns]
        try:
            cursor.execute(insert_sql, values)
            count += 1
        except Exception as e:
            print(f"  ERROR inserting into {table}: {e}")
            print(f"  Row: {row}")
            pg_conn.rollback()
            raise

    pg_conn.commit()
    print(f"  {table}: {count} rows migrated")


def main():
    print("Connecting to PostgreSQL RDS...")
    pg_conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASS,
        sslmode="require",
    )

    print(f"Reading from SQLite: {SQLITE_PATH}")
    print("=" * 50)

    # Disable FK checks during migration
    cursor = pg_conn.cursor()
    cursor.execute("SET session_replication_role = 'replica';")
    pg_conn.commit()

    for table in TABLES:
        columns, rows = get_sqlite_data(SQLITE_PATH, table)
        insert_pg_data(pg_conn, table, columns, rows)

    # Re-enable FK checks
    cursor.execute("SET session_replication_role = 'origin';")
    pg_conn.commit()

    pg_conn.close()
    print("=" * 50)
    print("Migration complete!")


if __name__ == "__main__":
    main()
