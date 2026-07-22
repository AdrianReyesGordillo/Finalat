"""Seed script to populate courses and lessons in the database.

Run with: python -m backend.seed_courses
This replaces the hardcoded frontend Vue components with database-backed content.
"""

import asyncio

from sqlalchemy import select

from backend.models.courses import Course, Lesson
from backend.models.database import async_session


# ---------------------------------------------------------------------------
# Course definitions (mirrors frontend/src/data/courses.ts)
# ---------------------------------------------------------------------------

COURSES_DATA = [
    {
        "id": "finanzas-personales",
        "title": "Introducción a las Finanzas Personales",
        "description": "Aprende los conceptos esenciales para manejar tu dinero: presupuestos, ahorro, deuda y cómo construir una base financiera sólida.",
        "sort_order": 1,
        "lessons": [
            {"id": "introduccion", "title": "Introducción", "sort_order": 1},
            {"id": "conceptos", "title": "Conceptos generales", "sort_order": 2},
            {"id": "fondo-emergencia", "title": "Fondo de emergencia", "sort_order": 3},
            {"id": "diversificacion", "title": "Diversificación", "sort_order": 4},
            {"id": "tarjeta-credito", "title": "¿Cómo funciona una TDC?", "sort_order": 5},
        ],
    },
    {
        "id": "renta-fija-variable",
        "title": "Renta Fija y Renta Variable",
        "description": "Entiende las diferencias entre instrumentos de renta fija y variable, desde CETES hasta acciones en la bolsa.",
        "sort_order": 2,
        "lessons": [
            {"id": "renta-fija", "title": "Renta fija", "sort_order": 1},
            {"id": "renta-variable", "title": "Renta variable", "sort_order": 2},
            {"id": "cetes", "title": "CETES", "sort_order": 3},
            {"id": "cuentas-ahorro", "title": "Cuentas de ahorro", "sort_order": 4},
            {"id": "acciones", "title": "Acciones", "sort_order": 5},
        ],
    },
    {
        "id": "fundamentos-trading",
        "title": "Fundamentos de Trading",
        "description": "Conoce los principios del trading: análisis técnico, patrones, indicadores y gestión de riesgo para operar en los mercados.",
        "sort_order": 3,
        "lessons": [
            {"id": "trading", "title": "Introducción al Trading", "sort_order": 1},
            {"id": "tendencias", "title": "Tendencias", "sort_order": 2},
            {"id": "velas", "title": "Velas japonesas", "sort_order": 3},
            {"id": "patrones", "title": "Patrones", "sort_order": 4},
            {"id": "indicadores", "title": "Indicadores", "sort_order": 5},
            {"id": "gestion-riesgo", "title": "Gestión de riesgo", "sort_order": 6},
        ],
    },
    {
        "id": "domina-tu-dashboard",
        "title": "Domina tu Dashboard Financiero",
        "description": "Aprende a usar cada sección del dashboard: patrimonio neto, gastos, créditos, inversiones, deudas y aportaciones. Entiende qué significa cada dato y cómo llenarlos correctamente.",
        "sort_order": 4,
        "lessons": [
            {"id": "dash-intro", "title": "¿Qué es el Dashboard?", "sort_order": 1},
            {"id": "dash-patrimonio", "title": "Patrimonio neto y tasa de ahorro", "sort_order": 2},
            {"id": "dash-gastos-ingresos", "title": "Gastos e Ingresos", "sort_order": 3},
            {"id": "dash-creditos", "title": "Tarjetas de crédito", "sort_order": 4},
            {"id": "dash-deudas", "title": "Deudas y préstamos", "sort_order": 5},
            {"id": "dash-inversiones", "title": "Inversiones y ahorro", "sort_order": 6},
            {"id": "dash-aportaciones", "title": "Aportaciones periódicas", "sort_order": 7},
        ],
    },
]


# ---------------------------------------------------------------------------
# Lesson content (extracted from Vue template files)
# Stored as HTML ready to render with v-html on the frontend.
# ---------------------------------------------------------------------------

LESSON_CONTENT = {}

LESSON_CONTENT["introduccion"] = """<h1>Finanzas paso a paso</h1>

<section>
<h2>Introducción</h2>
<p>En México, muchas personas terminan la preparatoria, la universidad o incluso comienzan a trabajar sin haber recibido una sola clase sobre cómo administrar su dinero. Sabemos resolver ecuaciones, conocemos fechas históricas y aprendemos muchas otras materias importantes, pero casi nunca nos enseñan cómo funciona una tarjeta de crédito, qué es la inflación, cómo hacer un presupuesto o cómo invertir.</p>
<p>Esto provoca que muchas personas aprendan sobre dinero mediante errores: endeudándose, pagando intereses innecesarios o viviendo constantemente preocupadas por llegar al final de mes.</p>
<p>La buena noticia es que aprender finanzas personales no es tan complicado como parece. No necesitas ser contador, economista o matemático. Lo único que necesitas es entender algunos conceptos básicos y comenzar a tomar mejores decisiones con tu dinero.</p>
<p>El objetivo de esta guía es explicarte esos conceptos de la forma más sencilla posible.</p>
</section>

<section>
<h2>El primer paso: conocer tu situación financiera</h2>
<p>Antes de pensar en ahorrar, invertir o generar más dinero, primero necesitas entender cómo se encuentra tu situación actual.</p>
<p>Muchas personas quieren invertir inmediatamente porque escucharon que alguien gana dinero con acciones, criptomonedas o CETES. Sin embargo, intentar invertir sin conocer tus finanzas es como intentar construir una casa sin revisar primero los cimientos.</p>
<p>Por eso, el primer paso siempre es organizar tu información financiera.</p>
<p>Debes saber exactamente cuánto dinero entra a tu vida y cuánto dinero sale de ella. En otras palabras, necesitas conocer tus ingresos y tus gastos.</p>
<p>Los ingresos son todo el dinero que recibes. Puede ser tu salario, comisiones, propinas, trabajos extra, ventas de productos, becas o cualquier otra fuente de dinero. No importa de dónde venga, si aumenta la cantidad de dinero que tienes disponible, se considera un ingreso.</p>
<p>Por otro lado, los gastos o egresos son todo el dinero que sale de tu bolsillo. Aquí entran gastos como la renta, la comida, el transporte, el internet, los servicios de streaming, las salidas con amigos, las compras en línea y cualquier otro pago que realices.</p>
<p>La mayoría de las personas cree que conoce bien sus gastos, pero cuando empieza a registrarlos descubre que una gran cantidad de dinero se va en pequeños pagos que parecían insignificantes. Un café diario, una suscripción olvidada o pedir comida varias veces por semana pueden parecer gastos pequeños por separado, pero al sumarlos durante todo un mes pueden representar una cantidad considerable.</p>
<p>Por esta razón es recomendable registrar cada gasto durante al menos uno o dos meses. No importa si utilizas una libreta, una hoja de cálculo o una aplicación. Lo importante es que tengas un registro real de lo que ocurre con tu dinero.</p>
</section>

<section>
<h2>Conoce tus deudas reales</h2>
<p>Otro aspecto fundamental es identificar correctamente tus deudas.</p>
<p>Uno de los errores más comunes es pensar que la deuda corresponde únicamente al pago mensual de una tarjeta de crédito. En realidad, lo importante es conocer la deuda total.</p>
<p>Por ejemplo, si una tarjeta te pide un pago mensual de $1,000 pesos, muchas personas piensan que solamente deben esos $1,000. Sin embargo, es posible que la deuda total sea de $20,000 pesos y que esos $1,000 sean únicamente el pago mínimo.</p>
<p>Por eso es importante anotar cuánto debes realmente en cada tarjeta, préstamo o financiamiento.</p>
<p>También es importante identificar las compras realizadas a meses sin intereses. Aunque no generan intereses si se pagan correctamente, siguen siendo compromisos financieros que reducen el dinero disponible de los próximos meses.</p>
<p>Imagina que tienes tres compras diferentes a meses sin intereses. Tal vez cada una parece pequeña por separado, pero juntas pueden representar una cantidad importante de tu ingreso mensual. Conocer estos compromisos te permitirá saber cuánto dinero necesitas generar cada mes para cubrir tus obligaciones sin atrasarte.</p>
</section>

<section>
<h2>Identifica gastos innecesarios</h2>
<p>Una vez que conoces tus ingresos, gastos y deudas, llega el momento de analizar en qué estás utilizando tu dinero.</p>
<p>Aquí aparece un tema que suele generar incomodidad: los gastos innecesarios.</p>
<p>Es importante aclarar algo. Tener gastos de entretenimiento no es malo. Salir con amigos, comprar algo que te gusta o darte un gusto ocasional también forma parte de disfrutar la vida. El problema surge cuando esos gastos se realizan sin planificación y terminan afectando tu estabilidad financiera.</p>
<p>Muchas compras se realizan por impulso. Frases como "me lo merezco", "Dios proveerá", "solo será esta vez" o "ya veré cómo lo pago después" suelen ser señales de que estamos tomando decisiones emocionales y no financieras.</p>
<p>Por ejemplo, comprar un teléfono nuevo no es necesariamente una mala decisión. Pero si para hacerlo necesitas endeudarte cuando todavía estás pagando el teléfono anterior, probablemente no sea el mejor momento.</p>
<p>La clave no es eliminar todos los gustos personales, sino aprender a diferenciar entre un gasto que realmente puedes permitirte y uno que solamente estás justificando.</p>
</section>

<section>
<h2>Aprende a analizar tus números</h2>
<p>Cuando llevas varios meses registrando información, comienzas a tener algo muy valioso: datos.</p>
<p>Y los datos permiten tomar mejores decisiones.</p>
<p>Supongamos que en enero gastaste $6,000 pesos y en febrero gastaste $5,200. Esto significa que redujiste tus gastos en $800 pesos. Ahora puedes investigar qué cambió. Tal vez comiste más en casa, utilizaste menos transporte o cancelaste alguna suscripción que no utilizabas.</p>
<p>Ese análisis te ayuda a descubrir hábitos que benefician tus finanzas y hábitos que las perjudican.</p>
<p>Con el tiempo podrás responder preguntas importantes como:</p>
<ul>
<li>¿Cuál es mi gasto más grande?</li>
<li>¿Cuánto dinero destino al entretenimiento?</li>
<li>¿Cuánto gasto en comida fuera de casa?</li>
<li>¿Cuánto dinero puedo ahorrar cada mes?</li>
<li>¿Qué gastos puedo reducir sin afectar mi calidad de vida?</li>
</ul>
<p>Las finanzas personales dejan de ser una cuestión de adivinanzas y se convierten en una cuestión de números.</p>
</section>

<section>
<h2>¿Ahorrar es suficiente?</h2>
<p>Una vez que logras ahorrar dinero, muchas personas creen que el trabajo está terminado. Sin embargo, existe un fenómeno económico que afecta a todos los países y que hace que ahorrar por sí solo no sea suficiente.</p>
<p>Ese fenómeno se llama inflación.</p>
<p>La inflación significa que, con el paso del tiempo, los precios aumentan. Dicho de otra manera, el dinero pierde poder de compra.</p>
<p>Imagina que hoy tienes $100 pesos. Tal vez con ellos puedas comprar cierta cantidad de productos en el supermercado. Dentro de algunos años, esos mismos $100 pesos probablemente comprarán menos productos porque los precios habrán aumentado.</p>
<p>Esto significa que aunque la cantidad de dinero sea la misma, su valor real será menor. Por eso muchas personas dicen que dejar el dinero guardado durante muchos años equivale a perder dinero lentamente.</p>
</section>

<section>
<h2>La importancia de invertir</h2>
<p>Aquí es donde entra la inversión.</p>
<p>La palabra "invertir" suele generar miedo porque muchas personas la relacionan con apuestas, fraudes o pérdidas de dinero. Además, durante muchos años se ha transmitido la idea de que invertir es algo exclusivo para personas ricas.</p>
<p>La realidad es muy diferente.</p>
<p>Invertir significa utilizar tu dinero para que produzca más dinero.</p>
<p>Cuando tu dinero permanece inmóvil, la inflación trabaja en tu contra. Cuando inviertes, intentas que tu dinero crezca al menos al mismo ritmo que la inflación y, de ser posible, más rápido.</p>
</section>

<section>
<h2>Lo que sigue</h2>
<p>Ahora que entiendes cómo organizar tus finanzas, controlar tus gastos, identificar deudas, comprender la inflación y la importancia de invertir, el siguiente paso es conocer los tipos de inversión que existen.</p>
<p>En las siguientes secciones exploraremos la renta fija (inversiones con rendimiento predecible) y la renta variable (inversiones con mayor potencial pero también mayor riesgo). Cada una tiene su lugar en una estrategia financiera bien construida.</p>
<p>Recuerda que las finanzas personales no se tratan de hacerse rico rápidamente. Se tratan de tomar mejores decisiones de manera constante. Una pequeña mejora repetida durante años puede generar resultados extraordinarios en tu futuro financiero.</p>
</section>"""


