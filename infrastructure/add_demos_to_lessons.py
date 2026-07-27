"""Add [[DEMO:xxx]] markers to the Dashboard course lessons."""
import psycopg2

c = psycopg2.connect(
    host='finalat-db.ci3qcku0a9m0.us-east-1.rds.amazonaws.com',
    port=5432, dbname='finalat', user='finalat_admin',
    password='Finalat2024Prd', sslmode='require'
)
cur = c.cursor()

# Map lesson IDs to their demo markers
demos = {
    'dash-gastos-ingresos': '[[DEMO:gastos-ingresos]]',
    'dash-creditos': '[[DEMO:creditos]]',
    'dash-inversiones': '[[DEMO:inversiones]]',
    'dash-aportaciones': '[[DEMO:aportaciones]]',
}

for lesson_id, marker in demos.items():
    # Check if marker already exists
    cur.execute("SELECT content FROM lessons WHERE id = %s", (lesson_id,))
    row = cur.fetchone()
    if row and marker not in row[0]:
        # Append marker at the end of content
        new_content = row[0] + f'\n\n<div class="demo-section">{marker}</div>'
        cur.execute("UPDATE lessons SET content = %s WHERE id = %s", (new_content, lesson_id))
        print(f"  {lesson_id}: added {marker}")
    else:
        print(f"  {lesson_id}: already has marker or not found")

c.commit()
print("Done!")
c.close()
