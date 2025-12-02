# API Barbería 💈 (TFG)

FastAPI + SQLModel + PostgreSQL con Docker Compose. Esta guía refleja el flujo real del proyecto (API en contenedor, Postgres y semillas automáticas).

Docs interactivas:
- Docker: http://localhost:25007/docs
- Local (sin Docker): http://127.0.0.1:8000/docs

## Requisitos

- Python 3.11+ (opcional si usas Docker)
- Windows PowerShell (copiar/pegar comandos)
- Docker Desktop 24+

## Estructura resumida

```
app/
  main.py  db.py
  endpoints/ (routers FastAPI)
  models/ (*Table para SQLModel + Pydantic)
  helpers/ (seed, memoria, utilidades)
Dockerfile
docker-compose.yml
requirements.txt
```

## 0. Limpieza opcional (solo si quieres empezar desde cero)
```powershell
Deactivate 2>$null; Start-Sleep -Milliseconds 200
Remove-Item -Recurse -Force .venv 2>$null
Remove-Item data.db 2>$null
``` 

## 1. Verificar Python
```powershell
python --version
where python
```
Debe mostrar una versión >= 3.11.

## 2. Crear entorno virtual (modo local)
```powershell
python -m venv .venv
```

## 3. Activar entorno
```powershell
.\.venv\Scripts\Activate.ps1
```
Prompt debe incluir `(.venv)`.

## 4. Actualizar pip (manejo de posible error TLS)
```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```
Si sale error de certificado (CA bundle) ejecuta:
```powershell
$env:CURL_CA_BUNDLE=$null; $env:REQUESTS_CA_BUNDLE=$null; $env:SSL_CERT_FILE=$null; $env:PIP_CERT=$null
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

## 5. Instalar dependencias
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 6. Crear / refrescar `.env`
```powershell
@"
APP_ENV=development
DATABASE_URL=sqlite:///./data.db
SECRET_KEY=pon-una-clave-larga-y-aleatoria
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
"@ | Out-File -Encoding utf8 .env
```

## 7. Prueba rápida de imports
```powershell
.\.venv\Scripts\python.exe -c "import fastapi, sqlmodel, PIL; print('Imports OK')"
```

## 8. (Solo si tuviste error `pydantic_core._pydantic_core`)
```powershell
.\.venv\Scripts\python.exe -m pip install --force-reinstall --no-cache-dir pydantic==2.12.4 pydantic-core==2.41.5
.\.venv\Scripts\python.exe -c "import pydantic_core, pydantic; print('Pydantic OK', pydantic.__version__, pydantic_core.__version__)"
```

## 9. Arrancar servidor (desarrollo con autoreload)
```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --log-level info
```
Mantén esta consola abierta.

## 10. Verificar salud y docs (en consola separada)
```powershell
Invoke-RestMethod -Method GET http://127.0.0.1:8000/health
Start-Process "http://127.0.0.1:8000/docs"
```

## 11. Registro + Login + Perfil (flujo JWT)
```powershell
$reg = @{ username = 'demo'; password = 'Demo#1234'; email = 'demo@example.com' } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri http://localhost:25007/auth/register -ContentType 'application/json' -Body $reg

$login = @{ username = 'demo'; password = 'Demo#1234' } | ConvertTo-Json
$tokens = Invoke-RestMethod -Method POST -Uri http://localhost:25007/auth/login -ContentType 'application/json' -Body $login
$access = $tokens.access_token
Invoke-RestMethod -Method GET -Uri http://localhost:25007/auth/me -Headers @{ Authorization = "Bearer $access" }
```

## 12. Backend con Docker Compose (recomendado)
La API y Postgres corren en contenedores. El API espera a que Postgres esté sano antes de arrancar.

```powershell
# Construir y levantar el backend en segundo plano
docker compose up --build -d

# Ver logs si lo necesitas
docker compose logs -f api

# Parar y eliminar contenedores
docker compose down
```

- API: `http://localhost:25007`
- Docs: `http://localhost:25007/docs`
- DB Postgres: servicio `db` en red docker; desde el host en `localhost:6543`.
- Volúmenes: datos de Postgres (`pgdata`) y estáticos (`static_data`).