LESSON_CONTENT["conceptos"] = """<h1>Conceptos financieros</h1>
<p class="subtitle">Próximamente: definiciones claras de los términos más importantes en finanzas personales e inversiones.</p>
<div class="placeholder">Contenido en desarrollo</div>"""

LESSON_CONTENT["fondo-emergencia"] = """<h1>Fondo de emergencia</h1>
<p class="subtitle">Próximamente: qué es, cuánto necesitas y dónde guardarlo.</p>
<div class="placeholder">Contenido en desarrollo</div>"""

LESSON_CONTENT["diversificacion"] = """<h1>Diversificación</h1>
<p class="subtitle">Próximamente: cómo repartir tu dinero para reducir riesgos.</p>
<div class="placeholder">Contenido en desarrollo</div>"""


LESSON_CONTENT["tarjeta-credito"] = """<h1>¿Cómo funciona una tarjeta de crédito?</h1>
<p class="subtitle">Entiende el mecanismo detrás de este instrumento financiero, sus costos y cómo usarla a tu favor.</p>

<section>
<h2>¿Qué es una tarjeta de crédito?</h2>
<p>Una tarjeta de crédito es un medio de pago que te permite realizar compras con dinero que el banco te presta. A diferencia de una tarjeta de débito (donde gastas tu propio saldo), con una de crédito estás usando una <strong>línea de crédito</strong> que debes pagar después.</p>
</section>

<section>
<h2>El ciclo de facturación</h2>
<p>Cada tarjeta tiene un ciclo mensual con dos fechas clave:</p>
<ul>
<li><strong>Fecha de corte:</strong> El día en que se cierra tu estado de cuenta y se calcula cuánto debes.</li>
<li><strong>Fecha límite de pago:</strong> El último día para pagar sin generar intereses (generalmente 20 días después del corte).</li>
</ul>
<div class="tip">💡 Si pagas el total antes de la fecha límite, no pagas intereses. Es como un préstamo gratis de hasta ~50 días.</div>
</section>

<section>
<h2>Tipos de pago</h2>
<div class="card-grid">
<div class="card"><h3>Pago total</h3><p>Pagas todo lo que debes. Sin intereses. Es la mejor opción siempre.</p></div>
<div class="card"><h3>Pago mínimo</h3><p>Evitas que te reporten en Buró, pero el resto genera intereses altos (30-60% anual).</p></div>
<div class="card"><h3>No pagar</h3><p>Se generan intereses moratorios, comisiones y un impacto negativo en tu historial crediticio.</p></div>
</div>
</section>

<section>
<h2>Costos: tasa de interés y CAT</h2>
<ul>
<li><strong>Tasa de interés anual:</strong> Lo que el banco cobra sobre el saldo no pagado. En México va del 25% al 70%+ dependiendo de la tarjeta.</li>
<li><strong>CAT (Costo Anual Total):</strong> Incluye intereses + comisiones + anualidad. Es el indicador real del costo de tu tarjeta.</li>
<li><strong>Anualidad:</strong> Cobro anual por tener la tarjeta. Muchas tarjetas la eliminan si alcanzas cierto nivel de gasto.</li>
</ul>
</section>

<section>
<h2>Ventajas y riesgos</h2>
<div class="card-grid">
<div class="card card-green"><h3>✅ Ventajas</h3><ul><li>Construyes historial crediticio</li><li>Financiamiento sin intereses (pagando total)</li><li>Protección en compras y seguros</li><li>Recompensas, cashback o puntos</li><li>Meses sin intereses en comercios</li></ul></div>
<div class="card card-red"><h3>⚠️ Riesgos</h3><ul><li>Intereses muy altos si no pagas el total</li><li>Fácil caer en deuda al gastar de más</li><li>Comisiones por disposición de efectivo</li><li>Pago mínimo crea una trampa de deuda</li><li>Puede afectar tu score de Buró</li></ul></div>
</div>
</section>

<section>
<h2>Consejos para usarla bien</h2>
<ol>
<li><strong>Paga siempre el total</strong> antes de la fecha límite.</li>
<li><strong>No uses más del 30%</strong> de tu línea de crédito (mejora tu score).</li>
<li><strong>Nunca saques efectivo</strong> del cajero con tu TDC: comisión + intereses desde el día 1.</li>
<li><strong>Revisa tu estado de cuenta</strong> cada mes para detectar cargos no reconocidos.</li>
<li><strong>Compara el CAT</strong>, no solo la tasa, al elegir una tarjeta.</li>
</ol>
</section>

<section>
<h2>En resumen</h2>
<p>Una tarjeta de crédito es una herramienta poderosa si se usa con disciplina: te da financiamiento gratis, construye tu historial y ofrece beneficios. Pero si no pagas el total cada mes, los intereses pueden convertirla en una trampa costosa. La clave es tratarla como si fuera débito: no gastes lo que no tienes.</p>
</section>"""


