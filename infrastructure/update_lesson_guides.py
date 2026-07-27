"""Update dashboard course lessons to include configuration guidance before the demo."""
import psycopg2

c = psycopg2.connect(
    host='finalat-db.ci3qcku0a9m0.us-east-1.rds.amazonaws.com',
    port=5432, dbname='finalat', user='finalat_admin',
    password='Finalat2024Prd', sslmode='require'
)
cur = c.cursor()

# Guide content to prepend before each demo marker
guides = {
    'dash-gastos-ingresos': '''
<div class="lesson-guide">
<h3>Antes de empezar: Configura tus categorías</h3>
<p>Para registrar gastos e ingresos necesitas tener categorías configuradas. Sigue estos pasos:</p>
<ol>
<li>Ve a <strong>Configuración</strong> (ícono de engrane en el menú lateral)</li>
<li>En la pestaña <strong>Paneles</strong>, asegúrate de que "Gastos / Ingresos" esté activado</li>
<li>Haz clic en el chevron (>) junto a "Gastos / Ingresos" para ver las <strong>Categorías</strong></li>
<li>Agrega las categorías que uses: Comida, Transporte, Entretenimiento, Salario, Freelance, etc.</li>
</ol>
<p>Una vez configuradas tus categorías, puedes registrar gastos e ingresos desde la sección correspondiente. Cada registro necesita:</p>
<ul>
<li><strong>Tipo:</strong> Ingreso o Gasto</li>
<li><strong>Fecha:</strong> Cuándo ocurrió</li>
<li><strong>Descripción:</strong> Qué fue (ej: "Uber Eats", "Nómina quincenal")</li>
<li><strong>Categoría:</strong> A cuál pertenece</li>
<li><strong>Monto:</strong> Cuánto fue</li>
</ul>
<p>Prueba registrar un gasto y un ingreso en la demo de abajo:</p>
</div>
''',
    'dash-creditos': '''
<div class="lesson-guide">
<h3>Antes de empezar: Registra tus tarjetas</h3>
<p>Para dar seguimiento a tus créditos, primero necesitas registrar tus tarjetas:</p>
<ol>
<li>Ve a <strong>Configuración → Créditos</strong></li>
<li>Haz clic en <strong>"+ Agregar"</strong></li>
<li>Ingresa el nombre del banco (ej: Nu, BBVA, Rappi) y selecciona un color</li>
<li>Repite para cada tarjeta que tengas</li>
</ol>
<p>Una vez registradas, en la sección de Créditos puedes actualizar para cada tarjeta:</p>
<ul>
<li><strong>Saldo a deber:</strong> Lo que debes actualmente</li>
<li><strong>Crédito total:</strong> Tu límite de crédito</li>
<li><strong>Pago mínimo:</strong> El mínimo que pide el banco</li>
<li><strong>Pago para no generar intereses:</strong> El total para no pagar intereses</li>
<li><strong>Fecha de corte y fecha de pago:</strong> Para el countdown de pago</li>
</ul>
<p>El sistema calcula automáticamente tu uso total, disponible, y te avisa cuando se acerca tu fecha de pago. Pruébalo:</p>
</div>
''',
    'dash-inversiones': '''
<div class="lesson-guide">
<h3>Antes de empezar: Configura tus cuentas de ahorro</h3>
<p>Para dar seguimiento a tus inversiones, primero registra dónde tienes tu dinero:</p>
<ol>
<li>Ve a <strong>Configuración → Cuentas de Ahorro</strong></li>
<li>Haz clic en <strong>"+ Agregar"</strong></li>
<li>Ingresa el nombre (ej: Nu México, Mercado Pago, CETES)</li>
<li>Configura la <strong>tasa anual (%)</strong> que te ofrece esa cuenta</li>
<li>Si tiene tope (ej: Nu Turbo solo da 13% hasta $25,000), ingresa el <strong>tope</strong> y la <strong>tasa sobre excedente</strong></li>
<li>Selecciona un color para identificarla</li>
</ol>
<p>En la sección de Inversiones podrás:</p>
<ul>
<li>Ver tu <strong>saldo actual</strong> en cada cuenta</li>
<li>Ver cuánto ganas <strong>al día</strong> en total</li>
<li>Seleccionar un periodo (1M, 3M, 6M, 1A, 5A) para ver la <strong>proyección</strong> de crecimiento</li>
<li>Actualizar los saldos cada lunes (el sistema te recuerda)</li>
</ul>
<p>Para el <strong>Afore</strong>, el sistema automáticamente crea una aportación semanal que puedes editar en Configuración → Aportaciones.</p>
<p>Prueba editar saldos y cambiar periodos en la demo:</p>
</div>
''',
    'dash-aportaciones': '''
<div class="lesson-guide">
<h3>Antes de empezar: Configura tus aportaciones</h3>
<p>Las aportaciones son compromisos periódicos que te pones para ahorrar/invertir. Para configurarlas:</p>
<ol>
<li>Ve a <strong>Configuración → Aportaciones</strong></li>
<li>Ya tienes una por defecto: <strong>Afore</strong> (semanal). Edita el monto que quieras aportar cada semana.</li>
<li>Agrega más aportaciones con <strong>"+ Agregar"</strong>: ej. "GBM" quincenal $1,000</li>
<li>Para cada una puedes elegir: nombre, persona (si es familiar), frecuencia (semanal/quincenal/mensual), monto y color</li>
</ol>
<p>En la sección de Aportaciones verás un calendario con cada periodo. Cuando hagas tu aportación:</p>
<ul>
<li>Haz clic en el <strong>lápiz (✏️)</strong> del periodo correspondiente</li>
<li>Cambia el estado a <strong>"Realizada"</strong></li>
<li>El sistema lleva tu racha y te ayuda a mantener el hábito</li>
</ul>
<p>La aportación de Afore está conectada con la sección de inversiones (campo "Aportación Voluntaria"). Prueba marcar semanas como realizadas:</p>
</div>
''',
}

for lesson_id, guide_html in guides.items():
    cur.execute("SELECT content FROM lessons WHERE id = %s", (lesson_id,))
    row = cur.fetchone()
    if not row:
        print(f"  {lesson_id}: NOT FOUND")
        continue
    
    content = row[0]
    
    # Remove old guide if exists
    if '<div class="lesson-guide">' in content:
        # Remove everything between lesson-guide divs
        import re
        content = re.sub(r'<div class="lesson-guide">.*?</div>\s*', '', content, flags=re.DOTALL)
    
    # Insert guide before the demo marker
    demo_marker = f'<div class="demo-section">'
    if demo_marker in content:
        content = content.replace(demo_marker, guide_html + demo_marker)
    else:
        # Append at end
        content = content + guide_html
    
    cur.execute("UPDATE lessons SET content = %s WHERE id = %s", (content, lesson_id))
    print(f"  {lesson_id}: guide added")

c.commit()
print("Done!")
c.close()
