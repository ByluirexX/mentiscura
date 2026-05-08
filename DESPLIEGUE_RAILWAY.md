# Guía de Despliegue en Railway — Mentis Cura

## Resumen

Este documento describe todos los pasos, archivos y configuraciones necesarios para desplegar la aplicación Flask **Mentis Cura** en Railway con una base de datos PostgreSQL en la nube.

---

## 1. Archivos creados y modificados

### 1.1 `requirements.txt` — Dependencias actualizadas

Se agregaron `gunicorn` (servidor de producción), `psycopg2-binary` (driver de PostgreSQL) y se actualizó `SQLAlchemy` para compatibilidad con Python 3.13.

```
# Framework web
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-WTF==1.2.1

# Base de datos
SQLAlchemy==2.0.40

# Seguridad
Werkzeug==3.0.1
email-validator==2.1.0

# Utilidades
python-dotenv==1.0.0

# Exportacion de reportes a PDF
xhtml2pdf==0.2.11

# Servidor de produccion
gunicorn==21.2.0
psycopg2-binary==2.9.10
```

> **Por qué SQLAlchemy 2.0.40:** La versión original (2.0.23) no era compatible con Python 3.13 que usa Railway por defecto.
>
> **Por qué psycopg2-binary:** Es el driver que permite a SQLAlchemy conectarse a PostgreSQL. La versión `-binary` incluye todo lo necesario sin compilar desde cero.

---

### 1.2 `Procfile` — Comando de inicio para Railway

```
web: gunicorn run:app --bind 0.0.0.0:$PORT
```

> Railway lee este archivo para saber cómo arrancar la aplicación. `$PORT` es el puerto que Railway asigna dinámicamente.

---