LESSON_CONTENT["renta-fija"] = """<h1>Renta fija</h1>

<section>
<h2>¿Qué es la renta fija?</h2>
<p>La renta fija es uno de los tipos de inversión más accesibles y fáciles de entender, especialmente para quienes están dando sus primeros pasos en el mundo financiero.</p>
<p>En este tipo de inversión, una institución como un banco, una fintech o incluso el gobierno utiliza tu dinero durante cierto tiempo y a cambio te paga un rendimiento previamente establecido.</p>
<p>La principal ventaja es que normalmente sabes con bastante anticipación cuánto rendimiento vas a obtener. No hay sorpresas ni variaciones inesperadas.</p>
<p>Por ejemplo, si una inversión ofrece un rendimiento anual del 10%, puedes calcular aproximadamente cuánto ganarás al finalizar el año. Esto convierte a la renta fija en una de las opciones favoritas para las personas que están comenzando a invertir.</p>
</section>

<section>
<h2>Ejemplos de renta fija en México</h2>
<p>Existen varios instrumentos de renta fija disponibles en México:</p>
<ul>
<li><strong>CETES:</strong> Certificados de la Tesorería emitidos por el gobierno federal. Son considerados de los más seguros.</li>
<li><strong>Cuentas de ahorro con rendimiento:</strong> Ofrecidas por fintechs como Nu, Mercado Pago, Stori, Ualá, entre otras.</li>
<li><strong>Pagarés bancarios:</strong> Inversiones a plazo fijo ofrecidas por bancos tradicionales.</li>
<li><strong>SOFIPOS:</strong> Sociedades Financieras Populares que ofrecen tasas competitivas con protección del PROSOFIPO.</li>
</ul>
<p>Cada uno tiene diferentes niveles de riesgo, liquidez y rendimiento. Lo importante es entender que todos comparten la característica principal: sabes de antemano cuánto vas a ganar.</p>
</section>

<section>
<h2>Interés simple e interés compuesto</h2>
<p>Cuando hablamos de inversiones de renta fija es fundamental entender la diferencia entre interés simple e interés compuesto.</p>
<p>El interés simple genera rendimientos únicamente sobre el dinero original que invertiste. Si inviertes $10,000 pesos al 15% anual, ganarás $1,500 pesos durante el año.</p>
<p>El interés compuesto funciona de manera diferente. En lugar de retirar las ganancias, estas se agregan al capital inicial y comienzan a generar nuevos rendimientos.</p>
<p>Siguiendo el mismo ejemplo, al finalizar el primer año tendrías $11,500 pesos. Durante el segundo año los intereses ya no se calcularían sobre $10,000, sino sobre $11,500. Esto provoca que el crecimiento se acelere con el tiempo.</p>
<p>Por esta razón el interés compuesto es considerado por muchos inversionistas como una de las herramientas más poderosas para construir patrimonio a largo plazo.</p>
</section>

<section>
<h2>Ventajas y desventajas</h2>
<div class="card-grid">
<div class="card card-green"><h3>Ventajas</h3><ul><li>Rendimiento predecible</li><li>Bajo riesgo</li><li>Ideal para principiantes</li><li>Protege contra la inflación</li></ul></div>
<div class="card card-red"><h3>Desventajas</h3><ul><li>Rendimientos limitados</li><li>Menor liquidez en plazos fijos</li><li>No supera significativamente la inflación</li><li>Penalizaciones por retiro anticipado</li></ul></div>
</div>
</section>

<section>
<h2>Conclusión</h2>
<p>La renta fija es el punto de partida ideal para cualquier persona que quiera hacer crecer su dinero con seguridad. No requiere conocimientos avanzados ni grandes cantidades de capital.</p>
<p>Una vez que domines estos instrumentos y tengas un fondo de emergencia sólido, estarás listo para explorar opciones con mayor potencial de crecimiento, como la renta variable.</p>
</section>"""


LESSON_CONTENT["renta-variable"] = """<h1>Renta variable</h1>

<section>
<h2>¿Qué es la renta variable?</h2>
<p>La renta variable es un tipo de inversión donde no sabes exactamente cuánto vas a ganar. A diferencia de la renta fija, donde normalmente existe una tasa o rendimiento estimado, en la renta variable el resultado puede cambiar constantemente.</p>
<p>Esto significa que tu inversión puede subir de valor, pero también puede bajar.</p>
<p>Por eso se llama "variable", porque su rendimiento no es fijo. Cambia dependiendo de muchos factores, como la situación económica, el desempeño de una empresa, las decisiones de los inversionistas, las noticias, la oferta y la demanda, e incluso eventos mundiales.</p>
</section>

<section>
<h2>Un ejemplo sencillo para entenderlo</h2>
<p>Imagina que compras una parte muy pequeña de una empresa. Esa empresa vende productos, tiene clientes, genera ganancias y puede crecer con el tiempo.</p>
<p>Si la empresa crece, vende más, gana más dinero y la gente confía en ella, es posible que esa pequeña parte que compraste aumente de valor.</p>
<p>Pero si la empresa tiene problemas, vende menos, pierde dinero o los inversionistas dejan de confiar en ella, esa pequeña parte puede bajar de valor.</p>
<p>Una acción representa una pequeña parte de una empresa. Si compras acciones de una empresa, te conviertes en dueño de una pequeñísima parte de ella.</p>
</section>

<section>
<h2>¿Por qué la renta variable puede dar más ganancias?</h2>
<p>La renta variable suele tener más riesgo que la renta fija, pero también puede dar mayores ganancias a largo plazo.</p>
<p>Esto pasa porque estás participando en el crecimiento de empresas, mercados o sectores completos.</p>
<p>Pero aquí es importante entender algo: nada está garantizado. Así como una empresa puede crecer, también puede fracasar. Por eso la renta variable no debe verse como una forma rápida y segura de ganar dinero.</p>
</section>

<section>
<h2>Ejemplos de renta variable</h2>
<ul>
<li><strong>Acciones:</strong> partes pequeñas de una empresa. Si la empresa aumenta su valor, tu acción puede subir de precio.</li>
<li><strong>ETFs:</strong> fondos que agrupan varias inversiones en un solo producto. Ayudan a diversificar sin elegir una sola empresa.</li>
<li><strong>Fondos de inversión:</strong> pueden invertir en diferentes activos, administrados por una institución o grupo de expertos.</li>
<li><strong>Criptomonedas:</strong> su precio cambia constantemente y son mucho más volátiles y riesgosas.</li>
</ul>
</section>

<section>
<h2>Volatilidad</h2>
<p>La volatilidad significa que el precio de una inversión puede subir y bajar con frecuencia.</p>
<p>El problema aparece cuando una persona invierte sin entender esto y se asusta cuando ve que su inversión baja. Entonces vende rápido por miedo y convierte una pérdida temporal en una pérdida real.</p>
</section>

<section>
<h2>Ventajas y desventajas</h2>
<div class="card-grid">
<div class="card card-green"><h3>Ventajas</h3><ul><li>Mayores rendimientos a largo plazo</li><li>Participas en el crecimiento de empresas</li><li>Puedes diversificar fácilmente</li><li>Accesible con cantidades pequeñas hoy en día</li></ul></div>
<div class="card card-red"><h3>Desventajas</h3><ul><li>No hay ganancia garantizada</li><li>Puede generar ansiedad por la volatilidad</li><li>Requiere paciencia y visión a largo plazo</li><li>No ideal para dinero que necesitas pronto</li></ul></div>
</div>
</section>

<section>
<h2>Conclusión</h2>
<p>La renta variable es un tipo de inversión donde el rendimiento no está garantizado. Tu dinero puede crecer, pero también puede bajar de valor.</p>
<p>Para una persona que apenas empieza, lo más importante no es correr a comprar acciones o criptomonedas. Lo más importante es aprender, ordenar sus finanzas, crear un fondo de emergencia y después invertir poco a poco, entendiendo siempre el riesgo.</p>
</section>"""


LESSON_CONTENT["cetes"] = """<h1>CETES</h1>
<p class="subtitle">Los Certificados de la Tesorería de la Federación son uno de los instrumentos de inversión más seguros y populares en México.</p>

<section>
<h2>¿Qué son los CETES?</h2>
<p>Los CETES (Certificados de la Tesorería de la Federación) son instrumentos de deuda a corto plazo emitidos por el Gobierno Federal de México. Cuando compras CETES, le estás prestando dinero al gobierno y este se compromete a devolvértelo al final del plazo, junto con un rendimiento previamente conocido.</p>
<p>Son considerados el activo de menor riesgo en México porque el gobierno mexicano respalda el pago.</p>
</section>

<section>
<h2>¿Cómo funcionan?</h2>
<p>Los CETES funcionan con un mecanismo llamado <strong>"a descuento"</strong>: los compras a un precio menor a su valor nominal y al vencimiento recibes el valor completo. La diferencia es tu rendimiento.</p>
<div class="tip">📊 Ejemplo: Compras un CETE a 28 días por $99.20 pesos. Al vencimiento recibes $100 pesos. Tu ganancia fueron $0.80, que anualizada equivale aproximadamente a una tasa del 10.5% anual.</div>
<ul>
<li><strong>Valor nominal:</strong> $10 pesos por título (es la unidad mínima).</li>
<li><strong>Plazos disponibles:</strong> 28, 91, 182 y 364 días.</li>
<li><strong>Subasta semanal:</strong> Banxico subasta CETES cada martes.</li>
<li><strong>Liquidación:</strong> Al vencimiento, el dinero regresa automáticamente a tu cuenta.</li>
</ul>
</section>

<section>
<h2>¿Cómo invertir en CETES?</h2>
<div class="card-grid">
<div class="card"><h3>CETES Directo</h3><p>Plataforma oficial del gobierno (cetesdirecto.com). Sin comisiones, sin intermediarios.</p><ul><li>Inversión mínima desde $100</li><li>Apertura 100% en línea</li><li>Reinversión automática</li></ul></div>
<div class="card"><h3>Casas de bolsa y bancos</h3><p>A través de tu broker (GBM, Kuspit, Actinver, etc.) o tu banco.</p><ul><li>Pueden cobrar comisión</li><li>Útil si ya operas ahí</li><li>Acceso a otros instrumentos</li></ul></div>
</div>
</section>

<section>
<h2>CETES vs. cuentas de ahorro</h2>
<table>
<thead><tr><th>Característica</th><th>CETES</th><th>Cuentas de ahorro</th></tr></thead>
<tbody>
<tr><td>Riesgo</td><td>Mínimo (gobierno federal)</td><td>Bajo (depende de la institución)</td></tr>
<tr><td>Liquidez</td><td>Hasta el vencimiento (28-364 días)</td><td>Inmediata 24/7</td></tr>
<tr><td>Tasa</td><td>Fija al momento de comprar</td><td>Variable (puede cambiar sin aviso)</td></tr>
<tr><td>Tope para tasa preferente</td><td>No tiene tope</td><td>Muchas tienen tope</td></tr>
<tr><td>Inversión mínima</td><td>$100</td><td>Generalmente $0</td></tr>
<tr><td>Protección</td><td>Respaldo del gobierno federal</td><td>IPAB (bancos) o PROSOFIPO (SOFIPOS)</td></tr>
</tbody>
</table>
</section>

<section>
<h2>Ventajas y desventajas</h2>
<div class="card-grid">
<div class="card card-green"><h3>Ventajas</h3><ul><li>Riesgo prácticamente nulo</li><li>Tasa fija conocida desde el día 1</li><li>Sin comisiones en CETES Directo</li><li>Sin tope para la tasa preferente</li><li>Reinversión automática disponible</li><li>Acceso desde $100</li></ul></div>
<div class="card card-red"><h3>Desventajas</h3><ul><li>Tu dinero queda comprometido hasta el vencimiento</li><li>Vender antes implica pérdidas o castigos</li><li>Rendimientos limitados frente a renta variable</li><li>A largo plazo puede no ganarle a la inflación real</li><li>Las tasas se mueven con la política de Banxico</li></ul></div>
</div>
</section>

<section>
<h2>Conclusión</h2>
<p>Los CETES son una excelente puerta de entrada al mundo de las inversiones: seguros, simples y con un rendimiento predecible. Funcionan muy bien para metas de mediano plazo o para quien quiere proteger un capital importante sin asumir riesgo.</p>
</section>"""