- PostgreSQL queda accesible desde el host en `localhost:6543` con:
  - Usuario: `admin`
  - Contraseña: `1234`
  - Base de datos: `tfg_peluqueria`

Para desarrollo puedes dejar `--reload` (hot-reload). En producción, elimina esa bandera del `docker-compose.yml`.

### Si Docker Desktop no está iniciado (Windows)

Si al ejecutar Docker ves un error como:

```
open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified
```

significa que el motor de Docker no está levantado. Arráncalo y espera a que esté listo antes de usar `docker compose`:

```powershell
# 1) Abrir Docker Desktop
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

# 2) Esperar a que el engine esté listo (hasta ~2 min)
$retries=30
for ($i=0; $i -lt $retries; $i++) {
  try { docker info | Out-Null; Write-Host "Docker engine is ready" -ForegroundColor Green; break }
  catch { Write-Host "Waiting for Docker Desktop... ($($i+1)/$retries)" -ForegroundColor Yellow; Start-Sleep -Seconds 4 }
}

# 3) Construir y levantar el servicio
docker compose up --build -d

# 4) Comprobar logs y salud
docker compose logs --tail=100 api
Invoke-RestMethod -Method GET http://localhost:25007/health
```

Para verificar WSL2 y la distro de Docker:

```powershell
wsl -l -v
```

Si `docker-desktop` aparece detenido o no está, abre Docker Desktop y en Settings → General activa “Use the WSL 2 based engine”. En Settings → Resources → WSL Integration, habilita la integración con tu distro de trabajo.
$reg = @{ username = 'demo'; password = 'Demo#1234'; email = 'demo@example.com' } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri http://localhost:25007/auth/register -ContentType 'application/json' -Body $reg