### 1.3 `railway.json` — Configuración de despliegue

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "deploy": {
    "startCommand": "gunicorn run:app --bind 0.0.0.0:$PORT",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

> Define el comando de inicio y la política de reinicio en caso de error.

---

### 1.4 `railpack.json` — Dependencias del sistema

```json
{
  "$schema": "https://schema.railpack.com",
  "buildAptPackages": ["libfreetype6-dev", "libpq-dev", "gcc"],
  "aptPackages": ["libfreetype6", "libpq5"]
}
```

> `xhtml2pdf` requiere la librería FreeType para generar PDFs. Sin estos paquetes del sistema, el build falla.
>
> - `buildAptPackages`: paquetes instalados durante la compilación
> - `aptPackages`: paquetes disponibles en tiempo de ejecución

---

### 1.5 `run.py` — Adaptado para producción

Se modificó el bloque de inicio para usar el puerto dinámico de Railway:

```python
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0' if os.environ.get('PORT') else '127.0.0.1'
    app.run(
        host=host,
        port=port,
        debug=(env == 'development')
    )
```

> El host `0.0.0.0` permite conexiones externas (necesario en la nube). Localmente sigue usando `127.0.0.1`.

---

### 1.6 `app/config.py` — Corrección del formato de DATABASE_URL

Railway provee `DATABASE_URL` con el prefijo `postgres://`, pero SQLAlchemy 2.x requiere `postgresql://`. Se agregó una corrección automática:

```python
_db_url = os.environ.get('DATABASE_URL') or \
    'postgresql://psico_user:psico123@localhost:5432/psico_monitor'
SQLALCHEMY_DATABASE_URI = _db_url.replace('postgres://', 'postgresql://', 1)
```

---

### 1.7 `.gitignore` — Archivos excluidos del repositorio

```
# Entorno virtual
venv/

# Python
__pycache__/
*.pyc
*.pyo
*.pyd

# Variables de entorno (contiene claves secretas)
.env

# macOS
.DS_Store

# Archivos subidos por usuarios
uploads/materiales/*
!uploads/materiales/.gitkeep

# Base de datos local
data/
*.db
*.sqlite3

# IDEs
.vscode/
.idea/
```

---

### 1.8 `.env.example` — Referencia de variables de entorno

```
FLASK_ENV=production
SECRET_KEY=cambia-esto-por-una-clave-secreta-aleatoria
DATABASE_URL=postgresql://usuario:password@host:5432/nombre_db
```

> Este archivo es solo de referencia. El archivo real `.env` nunca se sube a GitHub.

---

## 2. Pasos de despliegue en Railway

### Paso 1 — Subir el código a GitHub

```bash
git init
git add .
git commit -m "Primer commit - Mentis Cura v1.0"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/mentiscura.git
git push -u origin main
```

---

### Paso 2 — Crear el proyecto en Railway

1. Ir a [railway.app](https://railway.app) e iniciar sesión
2. Clic en **New Project → Deploy from GitHub repo**
3. Seleccionar el repositorio `mentiscura`
4. Railway detecta el `Procfile` automáticamente y hace el primer deploy

---

### Paso 3 — Agregar PostgreSQL

1. En el proyecto Railway, clic en **+ New → Database → Add PostgreSQL**
2. Railway crea la base de datos y genera automáticamente las variables de conexión

---

### Paso 4 — Configurar variables de entorno

En el servicio Flask → pestaña **Variables**, agregar:

| Variable | Valor |
|---|---|
| `FLASK_ENV` | `production` |
| `SECRET_KEY` | clave secreta aleatoria larga |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |

> El valor `${{Postgres.DATABASE_URL}}` es una referencia dinámica que Railway resuelve automáticamente tomando el `DATABASE_URL` del plugin de PostgreSQL.

---

### Paso 5 — Poblar la base de datos (seed)

Una vez que el deploy está en verde, ejecutar el script de datos iniciales desde la terminal local:

```bash
cd /ruta/del/proyecto
source venv/bin/activate
DATABASE_URL="postgres://..." FLASK_ENV=production python seed_data.py
```

> Reemplazar `postgres://...` con el valor real del `DATABASE_URL` obtenido desde Railway → servicio PostgreSQL → Variables.

Este script crea:
- 3 roles: administrador, orientador, discente
- Usuarios de prueba: `admin/admin123`, `orientador/orient123`, `A20001/disc123`
- Cuestionarios PHQ-2, PHQ-9 y ASSIST con todas sus preguntas y opciones

---

### Paso 6 — Generar dominio público

En Railway → servicio Flask → **Settings → Networking → Generate Domain**

Railway asigna una URL pública con HTTPS, por ejemplo:
```
https://mentiscura-production.up.railway.app
```

---

## 3. Flujo para actualizar el proyecto

Cada vez que se hagan cambios en el código:

```bash
cd /ruta/del/proyecto
git add -A
git commit -m "descripción del cambio"
git push origin main
```

Railway detecta el push y despliega automáticamente en 1-2 minutos.

---

## 4. Problemas encontrados y soluciones

| Problema | Causa | Solución |
|---|---|---|
| `npm: command not found` | Railway confundía el proyecto con Node.js | Crear `railway.json` con comando de inicio explícito |
| `Build Failed: exit code 1` | `xhtml2pdf` necesita FreeType para compilar | Crear `railpack.json` con `libfreetype6-dev` |
| `AssertionError: TypingOnly` | SQLAlchemy 2.0.23 no compatible con Python 3.13 | Actualizar a SQLAlchemy 2.0.40 |
| `could not translate host name "host"` | `DATABASE_URL` tenía valor de ejemplo | Usar referencia `${{Postgres.DATABASE_URL}}` en Railway |
| `Connection refused localhost:5432` | Railway no inyecta `DATABASE_URL` automáticamente | Agregar `DATABASE_URL` como variable de referencia manualmente |
| `postgres://` vs `postgresql://` | Railway usa prefijo `postgres://` pero SQLAlchemy 2.x requiere `postgresql://` | Corrección en `config.py` con `.replace()` |
| `Worker exited with code 3` | Gunicorn no podía iniciar la app por errores anteriores | Se resolvió al corregir `DATABASE_URL` |