LESSON_CONTENT["cuentas-ahorro"] = """<h1>Cuentas de ahorro</h1>
<p class="subtitle">Las cuentas de ahorro con rendimiento son una forma sencilla y líquida de hacer crecer tu dinero.</p>

<section>
<h2>¿Qué son?</h2>
<p>Una cuenta de ahorro con rendimiento es un producto bancario o de fintech donde tu dinero genera intereses diariamente, sin tener que comprometerlo a un plazo fijo. Puedes retirarlo cuando quieras y, mientras tanto, sigue ganando rendimientos.</p>
<p>En México, fintechs como Nu, Mercado Pago, Stori, Ualá, Klar, Finsus y Didi han popularizado este tipo de cuentas con tasas competitivas.</p>
</section>

<section>
<h2>¿Cómo funcionan?</h2>
<ul>
<li><strong>Rendimiento diario:</strong> Los intereses se calculan cada día sobre tu saldo.</li>
<li><strong>Tasa anual (GAT):</strong> Se expresa como Ganancia Anual Total.</li>
<li><strong>Liquidez total:</strong> Puedes disponer de tu dinero en cualquier momento, sin penalizaciones.</li>
<li><strong>Sin monto mínimo:</strong> La mayoría no exige un saldo mínimo para empezar.</li>
</ul>
</section>

<section>
<h2>Tipos de cuentas</h2>
<div class="card-grid">
<div class="card"><h3>A la vista (líquidas)</h3><p>Tu dinero está disponible 24/7. Tasas más bajas pero máxima flexibilidad. Ideal para fondo de emergencia.</p></div>
<div class="card"><h3>A plazo (congeladas)</h3><p>Comprometes tu dinero por días o meses a cambio de una tasa más alta. Si retiras antes, pierdes intereses.</p></div>
</div>
</section>

<section>
<h2>Seguridad: IPAB y PROSOFIPO</h2>
<ul>
<li><strong>IPAB (bancos):</strong> Protege hasta 400,000 UDIs (~3.2 millones de pesos) por persona, por institución.</li>
<li><strong>PROSOFIPO (SOFIPOS):</strong> Protege hasta 25,000 UDIs (~200 mil pesos) por persona, por institución.</li>
<li><strong>Fintechs (IFPE):</strong> No tienen seguro de depósito directo. Suelen apoyarse en un banco aliado o en fideicomisos.</li>
</ul>
</section>

<section>
<h2>Ventajas y desventajas</h2>
<div class="card-grid">
<div class="card card-green"><h3>Ventajas</h3><ul><li>Liquidez total (a la vista)</li><li>Sin monto mínimo</li><li>Apertura 100% digital</li><li>Rendimiento diario</li><li>Tasas competitivas vs. bancos tradicionales</li></ul></div>
<div class="card card-red"><h3>Desventajas</h3><ul><li>Las tasas pueden cambiar sin aviso</li><li>Algunas tienen tope máximo para tasa preferente</li><li>Menos cobertura del seguro de depósito en SOFIPOS/fintechs</li><li>ISR retenido sobre los intereses</li></ul></div>
</div>
</section>

<section>
<h2>Conclusión</h2>
<p>Las cuentas de ahorro con rendimiento son perfectas para tu fondo de emergencia y para el dinero que necesitas tener disponible. Combinan seguridad, liquidez y un rendimiento que al menos te ayuda a no perder tanto frente a la inflación.</p>
</section>"""


LESSON_CONTENT["acciones"] = """<h1>Acciones</h1>
<p class="subtitle">Todo lo que necesitas entender antes de comprar tu primera acción: qué son, dónde comprarlas, cómo analizarlas y cómo controlar tus emociones al invertir.</p>

<section>
<h2>¿Qué es una acción?</h2>
<p>Una acción es una pequeña parte de una empresa. Cuando compras una acción, te conviertes en dueño de una fracción muy pequeña de esa compañía. Eso significa que participas en lo que le pase a la empresa. Si crece y vale más, tus acciones pueden subir de precio. Si tiene problemas, pueden bajar.</p>
</section>

<section>
<h2>¿Qué es un ETF?</h2>
<p>Un ETF (Exchange Traded Fund) es como una canasta que dentro tiene muchas acciones de diferentes empresas. Cuando compras un ETF, con una sola operación estás comprando un pedacito de todas las empresas que hay dentro de esa canasta.</p>
<p>Los ETFs se compran y se venden en la bolsa igual que una acción, y normalmente puedes empezar con cantidades pequeñas.</p>
</section>

<section>
<h2>¿Cómo funcionan las acciones?</h2>
<p>Las acciones se compran y se venden en la bolsa de valores. En México la principal es la BMV, y en Estados Unidos están la NYSE y el Nasdaq.</p>
<p>Existen dos formas principales de ganar dinero con acciones:</p>
<ul>
<li><strong>Plusvalía:</strong> compras una acción a cierto precio y, si sube, la vendes más cara.</li>
<li><strong>Dividendos:</strong> algunas empresas reparten parte de sus ganancias entre sus accionistas.</li>
</ul>
</section>

<section>
<h2>¿Dónde comprar acciones?</h2>
<p>Necesitas un intermediario autorizado llamado casa de bolsa o broker. En México algunas opciones son:</p>
<ul>
<li><strong>GBM+:</strong> una de las más populares, permite invertir desde cantidades pequeñas.</li>
<li><strong>Kuspit, Bursanet, Actinver:</strong> casas de bolsa con plataformas en línea.</li>
<li><strong>Nu y otras fintech:</strong> han empezado a ofrecer compra de acciones.</li>
<li><strong>Brokers internacionales:</strong> como Interactive Brokers.</li>
</ul>
</section>

<section>
<h2>Tu peor enemigo: las emociones</h2>
<p>En las acciones, muchas veces no pierde dinero quien no sabe, sino quien no controla sus emociones. Dos comportamientos arruinan a la mayoría de los principiantes: comprar por FOMO y vender por pánico.</p>
<div class="card-grid">
<div class="card card-orange"><h3>Comprar por FOMO</h3><p>FOMO viene del inglés "fear of missing out". Pasa cuando ves que una acción está subiendo mucho y sientes que te estás perdiendo la oportunidad. Entonces compras tarde, cuando ya está cara.</p></div>
<div class="card card-red"><h3>Vender por pánico</h3><p>Ocurre cuando ves que tu inversión baja, te asustas y vendes rápido para "no perder más". Si vendes asustado, conviertes una pérdida temporal en una pérdida real.</p></div>
</div>
</section>

<section>
<h2>Ventajas y desventajas</h2>
<div class="card-grid">
<div class="card card-green"><h3>Ventajas</h3><ul><li>Buen potencial de crecimiento a largo plazo</li><li>Puedes empezar con cantidades pequeñas</li><li>Algunas pagan dividendos</li><li>Te vuelves dueño de grandes empresas</li><li>Mucha información disponible para analizar</li></ul></div>
<div class="card card-red"><h3>Desventajas</h3><ul><li>El precio puede bajar y no hay ganancia garantizada</li><li>Requiere paciencia y disciplina emocional</li><li>Necesitas investigar antes de comprar</li><li>No es ideal para dinero que usarás pronto</li><li>Puede haber comisiones e impuestos</li></ul></div>
</div>
</section>

<section>
<h2>Conclusión</h2>
<p>Las acciones son una de las mejores formas de hacer crecer tu dinero a largo plazo, pero solo cuando inviertes con conocimiento, paciencia y la cabeza fría. No se trata de adivinar ni de seguir modas, sino de entender lo que compras y mantener la calma cuando el mercado se mueve.</p>
</section>"""