$login = @{ username = 'demo'; password = 'Demo#1234' } | ConvertTo-Json
$tokens = Invoke-RestMethod -Method POST -Uri http://localhost:25007/auth/login -ContentType 'application/json' -Body $login
$access = $tokens.access_token
Invoke-RestMethod -Method GET -Uri http://localhost:25007/auth/me -Headers @{ Authorization = "Bearer $access" }
```

## 12. Listar barberos
```powershell
Invoke-RestMethod -Method GET http://localhost:25007/barbers
```

## 13. Foto de perfil (curl)
```powershell
curl -X POST http://localhost:25007/users/me/photo -H "Authorization: Bearer $access" -F "file=@foto.jpg"
```

## 14. Comprobar carpeta estática
- Local (sin Docker):
  ```powershell
  Test-Path .\static\user-photos
  Get-ChildItem .\static\user-photos | Select-Object Name, Length
  ```
- Con Docker (volumen nombrado):
  ```powershell
  docker exec -it tfg-api ls -la /app/static/user-photos 2>$null
  # Si quieres ver los ficheros en el host, cambia el volumen a bind mount en docker-compose.yml:
  #   - ./static:/app/static
  ```

## 15. Script auxiliar (opcional)
```powershell
@'
Write-Host 'Activando entorno...' -ForegroundColor Cyan
.\.venv\Scripts\Activate.ps1
Write-Host 'Revisando dependencias...' -ForegroundColor Cyan
.\.venv\Scripts\python.exe -m pip show fastapi sqlmodel Pillow | Out-Null
Write-Host 'Arrancando servidor...' -ForegroundColor Green
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --log-level info
'@ | Out-File -Encoding utf8 run_dev.ps1
```
Ejecutar:
```powershell
./run_dev.ps1
```

---
## Troubleshooting rápido

| Problema | Causa | Solución |
|----------|-------|----------|
| Error TLS pip (CA bundle) | Variable global apunta a ruta inválida | Limpiar vars y reintentar (paso 4). |
| `ModuleNotFoundError: pydantic_core` | Wheel corrupto o versión cruzada | Paso 8 (reinstalar). |
| Docker named pipe no encontrado (`dockerDesktopLinuxEngine`) | Docker Desktop apagado o WSL2 no iniciado | Inicia Docker Desktop, espera a que `docker info` funcione y reintenta `docker compose up`. Ver sección "Si Docker Desktop no está iniciado". |
| Puerto 8000 ocupado | Instancia previa | `Get-NetTCPConnection -LocalPort 8000` luego `Stop-Process -Id <PID>`. |
| Cambios no recargan | Falta `--reload` | Usar comando del paso 9. |
| Pillow ausente | Instalación incompleta | `pip install Pillow`. |

## Endpoints principales (ver `/docs`)
`/`, `/health`, `/auth/*`, `/barbers`, `/products`, `/product-categories`, `/services`, `/service-categories`, `/barbershop`, `/gallery`, `/reviews`, `/availability`, `/bookings`.

## Base de datos
Producción/Compose: PostgreSQL. Desarrollo local (sin Docker): SQLite (`data.db`). Las tablas se crean al startup y se insertan semillas si están vacías (incluye usuario admin por defecto `admin/admin`).

## Conexión a PostgreSQL (DBeaver / psql)

Si levantas con Docker Compose, el servicio de Postgres se expone en el puerto 6543 del host.

DBeaver (recomendado):

- Host: `localhost`
- Port: `6543`
- Database: `tfg_peluqueria`
- User: `admin`
- Password: `1234`
- URL JDBC (alternativa): `jdbc:postgresql://localhost:6543/tfg_peluqueria?user=admin&password=1234`

psql (línea de comandos):

- Si tienes `psql` instalado en Windows:
  ```powershell
  psql "postgresql://admin:1234@localhost:6543/tfg_peluqueria"
  ```
- Desde Docker (sin instalar nada en el host):
  ```powershell
  docker exec -it tfg-postgres psql -U admin -d tfg_peluqueria
  ```

Troubleshooting rápido conexión Postgres:

- Asegúrate de usar el puerto `6543` (el `5432` puede estar ocupado por otro Postgres local).
- Verificar puerto:
  ```powershell
  Test-NetConnection -ComputerName localhost -Port 6543
  ```
- Ver logs del contenedor:
  ```powershell
  docker logs -f tfg-postgres
  ```

## Docker (alternativa)
```powershell
docker build -t tfg-api .
docker run -p 8000:8000 --env-file .env --name tfg-api-dev tfg-api
Invoke-RestMethod http://127.0.0.1:8000/health
```
Reconstruir:
```powershell
docker rm -f tfg-api-dev
docker build -t tfg-api .
docker run -p 8000:8000 --env-file .env --name tfg-api-dev tfg-api
```

## Autenticación
JWT HS256 (`SECRET_KEY`). Expiración configurable: `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`.

## Seguridad y buenas prácticas
- Cambia `SECRET_KEY` en producción.
- Limita `allow_origins` en CORS a dominios reales.
- Usa HTTPS detrás de un reverse proxy.

## Licencia / Uso
Proyecto académico (TFG). Ajusta según políticas de tu institución.

---
Fin de la guía paso a paso.
# 4) Arranca de nuevo el servidor
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --log-level debug
```

Notas:
- FastAPI 0.110.x usa Pydantic v2 y depende de `pydantic-core` (binario). La reinstalación descarga el wheel correcto (`cp311-win_amd64` para Python 3.11 de 64-bit).
- Si venías de un error de certificados TLS con pip, primero aplica el fix de CA (ver sección anterior) y luego repite la reinstalación.

### Uvicorn se cierra al probar con Invoke-RestMethod

Ejecuta el servidor en una ventana de PowerShell y realiza pruebas en otra, para no interrumpir el proceso del servidor.

## Notas de desarrollo

- El seeding no pisa datos existentes; inserta únicamente si las tablas están vacías.
- Si cambias modelos y usas SQLite, puedes borrar `data.db` para recrear desde cero (o usar migraciones en el futuro).

---

Hecho con FastAPI + SQLModel. ¡Feliz hacking! 💈
# API Barbería 💈 (TFG) – Estructura Modular

Esta versión organiza la API en archivos separados por recurso (endpoint type) para facilitar mantenimiento y escalado.

## Estructura

```
app/
  main.py
  endpoints/
    __init__.py
    root.py
    health.py
    barbers.py
    barbershop.py
    services.py
    service_categories.py
    products.py
    product_categories.py
    gallery.py
    reviews.py
    availability.py
    bookings.py
  models/
    __init__.py
    barber.py
    barbershop.py
    service.py
    product.py
    category.py
    gallery.py
    review.py
    booking.py
    availability.py
  helpers/
    __init__.py
    db_memory.py
    scheduling.py
    ratings.py
Dockerfile
requirements.txt
.env
README.md
```

## Instalación y ejecución

Recomendado en Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Variables de entorno (opcional):

```powershell
echo "DATABASE_URL=sqlite:///./data.db" >> .env
```

Para PostgreSQL, instala el driver y exporta la URL:

```powershell
.\.venv\Scripts\python.exe -m pip install psycopg2-binary
echo "DATABASE_URL=postgresql+psycopg2://usuario:password@host:5432/dbname" >> .env
```

Docs: http://localhost:8000/docs

## Autenticación (JWT)

Contrato propuesto:

- POST `/auth/login` => `{ access_token, refresh_token, token_type: "bearer", expires_in }`
- POST `/auth/refresh` => `{ access_token, token_type, expires_in }`
- GET `/auth/me` (protegido) => datos básicos del usuario/claims

Variables `.env` relevantes:

```powershell
echo "SECRET_KEY=pon-una-clave-larga-y-aleatoria" >> .env
echo "ACCESS_TOKEN_EXPIRE_MINUTES=30" >> .env
echo "REFRESH_TOKEN_EXPIRE_DAYS=7" >> .env
```

Usuario demo para pruebas:

```json
{"username":"demo","password":"Demo#1234"}
```

## Solución de problemas

### Error de certificados en pip (Windows + PostgreSQL)

Si ves un error como:

```
ERROR: Could not find a suitable TLS CA certificate bundle, invalid path: C:\\Program Files\\PostgreSQL\\18\\ssl\\certs\\ca-bundle.crt
```

Es probable que el instalador de PostgreSQL haya creado la variable de entorno `CURL_CA_BUNDLE` apuntando a un fichero que no existe. Esto hace que `pip` y otras herramientas HTTPS fallen.

Solución rápida (solo para la sesión actual de PowerShell):

```powershell
[Environment]::SetEnvironmentVariable('CURL_CA_BUNDLE', $null, 'Process')
[Environment]::SetEnvironmentVariable('REQUESTS_CA_BUNDLE', $null, 'Process')
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Solución permanente (requiere PowerShell como Administrador):

```powershell
[Environment]::SetEnvironmentVariable('CURL_CA_BUNDLE', $null, 'Machine')
```

Después, abre una nueva ventana de PowerShell para que los cambios surtan efecto. Si trabajas detrás de un proxy corporativo y necesitas un CA personalizado, apunta `REQUESTS_CA_BUNDLE` a una ruta válida del bundle de certificados en lugar de eliminarlo.

## Endpoints

- Core: GET `/`, GET `/health`
- Auth: POST `/auth/register`, POST `/auth/login`, GET `/auth/me`, POST `/auth/refresh` (si está habilitado)
- Users: GET `/users/me`, PUT `/users/me`, POST `/users/me/photo`
- Barbers: GET `/barbers`, GET `/barbers/{id}`, GET `/barbers/by-service/{service_id}`, POST `/barbers`, PUT `/barbers/{id}`, DELETE `/barbers/{id}`
- Barbershop: GET `/barbershop`, POST `/barbershop`
- Services: GET `/services`, GET `/services/{id}`, GET `/services/by-category/{category_id}`, POST `/services`, PUT `/services/{id}`, DELETE `/services/{id}`
- Service categories: GET `/service-categories`, GET `/service-categories/{id}`, POST `/service-categories`, PUT `/service-categories/{id}`, DELETE `/service-categories/{id}`
- Products: GET `/products`, GET `/products/{id}`, GET `/products/by-category/{category_id}`, POST `/products`, PUT `/products/{id}`, DELETE `/products/{id}`
- Product categories: GET `/product-categories`, GET `/product-categories/{id}`, POST `/product-categories`, PUT `/product-categories/{id}`, DELETE `/product-categories/{id}`
- Gallery: GET `/gallery`, GET `/gallery/{id}`, POST `/gallery`, PUT `/gallery/{id}`, DELETE `/gallery/{id}`
- Reviews: GET `/reviews`, GET `/reviews/{id}`, POST `/reviews`, PUT `/reviews/{id}`, DELETE `/reviews/{id}`
- Availability: GET `/availability`, POST `/availability`
- Bookings: GET `/bookings`, POST `/bookings`, GET `/bookings/me`, GET `/bookings/{id}`

