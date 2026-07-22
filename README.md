# Finalat

Plataforma de finanzas personales para Mexico. Incluye un agente conversacional con IA, dashboard financiero, modulo educativo y herramientas de optimizacion de inversiones.

---

## Arquitectura

| Capa | Tecnologia | Despliegue |
|------|-----------|------------|
| Frontend | Vue 3 + TypeScript + Vite | S3 + CloudFront |
| Backend | FastAPI (Python 3.13) | EC2 (systemd) |
| Base de datos | PostgreSQL 15 (prod) / SQLite (dev) | RDS / local |
| Autenticacion | Firebase Auth | Firebase |
| IA | Amazon Bedrock (Nova Pro) | AWS |
| Migraciones | Alembic | CI/CD |

---

## Estructura del proyecto

```
Finalat/
├── backend/
│   ├── alembic/            # Migraciones de base de datos
│   ├── finanzas/           # Logica de negocio financiera
│   ├── middleware/         # Auth, rate limiter, security headers
│   ├── models/             # Modelos SQLAlchemy (15 tablas)
│   ├── routers/            # Endpoints FastAPI (17 routers)
│   ├── schemas/            # Esquemas Pydantic (request/response)
│   ├── services/           # Servicios externos (Bedrock, Banxico, scrapers)
│   ├── config.py           # Configuracion via env vars
│   ├── main.py             # Entry point de la API
│   └── requirements.txt    # Dependencias Python
├── frontend/
│   ├── src/
│   │   ├── components/     # Componentes reutilizables
│   │   ├── finanzas/       # Modulo de finanzas (views + layout)
│   │   ├── services/       # Clientes API (axios)
│   │   ├── stores/         # Estado global (Pinia)
│   │   ├── views/          # Vistas principales
│   │   ├── firebase.ts     # Configuracion Firebase
│   │   └── main.ts         # Entry point + rutas
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── .github/workflows/      # CI/CD (GitHub Actions)
└── .env                    # Variables de entorno (no committear)
```

---

## Requisitos previos

- **Python** 3.13+
- **Node.js** 20+ (LTS)
- **PostgreSQL** 15+ (produccion) o SQLite (desarrollo local)
- Cuenta de **Firebase** (autenticacion)
- Credenciales **AWS** (Bedrock, S3, CloudFront)

---

## Instalacion local

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Crea un archivo `backend/.env` con las variables necesarias:

```env
DATABASE_URL=sqlite+aiosqlite:///./finalat.db
FERNET_KEY=<clave-fernet-generada>
FIREBASE_PROJECT_ID=<tu-project-id>
FIREBASE_WEB_API_KEY=<tu-api-key>
BMX_TOKEN=<token-banxico>
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=<tu-key>
AWS_SECRET_ACCESS_KEY=<tu-secret>
BEDROCK_MODEL_ID=amazon.nova-pro-v1:0
CORS_ORIGINS=http://localhost:5173
APP_ENV=development
```

Para generar una clave Fernet:

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

Ejecuta migraciones y levanta el servidor:

```bash
alembic upgrade head
uvicorn backend.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

La app estara disponible en `http://localhost:5173`. El proxy de Vite redirige `/api` al backend en el puerto 8000.

---

## Scripts disponibles

### Backend

| Comando | Descripcion |
|---------|------------|
| `uvicorn backend.main:app --reload` | Servidor de desarrollo |
| `alembic upgrade head` | Ejecutar migraciones |
| `alembic revision --autogenerate -m "desc"` | Crear nueva migracion |
| `pytest --tb=short -q` | Ejecutar tests |
| `ruff check .` | Linting |

### Frontend

| Comando | Descripcion |
|---------|------------|
| `npm run dev` | Servidor de desarrollo (Vite) |
| `npm run build` | Build de produccion (vue-tsc + vite) |
| `npm run preview` | Preview del build local |

---

## Modulos principales