LESSON_CONTENT["trading"] = """<h1>Trading: introducción</h1>
<p class="subtitle">Qué es el trading, en qué se diferencia de invertir y cuáles son los instrumentos más usados.</p>

<section>
<h2>¿Qué es el trading?</h2>
<p>El trading consiste en comprar y vender instrumentos financieros en plazos relativamente cortos, buscando aprovechar los movimientos del precio para obtener una ganancia. Mientras que un inversionista de largo plazo compra y mantiene durante años, un trader puede comprar y vender en minutos, horas, días o semanas.</p>
<p>Dicho de forma simple: invertir es plantar un árbol y esperar a que crezca; el trading es intentar aprovechar las subidas y bajadas del precio en el camino.</p>
</section>

<section>
<h2>Trading vs. inversión a largo plazo</h2>
<table>
<thead><tr><th>Aspecto</th><th>Trading</th><th>Inversión a largo plazo</th></tr></thead>
<tbody>
<tr><td>Horizonte</td><td>Minutos a semanas</td><td>Años</td></tr>
<tr><td>Tiempo dedicado</td><td>Alto, seguimiento constante</td><td>Bajo</td></tr>
<tr><td>Riesgo</td><td>Alto</td><td>Moderado (con diversificación)</td></tr>
<tr><td>Análisis principal</td><td>Técnico (gráficas)</td><td>Fundamental (empresa)</td></tr>
</tbody>
</table>
</section>

<section>
<h2>Instrumentos más populares</h2>
<ul>
<li><strong>Acciones:</strong> partes de empresas que cotizan en bolsa.</li>
<li><strong>Divisas (Forex):</strong> compra y venta de monedas. Es el mercado más grande del mundo.</li>
<li><strong>Criptomonedas:</strong> como Bitcoin o Ethereum. Muy volátiles, operan las 24 horas.</li>
<li><strong>Índices:</strong> representan a un grupo de empresas, como el S&P 500.</li>
<li><strong>Materias primas:</strong> oro, petróleo, plata, etc.</li>
<li><strong>ETFs:</strong> canastas de activos que también pueden operarse en plazos cortos.</li>
</ul>
</section>

<section>
<h2>Tipos de trading según el plazo</h2>
<div class="card-grid">
<div class="card"><h3>Scalping</h3><p>Operaciones muy rápidas, de segundos o minutos.</p></div>
<div class="card"><h3>Day trading</h3><p>Abre y cierra operaciones dentro del mismo día.</p></div>
<div class="card"><h3>Swing trading</h3><p>Mantiene operaciones de varios días a semanas.</p></div>
<div class="card"><h3>Position trading</h3><p>El más largo dentro del trading: semanas o meses.</p></div>
</div>
</section>

<section>
<div class="warning">
<h3>Una advertencia importante</h3>
<p>El trading no es una forma fácil ni rápida de hacerse rico. La gran mayoría de las personas que empiezan a hacer trading pierden dinero, sobre todo al inicio, por falta de conocimiento y por dejarse llevar por las emociones.</p>
<p>Si te interesa, empieza aprendiendo con calma, practica con cuentas de prueba (demo) y nunca arriesgues dinero que no puedas permitirte perder.</p>
</div>
</section>"""

LESSON_CONTENT["tendencias"] = """<h1>Tendencias</h1>
<p class="subtitle">La dirección del precio es lo primero que un trader aprende a identificar.</p>

<section>
<h2>¿Qué es una tendencia?</h2>
<p>Una tendencia es la dirección general en la que se está moviendo el precio de un activo durante un periodo de tiempo. Aunque el precio sube y baja constantemente, si das un paso atrás puedes ver hacia dónde va en conjunto.</p>
<p>Existe una frase muy conocida en el trading: "la tendencia es tu amiga". Significa que suele ser más fácil operar a favor de la dirección del mercado que en su contra.</p>
</section>

<section>
<h2>Tipos de tendencia</h2>
<div class="card-grid">
<div class="card card-green"><h3>Alcista</h3><p>El precio hace máximos y mínimos cada vez más altos. La fuerza está en los compradores.</p></div>
<div class="card card-red"><h3>Bajista</h3><p>El precio hace máximos y mínimos cada vez más bajos. La fuerza está en los vendedores.</p></div>
<div class="card"><h3>Lateral</h3><p>El precio se mueve de lado, sin una dirección clara, entre un techo y un piso.</p></div>
</div>
</section>

<section>
<h2>Soportes y resistencias</h2>
<ul>
<li><strong>Soporte:</strong> un nivel de precio donde la caída tiende a detenerse porque aparecen compradores. Funciona como un "piso".</li>
<li><strong>Resistencia:</strong> un nivel donde la subida tiende a frenarse porque aparecen vendedores. Funciona como un "techo".</li>
</ul>
<p>Cuando el precio rompe un soporte o una resistencia importante, suele ser una señal de que la tendencia podría cambiar o acelerarse.</p>
</section>

<section>
<h2>Líneas de tendencia</h2>
<p>Una línea de tendencia es una línea que dibujas sobre la gráfica conectando los puntos donde el precio rebota. Te ayuda a visualizar la dirección y a detectar cuándo se está respetando o rompiendo.</p>
</section>"""


LESSON_CONTENT["velas"] = """<h1>Velas japonesas</h1>
<p class="subtitle">La forma más común de leer el precio en una gráfica de trading.</p>

<section>
<h2>¿Qué es una vela japonesa?</h2>
<p>Una vela japonesa es una figura que resume cómo se movió el precio durante un periodo de tiempo. Cada vela te dice cuatro cosas: a qué precio abrió, a qué precio cerró, el punto más alto y el punto más bajo en ese periodo.</p>
<p>Las velas son tan populares porque, de un solo vistazo, te muestran si en ese periodo ganaron los compradores o los vendedores.</p>
</section>

<section>
<h2>Partes de una vela</h2>
<ul>
<li><strong>Cuerpo:</strong> la parte ancha. Va del precio de apertura al de cierre.</li>
<li><strong>Mechas o sombras:</strong> las líneas finas arriba y abajo. Marcan el precio máximo y mínimo alcanzado.</li>
<li><strong>Color:</strong> normalmente verde (o blanco) si el precio subió, y rojo (o negro) si bajó.</li>
</ul>
<div class="card-grid">
<div class="card card-green"><h3>Vela alcista (verde)</h3><p>El precio cerró más arriba de donde abrió. Ganaron los compradores.</p></div>
<div class="card card-red"><h3>Vela bajista (roja)</h3><p>El precio cerró más abajo de donde abrió. Ganaron los vendedores.</p></div>
</div>
</section>

<section>
<h2>Velas individuales más conocidas</h2>
<ul>
<li><strong>Doji:</strong> abre y cierra casi en el mismo precio. Indica duda o indecisión en el mercado.</li>
<li><strong>Martillo:</strong> cuerpo pequeño arriba y mecha larga abajo. Suele aparecer al final de una caída y sugerir un posible rebote.</li>
<li><strong>Estrella fugaz:</strong> cuerpo pequeño abajo y mecha larga arriba. Puede anticipar una caída tras una subida.</li>
<li><strong>Marubozu:</strong> vela con cuerpo grande y casi sin mechas. Indica una fuerza clara de un lado.</li>
</ul>
</section>

<section>
<h2>Temporalidad de las velas</h2>
<p>Cada vela representa un periodo que tú eliges. En una gráfica de 1 minuto, cada vela es un minuto; en una de 1 día, cada vela es un día completo. Los traders de plazos cortos usan velas de minutos, mientras que quienes operan a más días suelen mirar velas diarias o semanales.</p>
</section>"""

LESSON_CONTENT["patrones"] = """<h1>Patrones</h1>
<p class="subtitle">Figuras que se repiten en las gráficas y que los traders usan para anticipar movimientos.</p>

<section>
<h2>¿Qué es un patrón?</h2>
<p>Un patrón es una figura que se forma en la gráfica del precio y que tiende a repetirse a lo largo del tiempo. Los traders los estudian porque, históricamente, ciertas figuras suelen ir seguidas de movimientos parecidos.</p>
<p>Es importante entender algo: los patrones no son una bola de cristal. No garantizan nada. Solo aumentan o disminuyen la probabilidad de que algo ocurra.</p>
</section>

<section>
<h2>Patrones de continuación</h2>
<p>Sugieren que la tendencia actual probablemente seguirá después de una pausa:</p>
<ul>
<li><strong>Banderas:</strong> una pausa corta en forma de pequeño canal después de un movimiento fuerte.</li>
<li><strong>Triángulos:</strong> el precio se va comprimiendo hasta que rompe hacia un lado.</li>
<li><strong>Rectángulos:</strong> el precio se mueve de lado entre un soporte y una resistencia antes de continuar.</li>
</ul>
</section>

<section>
<h2>Patrones de cambio (reversión)</h2>
<p>Sugieren que la tendencia actual podría estar por terminar:</p>
<ul>
<li><strong>Hombro-cabeza-hombro:</strong> tres picos, el del centro más alto. Suele anticipar un cambio de alcista a bajista.</li>
<li><strong>Doble techo:</strong> el precio sube dos veces a un nivel parecido y no logra romperlo. Señal de posible caída.</li>
<li><strong>Doble piso:</strong> el precio baja dos veces a un nivel parecido y rebota. Señal de posible subida.</li>
</ul>
</section>

<section>
<div class="tip">Consejo: ningún patrón funciona el 100% de las veces. Los traders con experiencia confirman los patrones con el volumen, la tendencia general y la gestión de riesgo.</div>
</section>"""

