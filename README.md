# API Barbería 💈 (TFG)

API para gestionar barberos, servicios, reservas y reseñas. Construida con FastAPI + SQLModel + PostgreSQL. Lista para ejecutarse en Docker o localmente y con seeding automático (datos iniciales, usuario admin, etc.).

> Elevator pitch: Plataforma backend para una barbería: catálogo, disponibilidad, reservas, autenticación JWT y recursos multimedia listos para integrarse con app móvil o web.

## Contenido
- [Quick Start](#quick-start)
- [Requisitos](#requisitos)
- [Instalación Local](#instalación-local)
- [Ejecución con Docker Compose](#ejecución-con-docker-compose)
- [Variables de Entorno](#variables-de-entorno)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Endpoints Principales](#endpoints-principales)
- [Autenticación](#autenticación)
- [Base de Datos](#base-de-datos)
- [Troubleshooting](#troubleshooting)
- [Desarrollo y Notas](#desarrollo-y-notas)
- [Licencia](#licencia)

## Quick Start

```powershell
git clone https://github.com/garzastrabajo/TFGSistemaDeGestionDeCitasParaPeluqueriasBackend.git
cd TFGSistemaDeGestionDeCitasParaPeluqueriasBackend
docker compose up --build -d
# Docs: http://localhost:25007/docs
```

## Requisitos
- Python 3.11+ (solo si ejecutarás sin Docker)
- Docker Desktop 24+ (para entorno contenedorizado)
- Windows PowerShell (comandos listos para copiar/pegar)

## Instalación Local

1. (Opcional) Limpieza:
```powershell
Deactivate 2>$null; Start-Sleep -Milliseconds 200
Remove-Item -Recurse -Force .venv 2>$null
Remove-Item data.db 2>$null
```
2. Verificar Python:
```powershell
python --version
where python
```
3. Crear entorno virtual:
```powershell
python -m venv .venv
```
4. Activar entorno:
```powershell
./.venv/Scripts/Activate.ps1
```
5. Actualizar pip (manejo TLS):
```powershell
./.venv/Scripts/python.exe -m pip install --upgrade pip
```
Si aparece error de certificados:
```powershell
$env:CURL_CA_BUNDLE=$null; $env:REQUESTS_CA_BUNDLE=$null; $env:SSL_CERT_FILE=$null; $env:PIP_CERT=$null
./.venv/Scripts/python.exe -m pip install --upgrade pip
```
6. Instalar dependencias:
```powershell
./.venv/Scripts/python.exe -m pip install -r requirements.txt
```
7. Crear `.env` rápido:
```powershell
@"
APP_ENV=development
DATABASE_URL=sqlite:///./data.db
SECRET_KEY=pon-una-clave-larga-y-aleatoria
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
"@ | Out-File -Encoding utf8 .env
```
8. Prueba rápida:
```powershell
./.venv/Scripts/python.exe -c "import fastapi, sqlmodel, PIL; print('Imports OK')"
```
9. Servidor dev (autoreload):
```powershell
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload --log-level info
```
10. Salud y docs (nueva ventana):
```powershell
Invoke-RestMethod -Method GET http://127.0.0.1:8000/health
Start-Process "http://127.0.0.1:8000/docs"
```

> **Nota:** Si el puerto 8000 está en uso: `Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess` y luego `Stop-Process -Id <PID>`.

## Ejecución con Docker Compose

```powershell
docker compose up --build -d
docker compose logs -f api  # ver inicio y seeding
```

- API: http://localhost:25007
- Docs: http://localhost:25007/docs
- PostgreSQL: localhost:6543 (admin / 1234 / tfg_peluqueria)

Parar y limpiar:
```powershell
docker compose down
```

### Docker Desktop no iniciado
Error típico:
```
open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified
```
Solución:
```powershell
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
$retries=30
for ($i=0; $i -lt $retries; $i++) {
  try { docker info | Out-Null; Write-Host "Docker engine listo" -ForegroundColor Green; break }
  catch { Write-Host "Esperando Docker... ($($i+1)/$retries)" -ForegroundColor Yellow; Start-Sleep -Seconds 4 }
}
docker compose up --build -d
```
Verificar WSL2:
```powershell
wsl -l -v
```

## Variables de Entorno
| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `DATABASE_URL` | Cadena conexión SQLModel/SQLAlchemy | `postgresql+psycopg2://admin:1234@localhost:6543/tfg_peluqueria` |
| `SECRET_KEY` | Clave JWT HS256 | Largo y aleatorio |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Minutos de validez access token | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Días de validez refresh token | `7` |
| `APP_ENV` | Entorno (`development`/`production`) | `development` |

## Estructura del Proyecto
```
app/
  main.py
  db.py
  endpoints/
    auth.py, bookings.py, ...
  models/
    barber.py, booking.py, ...
  helpers/
    seed.py, scheduling.py, ratings.py, db_memory.py
Dockerfile
docker-compose.yml
requirements.txt
.env
README.md
scripts/
  backfill_user_photo_urls.py
```

## Endpoints Principales
| Recurso | Método(s) | Ruta(s) |
|---------|-----------|---------|
| Root | GET | `/` |
| Health | GET | `/health` |
| Auth | POST | `/auth/register`, `/auth/login`, `/auth/refresh`* |
| Users | GET / PUT / POST | `/users/me`, `/users/me/photo` |
| Barbers | GET / POST / PUT / DELETE | `/barbers`, `/barbers/{id}`, `/barbers/by-service/{service_id}` |
| Barbershop | GET / POST | `/barbershop` |
| Services | GET / POST / PUT / DELETE | `/services`, `/services/{id}`, `/services/by-category/{category_id}` |
| Service Categories | GET / POST / PUT / DELETE | `/service-categories`, `/service-categories/{id}` |
| Products | GET / POST / PUT / DELETE | `/products`, `/products/{id}`, `/products/by-category/{category_id}` |
| Product Categories | GET / POST / PUT / DELETE | `/product-categories`, `/product-categories/{id}` |
| Gallery | GET / POST / PUT / DELETE | `/gallery`, `/gallery/{id}` |
| Reviews | GET / POST / PUT / DELETE | `/reviews`, `/reviews/{id}` |
| Availability | GET | `/availability` |
| Bookings | GET / POST | `/bookings`, `/bookings/{id}`, `/bookings/me` |
*`/auth/refresh` depende de implementación.

## Autenticación
JWT HS256. Flujo básico:
1. Registro: `POST /auth/register`
2. Login: `POST /auth/login` → devuelve `access_token` y (opcional) `refresh_token`
3. Perfil: `GET /auth/me` con cabecera `Authorization: Bearer <access_token>`

Ejemplo rápido:
```powershell
$reg = @{ username='demo'; password='Demo#1234'; email='demo@example.com' } | ConvertTo-Json
Invoke-RestMethod -Method POST http://localhost:25007/auth/register -ContentType 'application/json' -Body $reg
$login = @{ username='demo'; password='Demo#1234' } | ConvertTo-Json
$tokens = Invoke-RestMethod -Method POST http://localhost:25007/auth/login -ContentType 'application/json' -Body $login
$access = $tokens.access_token
Invoke-RestMethod -Method GET http://localhost:25007/auth/me -Headers @{ Authorization = "Bearer $access" }
```

> **Warning:** Cambia `SECRET_KEY` y restringe CORS en producción.

## Base de Datos
- Local por defecto: SQLite (`data.db`)
- Docker Compose: PostgreSQL (persistencia + volumen `pgdata`)
- Seeding automático al arrancar: barbería, barberos, categorías, servicios, productos, reseñas demo, usuario admin (`admin/admin`).

Conexión PostgreSQL (DBeaver / JDBC / psql):
```
Host: localhost
Port: 6543
DB: tfg_peluqueria
User: admin
Pass: 1234
```
JDBC:
```
jdbc:postgresql://localhost:6543/tfg_peluqueria?user=admin&password=1234
```
psql:
```powershell
psql "postgresql://admin:1234@localhost:6543/tfg_peluqueria"
```

## Troubleshooting
| Problema | Causa | Solución |
|----------|-------|----------|
| Error TLS pip (CA bundle) | Var entorno apunta a ruta inválida | Limpiar vars (`CURL_CA_BUNDLE`, etc.) y reinstalar pip |
| `ModuleNotFoundError: pydantic_core` | Wheel corrupto o versión cruzada | Reinstalar pydantic y pydantic-core (ver sección instalación) |
| Named pipe Docker | Docker Desktop apagado | Iniciar Docker Desktop y esperar `docker info` OK |
| Puerto 8000 ocupado | Proceso previo | Identificar PID y terminarlo (`Stop-Process`) |
| Cambios no recargan | Falta `--reload` | Usar comando uvicorn con `--reload` |
| Pillow ausente | Instalación incompleta | `pip install Pillow` |
| SQLite lock frecuente | Accesos simultáneos | Usar PostgreSQL para concurrencia real |

> **Nota:** Para inspeccionar imágenes de usuario: `docker exec -it tfg-api ls -la /app/static/user-photos`.

## Desarrollo y Notas
- El seeding solo crea datos si las tablas están vacías (idempotente).
- Usuario admin por defecto: `admin / admin` (cambiar en producción).
- Carpeta estática: `./static/user-photos` (se crea al startup).
- Script utilitario: crear `run_dev.ps1`:
```powershell
@'
Write-Host 'Activando entorno...' -ForegroundColor Cyan
./.venv/Scripts/Activate.ps1
Write-Host 'Arrancando servidor...' -ForegroundColor Green
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload --log-level info
'@ | Out-File -Encoding utf8 run_dev.ps1
./run_dev.ps1
```

## Licencia
Proyecto académico (TFG). Ajustar según políticas institucionales. Uso interno y educativo.

---
Hecho con FastAPI + SQLModel 💈  – ¡Feliz hacking!