### Finanzas personales
- **Ahorro**: Registro y seguimiento de cuentas de ahorro
- **Creditos**: Gestion de creditos activos
- **Gastos/Ingresos**: Registro categorizado de movimientos
- **Deudas**: Control de deudas y amortizaciones
- **Aportaciones**: Aportaciones voluntarias (Afore, inversiones)
- **Afore**: Seguimiento del saldo de Afore
- **GBM Portfolio**: Portafolio de inversiones (GBM+)
- **Patrimonio**: Vista consolidada del patrimonio neto

### Agente IA (Fina)
Asistente financiero conversacional basado en Amazon Bedrock (Nova Pro). Proporciona recomendaciones personalizadas con base en los datos del usuario.

### Modulo educativo
Catalogo de cursos con lecciones y seguimiento de progreso.

### Herramientas
- **Optimizador de inversiones**: Sugiere distribucion de portafolio
- **Tasas de referencia**: Scraping automatico de tasas CETES via Banxico
- **Instrumentos financieros**: Catalogo de instrumentos disponibles en Mexico

---

## API

La API corre en `/api` y expone los siguientes grupos de endpoints:

| Prefijo | Descripcion |
|---------|------------|
| `/api/ahorro` | Cuentas de ahorro |
| `/api/creditos` | Creditos |
| `/api/gastos-ingresos` | Gastos e ingresos |
| `/api/deudas` | Deudas |
| `/api/aportaciones` | Aportaciones voluntarias |
| `/api/afore` | Afore |
| `/api/gbm` | Portafolio GBM |
| `/api/patrimonio` | Patrimonio consolidado |
| `/api/categories` | Categorias de gastos |
| `/api/instruments` | Instrumentos financieros |
| `/api/optimizer` | Optimizador de portafolio |
| `/api/courses` | Cursos y lecciones |
| `/api/advisor` | Asesor IA |
| `/api/chat` | Chat con agente Fina |
| `/api/scrapers` | Sincronizacion de tasas |
| `/api/finanzas` | Dashboard financiero |
| `/api/update-tracker` | Rastreo de actualizaciones |

Documentacion interactiva disponible en `/docs` (Swagger UI) y `/redoc`.

---

## CI/CD

El proyecto usa GitHub Actions con tres workflows:

1. **ci.yml** - Se ejecuta en push/PR a `main` y `prd`:
   - Backend: linting (ruff), type checking (mypy), tests (pytest)
   - Frontend: build (vue-tsc + vite), tests (vitest)

2. **deploy-backend.yml** - Deploy automatico a EC2 en push a `main`:
   - Ejecuta tests con PostgreSQL
   - Conecta via SSH, pull del codigo, instala dependencias
   - Corre migraciones de Alembic
   - Reinicia servicio systemd

3. **deploy-frontend.yml** - Deploy automatico a S3/CloudFront en push a `main`:
   - Build del SPA
   - Sync a S3 con estrategia de cache (assets inmutables, index.html corto)
   - Invalidacion de cache en CloudFront

---

## Stack tecnologico

### Backend
- FastAPI + Uvicorn
- SQLAlchemy 2.0 (async) + asyncpg
- Alembic (migraciones)
- Pydantic v2 (validacion)
- cryptography (cifrado de campos sensibles)
- PyJWT (verificacion de tokens Firebase)
- httpx + BeautifulSoup4 (scraping)
- APScheduler (tareas programadas)
- boto3 (Amazon Bedrock)
- pytest + hypothesis (testing)

### Frontend
- Vue 3 (Composition API + `<script setup>`)
- TypeScript
- Vite 5
- Pinia (state management)
- Vue Router 4
- PrimeVue 4 (componentes UI)
- Tailwind CSS 3 (utilidades)
- Chart.js + vue-chartjs (graficas)
- Firebase SDK (autenticacion)
- Axios (HTTP client)

---

## Seguridad

- Autenticacion via Firebase Auth (JWT verificado en middleware)
- Cifrado de campos sensibles con Fernet (AES-128-CBC)
- Rate limiting por usuario/IP
- Security headers (CSP, HSTS, X-Frame-Options)
- Compresion GZip para respuestas > 1KB
- CORS configurado por entorno

---

## Licencia

Proyecto privado. Todos los derechos reservados.