LESSON_CONTENT["indicadores"] = """<h1>Indicadores</h1>
<p class="subtitle">Herramientas matemáticas que se dibujan sobre la gráfica para apoyar tus decisiones.</p>

<section>
<h2>¿Qué es un indicador?</h2>
<p>Un indicador técnico es un cálculo que se hace con los datos del precio y el volumen, y que se muestra sobre la gráfica o debajo de ella. Su objetivo es ayudarte a ver cosas que a simple vista no son tan claras, como la fuerza de una tendencia o si un activo está "muy comprado" o "muy vendido".</p>
<p>Los indicadores no predicen el futuro. Son ayudas. Usar muchos a la vez puede confundir más que ayudar, así que lo recomendable es empezar con pocos y entenderlos bien.</p>
</section>

<section>
<h2>Indicadores más usados</h2>
<ul>
<li><strong>Medias móviles:</strong> suavizan el precio para mostrar la tendencia con más claridad. Las más usadas son las de 50 y 200 periodos.</li>
<li><strong>RSI (Índice de Fuerza Relativa):</strong> mide si un activo está sobrecomprado o sobrevendido. Va de 0 a 100.</li>
<li><strong>MACD:</strong> ayuda a detectar cambios en la fuerza y dirección de la tendencia.</li>
<li><strong>Volumen:</strong> muestra cuántas operaciones hubo. Un movimiento con mucho volumen suele tener más fuerza.</li>
<li><strong>Bandas de Bollinger:</strong> marcan un rango alrededor del precio; ayudan a ver volatilidad y posibles extremos.</li>
</ul>
</section>

<section>
<h2>Tipos de indicadores</h2>
<div class="card-grid">
<div class="card"><h3>De tendencia</h3><p>Ayudan a ver la dirección del mercado (medias móviles, MACD).</p></div>
<div class="card"><h3>De momento (osciladores)</h3><p>Miden la fuerza y la velocidad del movimiento (RSI).</p></div>
</div>
</section>

<section>
<div class="tip">Recuerda: los indicadores funcionan mejor en conjunto y confirmando lo que ya ves en la tendencia y las velas. Ninguno por sí solo te dará señales perfectas.</div>
</section>"""

LESSON_CONTENT["gestion-riesgo"] = """<h1>Gestión de riesgo y psicología</h1>
<p class="subtitle">La parte que separa a quien sobrevive en el trading de quien pierde su dinero rápido.</p>

<section>
<h2>¿Por qué es lo más importante?</h2>
<p>Mucha gente cree que el secreto del trading es adivinar hacia dónde va el precio. La realidad es que ni los mejores traders aciertan siempre. Lo que los mantiene a flote no es acertar más, sino perder poco cuando se equivocan.</p>
<p>Puedes equivocarte muchas veces y aun así no quebrar, siempre que cada error te cueste poco.</p>
</section>

<section>
<h2>Herramientas básicas de gestión de riesgo</h2>
<ul>
<li><strong>Stop loss:</strong> una orden que cierra tu operación automáticamente si el precio baja a cierto nivel.</li>
<li><strong>Take profit:</strong> una orden que cierra tu operación cuando llegas a la ganancia que buscabas.</li>
<li><strong>Tamaño de la posición:</strong> nunca arriesgues todo tu capital en una sola operación. Muchos traders arriesgan solo el 1% o 2% por operación.</li>
<li><strong>Relación riesgo/beneficio:</strong> antes de entrar, calcula cuánto puedes perder frente a cuánto puedes ganar.</li>
</ul>
</section>

<section>
<h2>La psicología del trader</h2>
<p>El mayor enemigo del trader no es el mercado, son sus propias emociones:</p>
<div class="card-grid">
<div class="card card-orange"><h3>FOMO (miedo a quedarse fuera)</h3><p>Entrar tarde a una operación solo porque el precio ya subió mucho.</p></div>
<div class="card card-red"><h3>Pánico</h3><p>Cerrar una operación de golpe por miedo cuando el precio se mueve en tu contra.</p></div>
</div>
<p>Otras trampas comunes son la avaricia (no cerrar una ganancia esperando más) y la venganza (intentar recuperar una pérdida con operaciones impulsivas).</p>
</section>

<section>
<h2>Buenas prácticas para empezar</h2>
<ul>
<li>Practica primero en una cuenta demo, con dinero ficticio.</li>
<li>Define un plan antes de operar: cuándo entras, cuándo sales y cuánto arriesgas.</li>
<li>Usa siempre stop loss.</li>
<li>Lleva un registro de tus operaciones para aprender de tus errores.</li>
<li>Nunca operes con dinero que necesitas para vivir.</li>
<li>No persigas pérdidas: si tuviste un mal día, mejor detente.</li>
</ul>
</section>

<section>
<h2>En resumen</h2>
<p>El trading puede ser emocionante, pero es difícil y arriesgado. Protege tu capital, controla tus emociones y recuerda que para la mayoría de las personas invertir a largo plazo es una opción más segura y sencilla. Si decides hacer trading, hazlo con educación, disciplina y dinero que puedas permitirte perder.</p>
</section>"""



# ---------------------------------------------------------------------------
# Seed function
# ---------------------------------------------------------------------------

async def seed_courses() -> None:
    """Insert courses and lessons into the database if they don't already exist."""

    async with async_session() as db:
        # Check if courses already exist
        result = await db.execute(select(Course).limit(1))
        if result.scalars().first() is not None:
            print("Courses already exist in the database. Skipping seed.")
            return

        for course_data in COURSES_DATA:
            lessons_data = course_data["lessons"]
            course = Course(
                id=course_data["id"],
                title=course_data["title"],
                description=course_data["description"],
                lesson_count=len(lessons_data),
                sort_order=course_data["sort_order"],
            )
            db.add(course)

            for lesson_data in lessons_data:
                content = LESSON_CONTENT.get(lesson_data["id"], "<p>Contenido en desarrollo</p>")
                lesson = Lesson(
                    id=lesson_data["id"],
                    course_id=course_data["id"],
                    title=lesson_data["title"],
                    content=content,
                    sort_order=lesson_data["sort_order"],
                )
                db.add(lesson)

        await db.commit()
        print(f"Seeded {len(COURSES_DATA)} courses with their lessons successfully.")


async def main() -> None:
    await seed_courses()


if __name__ == "__main__":
    asyncio.run(main())


# ---------------------------------------------------------------------------
# CURSO: Domina tu Dashboard Financiero
# ---------------------------------------------------------------------------

LESSON_CONTENT["dash-intro"] = """<h1>¿Qué es el Dashboard Financiero?</h1>
<p class="subtitle">Tu centro de control para visualizar toda tu vida financiera en un solo lugar.</p>

<section>
<h2>Para qué sirve</h2>
<p>El Dashboard Financiero es la pantalla principal donde puedes ver un resumen completo de tu situación económica actual. En vez de revisar cada app de banco, tarjeta o inversión por separado, aquí tienes todo unificado.</p>
<p>Piensa en el dashboard como el tablero de un auto: te muestra la velocidad (ingresos), el combustible (ahorro), las alertas (deudas próximas) y el estado general del viaje (patrimonio neto).</p>
</section>

<section>
<h2>¿Qué secciones tiene?</h2>
<ul>
<li><strong>Resumen principal:</strong> Patrimonio neto, ingresos y gastos del mes, y tu tasa de ahorro.</li>
<li><strong>Tarjetas de crédito:</strong> Uso, deuda y próximos pagos de cada tarjeta.</li>
<li><strong>Inversiones:</strong> Tu dinero en cuentas de ahorro, acciones, afore y préstamos.</li>
<li><strong>Ingresos vs Gastos:</strong> Gráfica de los últimos 6 meses para ver tendencias.</li>
<li><strong>Deudas:</strong> Préstamos activos con cuenta regresiva al próximo pago.</li>
<li><strong>Últimos movimientos:</strong> Tus gastos e ingresos más recientes.</li>
</ul>
</section>

<section>
<h2>¿Cómo empiezo a llenarlo?</h2>
<p>El dashboard se alimenta de los datos que registras en las otras secciones. Para que tenga información útil necesitas:</p>
<ol>
<li>Ir a <strong>Configuración</strong> y agregar tus tarjetas de crédito y cuentas de ahorro.</li>
<li>Registrar tus <strong>gastos e ingresos</strong> conforme ocurran.</li>
<li>Agregar tus <strong>deudas</strong> si tienes préstamos activos.</li>
<li>Configurar tus <strong>aportaciones</strong> si haces ahorro periódico.</li>
</ol>
<p>No tienes que llenar todo de golpe. Empieza por lo básico (ingresos y gastos) y ve agregando el resto conforme te familiarices.</p>
</section>

<section>
<div class="tip">El dashboard se actualiza automáticamente cada vez que registras un nuevo dato en cualquier sección. Entre más completa esté tu información, mejores decisiones podrás tomar.</div>
</section>"""

LESSON_CONTENT["dash-patrimonio"] = """<h1>Patrimonio neto y tasa de ahorro</h1>
<p class="subtitle">Los dos indicadores más importantes de tu salud financiera.</p>

<section>
<h2>¿Qué es el patrimonio neto?</h2>
<p>Tu patrimonio neto es la diferencia entre <strong>todo lo que tienes</strong> (activos) y <strong>todo lo que debes</strong> (pasivos).</p>
<p>La fórmula es simple:</p>
<div class="tip">Patrimonio Neto = (Ahorro + Inversiones + Afore + Acciones) − (Deuda en tarjetas)</div>
<p>Si el resultado es positivo, significa que tus activos superan tus deudas. Si es negativo, debes más de lo que tienes — y ese es el primer problema a resolver.</p>
</section>

<section>
<h2>¿Qué me dice este número?</h2>
<ul>
<li><strong>Patrimonio creciendo mes a mes:</strong> Vas por buen camino. Estás acumulando riqueza.</li>
<li><strong>Patrimonio estancado:</strong> Tus ingresos y gastos están equilibrados pero no creces. Busca optimizar.</li>
<li><strong>Patrimonio bajando:</strong> Estás gastando más de lo que ganas o tus deudas crecen. Necesitas actuar.</li>
</ul>
<p>En el dashboard verás el porcentaje de cambio vs. el mes anterior. Un "+5% vs mes anterior" significa que tu patrimonio creció 5% en un mes.</p>
</section>

<section>
<h2>¿Qué es la tasa de ahorro?</h2>
<p>La tasa de ahorro mide qué porcentaje de tus ingresos logras conservar después de todos tus gastos:</p>
<div class="tip">Tasa de Ahorro = ((Ingresos − Gastos) ÷ Ingresos) × 100</div>
<p>Por ejemplo, si ganas $20,000 y gastas $14,000, tu tasa de ahorro es 30%. Eso significa que de cada peso que ganas, conservas 30 centavos.</p>
</section>

<section>
<h2>¿Cuál es una buena tasa de ahorro?</h2>
<div class="card-grid">
<div class="card card-red"><h3>Menos de 10%</h3><p>Zona de riesgo. Cualquier imprevisto puede desestabilizarte. Prioriza reducir gastos.</p></div>
<div class="card card-orange"><h3>10% - 20%</h3><p>Aceptable. Puedes cubrir emergencias básicas pero el crecimiento es lento.</p></div>
<div class="card card-green"><h3>20% - 30%</h3><p>Muy bien. Estás construyendo patrimonio de forma sostenible. La meta del dashboard es 30%.</p></div>
<div class="card card-green"><h3>Más de 30%</h3><p>Excelente. Puedes acelerar inversiones y alcanzar metas financieras más rápido.</p></div>
</div>
</section>

<section>
<h2>¿Cómo se calcula en el dashboard?</h2>
<p>El dashboard toma automáticamente tus ingresos y gastos del mes actual (de la sección Gastos/Ingresos) y calcula la tasa. También compara con el mes anterior para que veas si vas mejorando o empeorando.</p>
</section>"""

LESSON_CONTENT["dash-gastos-ingresos"] = """<h1>Gastos e Ingresos</h1>
<p class="subtitle">El registro diario de tu dinero: de dónde viene y a dónde se va.</p>

<section>
<h2>¿Para qué sirve esta sección?</h2>
<p>Aquí registras cada movimiento de dinero: lo que ganas (ingresos) y lo que gastas (egresos). Es la base de todo tu dashboard porque de aquí salen los cálculos de balance, tasa de ahorro y patrimonio.</p>
<p>Sin datos aquí, el dashboard no puede mostrarte nada útil. Por eso es la primera sección que debes empezar a llenar.</p>
</section>

<section>
<h2>¿Qué datos necesitas registrar?</h2>
<p>Para cada movimiento necesitas:</p>
<ul>
<li><strong>Tipo:</strong> ¿Es un ingreso o un gasto?</li>
<li><strong>Fecha:</strong> ¿Cuándo ocurrió?</li>
<li><strong>Descripción:</strong> ¿Qué fue? (ej: "Uber Eats", "Nómina quincenal", "Netflix")</li>
<li><strong>Categoría:</strong> ¿En qué grupo cae? (Comida, Transporte, Entretenimiento, Salario, etc.)</li>
<li><strong>Monto:</strong> ¿Cuánto fue?</li>
</ul>
</section>

<section>
<h2>¿Qué métricas te muestra?</h2>
<div class="card-grid">
<div class="card card-green"><h3>Ingresos Totales</h3><p>La suma de todo el dinero que recibiste en el periodo seleccionado. Incluye el porcentaje de cambio vs. el mes anterior.</p></div>
<div class="card card-red"><h3>Gastos Totales</h3><p>La suma de todo lo que gastaste. Si sube mucho vs. el mes anterior, es una señal de alerta.</p></div>
<div class="card"><h3>Balance</h3><p>Ingresos menos gastos. Si es positivo, ahorraste. Si es negativo, gastaste más de lo que ganaste.</p></div>
</div>
</section>

<section>
<h2>Las gráficas</h2>
<p>La sección incluye varias gráficas que te ayudan a entender patrones:</p>
<ul>
<li><strong>Ingresos vs Gastos (6 meses):</strong> Te muestra la tendencia. ¿Tus gastos están alcanzando a tus ingresos?</li>
<li><strong>Balance Mensual:</strong> ¿Cuánto te queda cada mes? Si la línea baja, algo está mal.</li>
<li><strong>Ingresos vs (Gastos + Créditos):</strong> Incluye los pagos de tarjeta para ver tu carga real.</li>
<li><strong>Patrimonio Neto:</strong> Evolución de tu riqueza total en el tiempo.</li>
<li><strong>Ingresos por Categoría:</strong> Identifica de dónde viene tu dinero.</li>
</ul>
</section>

<section>
<h2>Consejos para llenar bien esta sección</h2>
<ol>
<li><strong>Registra todo el mismo día</strong> que ocurre. Si dejas pasar días, se te olvidan gastos pequeños.</li>
<li><strong>Usa categorías consistentes.</strong> No pongas "Comida" un día y "Alimentos" otro — usa siempre la misma.</li>
<li><strong>Incluye gastos pequeños.</strong> El café de $60, la propina de $20. Se acumulan.</li>
<li><strong>Registra todos tus ingresos:</strong> nómina, freelance, ventas, comisiones, todo.</li>
</ol>
</section>"""

LESSON_CONTENT["dash-creditos"] = """<h1>Tarjetas de crédito</h1>
<p class="subtitle">Controla tus tarjetas: uso, deuda, pagos y fechas importantes.</p>

<section>
<h2>¿Qué muestra esta sección?</h2>
<p>Aquí ves el estado de todas tus tarjetas de crédito en un solo lugar. Para cada tarjeta puedes ver:</p>
<ul>
<li><strong>Crédito total:</strong> El límite máximo que el banco te permite gastar.</li>
<li><strong>Saldo a deber:</strong> Cuánto debes actualmente.</li>
<li><strong>Disponible:</strong> Cuánto puedes gastar todavía (límite - deuda).</li>
<li><strong>Porcentaje de uso:</strong> Qué proporción de tu límite estás usando.</li>
<li><strong>Fecha de corte:</strong> Cuando se cierra tu estado de cuenta del mes.</li>
<li><strong>Fecha de pago:</strong> El último día para pagar sin generar intereses.</li>
<li><strong>Pago mínimo:</strong> Lo mínimo para no caer en mora (pero genera intereses).</li>
<li><strong>Pago para no generar intereses:</strong> Lo que necesitas pagar para evitar intereses.</li>
</ul>
</section>

<section>
<h2>¿Qué es el porcentaje de uso y por qué importa?</h2>
<p>El porcentaje de uso (o "utilización") es cuánto de tu crédito disponible estás usando:</p>
<div class="tip">Uso = (Deuda ÷ Límite de crédito) × 100</div>
<p>Este número importa mucho porque afecta tu score en Buró de Crédito:</p>
<div class="card-grid">
<div class="card card-green"><h3>0% - 30%</h3><p>Ideal. Muestra que usas tu crédito responsablemente.</p></div>
<div class="card card-orange"><h3>30% - 70%</h3><p>Precaución. Empieza a impactar negativamente tu score.</p></div>
<div class="card card-red"><h3>70% - 100%</h3><p>Peligro. Señal de sobreendeudamiento. Afecta mucho tu historial.</p></div>
</div>
</section>

<section>
<h2>La cuenta regresiva de pago</h2>
<p>Cada tarjeta muestra un contador con los días que faltan para tu fecha de pago. Esto te ayuda a planificar:</p>
<ul>
<li><strong>Verde (más de 7 días):</strong> Tienes tiempo. Planifica el pago.</li>
<li><strong>Amarillo (3-7 días):</strong> Prepárate. Asegura que tengas el dinero.</li>
<li><strong>Rojo (menos de 3 días):</strong> Urgente. Paga ya para evitar intereses o mora.</li>
</ul>
</section>

<section>
<h2>¿Cómo llenar esta sección?</h2>
<ol>
<li>Ve a <strong>Configuración → Créditos</strong> y agrega cada tarjeta (nombre y color).</li>
<li>Actualiza los datos cada semana: saldo actual, fechas de corte y pago.</li>
<li>El dashboard te recordará los lunes si hay datos pendientes de actualizar.</li>
</ol>
<div class="tip">Lo más importante es mantener actualizado el "Pago para no generar intereses" — ese es el número que debes pagar antes de tu fecha límite para no caer en deuda revolvente.</div>
</section>"""

LESSON_CONTENT["dash-deudas"] = """<h1>Deudas y préstamos</h1>
<p class="subtitle">Lleva el control de lo que debes: cuánto, a quién y cuándo vence.</p>

<section>
<h2>¿Qué es esta sección?</h2>
<p>Aquí registras todas tus deudas que NO son de tarjeta de crédito: préstamos personales, Fonacot, crédito de nómina, financiamientos, meses sin intereses, préstamos familiares, etc.</p>
<p>La diferencia con la sección de créditos es que aquí son deudas con un monto fijo que se va reduciendo con cada pago, mientras que las tarjetas son crédito revolvente.</p>
</section>

<section>
<h2>¿Qué datos necesitas para cada deuda?</h2>
<ul>
<li><strong>Nombre del préstamo:</strong> Identificador (ej: "Fonacot", "Liverpool MSI", "Préstamo familiar").</li>
<li><strong>Deuda total:</strong> Cuánto debes en total actualmente.</li>
<li><strong>Temporalidad:</strong> ¿Pagas mensual o quincenal?</li>
<li><strong>Cantidad a pagar por periodo:</strong> Cuánto pagas cada mes o quincena.</li>
<li><strong>Fecha de pago:</strong> Cuándo vence el próximo pago.</li>
</ul>
</section>

<section>
<h2>¿Qué métricas te muestra?</h2>
<div class="card-grid">
<div class="card"><h3>Deuda Total</h3><p>La suma de todas tus deudas activas. Este número debe ir bajando cada mes.</p></div>
<div class="card"><h3>Préstamos Activos</h3><p>Cuántas deudas tienes abiertas simultáneamente.</p></div>
<div class="card"><h3>Próximo Pago</h3><p>Cuántos días faltan y cuánto necesitas tener listo.</p></div>
</div>
</section>

<section>
<h2>Pagos restantes</h2>
<p>El sistema calcula automáticamente cuántos pagos te faltan dividiendo tu deuda total entre el monto de cada pago. Esto te da una idea clara de cuándo terminarás de pagar.</p>
<p>Ejemplo: Si debes $28,000 y pagas $2,800 al mes, te faltan 10 pagos (aproximadamente 10 meses).</p>
</section>

<section>
<h2>Estrategias para pagar deudas</h2>
<ul>
<li><strong>Método bola de nieve:</strong> Paga primero la deuda más pequeña. Al terminarla, usa ese dinero para atacar la siguiente. Te da motivación rápida.</li>
<li><strong>Método avalancha:</strong> Paga primero la deuda con mayor tasa de interés. Matemáticamente ahorras más dinero así.</li>
<li><strong>Meses sin intereses:</strong> No generan intereses si pagas a tiempo, pero siguen siendo compromisos. Registrarlos te ayuda a no olvidarlos.</li>
</ul>
</section>"""

LESSON_CONTENT["dash-inversiones"] = """<h1>Inversiones y ahorro</h1>
<p class="subtitle">Donde crece tu dinero: cuentas de ahorro, acciones, afore y préstamos personales.</p>

<section>
<h2>¿Qué incluye esta sección?</h2>
<p>La sección de Inversiones tiene 4 sub-secciones:</p>
<div class="card-grid">
<div class="card"><h3>Cuentas de Ahorro</h3><p>Tu dinero líquido generando intereses diarios (Nu, Mercado Pago, CETES, etc.)</p></div>
<div class="card"><h3>Préstamos</h3><p>Dinero que TÚ prestaste a alguien y que te está generando intereses.</p></div>
<div class="card"><h3>Afore</h3><p>Tu cuenta de retiro: saldo, rendimiento y proyección a largo plazo.</p></div>
<div class="card"><h3>Acciones (GBM)</h3><p>Tu portafolio de bolsa: acciones, ETFs, rendimientos y distribución.</p></div>
</div>
</section>

<section>
<h2>Cuentas de ahorro: lo que te muestra</h2>
<p>Para cada cuenta de ahorro (Nu, Mercado Pago, Stori, etc.) el dashboard te muestra:</p>
<ul>
<li><strong>Saldo actual:</strong> Cuánto tienes en esa cuenta.</li>
<li><strong>Tasa anual:</strong> El rendimiento que te da (ej: 15% anual en Nu).</li>
<li><strong>Ganancia diaria:</strong> Cuánto generas cada día solo por tener tu dinero ahí.</li>
<li><strong>Proyección:</strong> Cuánto tendrás en 1 semana, 1 mes, 6 meses, 1 año, etc. con interés compuesto.</li>
</ul>
<div class="tip">La ganancia diaria es aproximada. El cálculo considera impuestos (ISR retenido) para darte un número más realista.</div>
</section>

<section>
<h2>El portafolio total</h2>
<p>En el dashboard principal, la sección de inversiones muestra tu "Portafolio Total" que suma:</p>
<p><strong>Liquidez</strong> (cuentas de ahorro) + <strong>Préstamos activos</strong> + <strong>Acciones/ETFs</strong> (GBM) + <strong>Afore</strong></p>
<p>Este número, junto con la deuda de tus tarjetas, determina tu patrimonio neto.</p>
</section>

<section>
<h2>¿Cómo actualizar los datos?</h2>
<ul>
<li><strong>Cuentas de ahorro:</strong> Haz clic en el ícono de editar (lápiz) en cada cuenta y actualiza el saldo.</li>
<li><strong>Acciones (GBM):</strong> Sube los archivos Excel que descargas de la app GBM (Nacional y USA).</li>
<li><strong>Afore:</strong> Actualízalo el día 1 de cada mes con los datos de tu estado de cuenta.</li>
<li><strong>Préstamos:</strong> Agrega préstamos que tú hayas dado (capital, tasa, plazo).</li>
</ul>
</section>

<section>
<h2>Ganancias diarias por intereses</h2>
<p>En el dashboard principal hay una sección que muestra cuánto ganas CADA DÍA solo por tener tu dinero en cuentas de ahorro. Esto te motiva a mantener el dinero invertido en vez de gastarlo:</p>
<p>Ejemplo: Si tienes $45,000 en Nu al 15% anual, ganas aproximadamente $16.4 pesos diarios sin hacer nada.</p>
</section>"""

LESSON_CONTENT["dash-aportaciones"] = """<h1>Aportaciones periódicas</h1>
<p class="subtitle">Tu sistema de ahorro disciplinado: registra y da seguimiento a tus compromisos de ahorro.</p>

<section>
<h2>¿Qué son las aportaciones?</h2>
<p>Las aportaciones son compromisos de ahorro que te fijas a ti mismo. Por ejemplo:</p>
<ul>
<li>"Voy a depositar $2,000 a mi fondo de emergencia cada quincena."</li>
<li>"Voy a invertir $3,000 en CETES cada mes."</li>
<li>"Voy a ahorrar $1,500 mensual para vacaciones."</li>
</ul>
<p>Esta sección te ayuda a hacer seguimiento de si cumples o no con esos compromisos.</p>
</section>

<section>
<h2>¿Cómo funciona?</h2>
<p>Configuras tus aportaciones en <strong>Configuración → Aportaciones</strong> indicando:</p>
<ul>
<li><strong>Nombre/Objetivo:</strong> Para qué es (ej: "Fondo de emergencia").</li>
<li><strong>Monto:</strong> Cuánto te comprometes a aportar.</li>
<li><strong>Frecuencia:</strong> Semanal, quincenal o mensual.</li>
</ul>
<p>El sistema genera automáticamente los periodos del mes y tú marcas cada uno como "Realizada" o "Pendiente".</p>
</section>

<section>
<h2>Los estados de cada aportación</h2>
<div class="card-grid">
<div class="card card-green"><h3>Realizada</h3><p>Ya hiciste esa aportación en el periodo indicado.</p></div>
<div class="card card-orange"><h3>Pendiente</h3><p>Todavía no la has hecho pero estás a tiempo.</p></div>
</div>
</section>

<section>
<h2>¿Por qué es importante?</h2>
<p>Las aportaciones periódicas son el hábito más poderoso en finanzas personales. No importa si empiezas con $500 al mes — lo que importa es la consistencia.</p>
<p>Beneficios de tener este seguimiento:</p>
<ul>
<li><strong>Visibilidad:</strong> Ves de un vistazo si estás cumpliendo con tus compromisos.</li>
<li><strong>Accountability:</strong> Es más difícil "saltarse" una aportación cuando la ves marcada como pendiente.</li>
<li><strong>Progreso:</strong> Al final del mes puedes ver cuántos periodos cumpliste.</li>
</ul>
</section>

<section>
<h2>Consejos</h2>
<ol>
<li><strong>Programa transferencias automáticas</strong> el día que recibes tu ingreso. Así no depende de tu fuerza de voluntad.</li>
<li><strong>Empieza pequeño.</strong> Es mejor aportar $500 consistentemente que comprometerte a $5,000 y no cumplir.</li>
<li><strong>Revisa cada mes.</strong> Si llevas varios periodos "pendiente", tal vez necesitas ajustar el monto a algo más realista.</li>
</ol>
<div class="tip">La regla de oro: págate a ti primero. Cuando recibes tu ingreso, lo primero que sale debería ser tu aportación al ahorro. Los gastos se ajustan a lo que queda.</div>
</section>"""
