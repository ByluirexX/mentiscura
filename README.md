# Mentis Cura - Sistema de Monitoreo Psicológico

## Descripción

Prototipo académico de un Sistema de Monitoreo Psicológico para el Sistema Educativo Militar. Implementa instrumentos estandarizados de tamizaje (PHQ-2 y PHQ-9) para la detección temprana de indicadores de riesgo en salud mental.

**IMPORTANTE**: Este sistema NO realiza diagnósticos clínicos. Es exclusivamente una herramienta de tamizaje y alertamiento que facilita la identificación de casos que requieren atención profesional.

## Características

- Registro de discentes con datos académicos (matrícula, carrera, compañía, año)
- Aplicación de cuestionarios PHQ-2 y PHQ-9
- Cálculo automático de puntajes y clasificación de riesgo
- Generación de alertas internas para personal autorizado
- Alerta automática de prioridad crítica en pregunta 9 (ideación suicida)
- Control de acceso basado en roles (Administrador, Orientador, Discente)
- Búsqueda de discentes por matrícula, nombre o compañía
- Historial y trazabilidad de evaluaciones
- Bitácora de auditoría para todos los accesos
- Hash seguro de contraseñas (PBKDF2-SHA256)
- Protección CSRF en formularios
- Interfaz responsive con Bootstrap 5

## Requisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- PostgreSQL (recomendado) 

## Instalación

### 1. Clonar o descargar el proyecto

```bash
cd psico_monitor
```

### 2. Crear entorno virtual (recomendado)

```bash
# En Linux/macOS
python3 -m venv venv
source venv/bin/activate

# En Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt

# Para PostgreSQL, instalar también:
pip install psycopg2-binary
```

### 4. Configurar base de datos

### PostgreSQL (Recomendado)

1. Crear base de datos en pgAdmin4 o por consola:
```sql
CREATE DATABASE psico_monitor;
CREATE USER psico_user WITH PASSWORD 'psico123';
GRANT ALL PRIVILEGES ON DATABASE psico_monitor TO psico_user;
```

2. La configuración ya está en `app/config.py`:
```python
SQLALCHEMY_DATABASE_URI = 'postgresql://psico_user:psico123@localhost:5432/psico_monitor'
```



### 5. Inicializar base de datos con datos de prueba

```bash
python seed_data.py
```

### 6. Ejecutar la aplicación

```bash
python run.py
```

La aplicación estará disponible en: **http://127.0.0.1:5000**

## Usuarios de Prueba

| Usuario    | Contraseña | Rol           | Nota                    |
|------------|------------|---------------|-------------------------|
| admin      | admin123   | Administrador |                         |
| orientador | orient123  | Orientador    |                         |
| psicologia | psico123   | Orientador    |                         |
| A20001     | disc123    | Discente      | Ingresar con matrícula  |
| B20002     | disc123    | Discente      | Ingresar con matrícula  |
| C20003     | disc123    | Discente      | Ingresar con matrícula  |
| D20004     | disc123    | Discente      | Ingresar con matrícula  |
| E20005     | disc123    | Discente      | Ingresar con matrícula  |

**Nota:** Los discentes inician sesión usando su **matrícula** como nombre de usuario.

## Registro de Discentes

Los discentes pueden auto-registrarse desde la pantalla de login. Campos requeridos:

- **Nombre** y **Apellidos** (paterno y materno)
- **Matrícula** (formato: letra + números, ej: A12345) - será su usuario
- **Edad** (16-50 años)
- **Año que cursa** (1° a 6° año)
- **Carrera**: Tronco Común, Ing. Computación, Ing. Industrial, Ing. Comunicaciones, Ing. Construcción
- **Compañía**: Primera Cía., Segunda Cía., Tercera Cía., Cuarta Cía., Cía. Oficiales
- **Contraseña** (mínimo 6 caracteres)

## Estructura del Proyecto(modelo-vista-controlador)

```
psico_monitor/
├── app/
│   ├── __init__.py              # Factory de la aplicación Flask
│   ├── config.py                 # Configuración (PostgreSQL/SQLite)
│   ├── models/                   # Modelos de datos (ORM)
│   │   ├── usuario.py            # Usuario y Rol (con datos académicos)
│   │   ├── cuestionario.py       # Cuestionario, Pregunta, Opción
│   │   ├── evaluacion.py         # Evaluación, Respuesta y PuntajeSustancia
│   │   ├── alerta.py             # Alertas del sistema
│   │   └── material.py           # Materiales de apoyo
│   ├── services/                 # Capa de lógica de negocio
│   │   ├── auth_service.py       # Autenticación
│   │   ├── evaluacion_service.py # Procesamiento de evaluaciones
│   │   ├── alerta_service.py     # Gestión de alertas
│   │   └── reporte_service.py    # Generación de reportes PDF
│   ├── routes/                   # Controladores (Blueprints)
│   │   ├── auth.py               # Login/Logout/Registro
│   │   ├── main.py               # Dashboard principal
│   │   ├── cuestionarios.py      # Aplicación de cuestionarios (PHQ-2, PHQ-9, ASSIST)
│   │   ├── evaluaciones.py       # Visualización de resultados
│   │   ├── alertas.py            # Gestión de alertas
│   │   ├── admin.py              # Administración
│   │   ├── reportes.py           # Generación de reportes
│   │   └── materiales.py         # Gestión de materiales de apoyo
│   ├── templates/                # Plantillas Jinja2
│   │   ├── auth/                 # Login, Registro, Registro Exitoso
│   │   ├── main/                 # Dashboards por rol
│   │   ├── cuestionarios/        # Formularios PHQ-2, PHQ-9 y ASSIST
│   │   ├── evaluaciones/         # Resultados e historial
│   │   ├── alertas/              # Gestión de alertas
│   │   ├── admin/                # Administración
│   │   ├── materiales/           # Materiales de apoyo
│   │   └── reportes/             # Reportes y PDF
│   └── utils/                    # Utilidades (decoradores)
├── requirements.txt              # Dependencias Python
├── run.py                        # Script de ejecución
├── seed_data.py                  # Datos iniciales
├── README.md                     # Este archivo
└── DOCUMENTO_TESIS.md            # Documentación para tesis
```

## Arquitectura

El sistema implementa una **arquitectura por capas**:

1. **Capa de Presentación** (Templates + Routes): Interfaz web con Jinja2 y Bootstrap
2. **Capa de Servicios** (Services): Lógica de negocio y reglas de evaluación
3. **Capa de Datos** (Models): ORM SQLAlchemy con modelos relacionales

## Reglas de Evaluación

### PHQ-2 (Puntaje 0-6)
- **< 3**: Sin indicador de riesgo
- **≥ 3**: Indicador positivo (sugiere aplicar PHQ-9)

### PHQ-9 (Puntaje 0-27)
| Puntaje | Nivel de Riesgo       |
|---------|----------------------|
| 0-4     | Mínimo o Ninguno     |
| 5-9     | Leve                 |
| 10-14   | Moderado             |
| 15-19   | Moderadamente Severo |
| 20-27   | Severo               |

### Alerta Automática P9
La pregunta 9 del PHQ-9 evalúa ideación suicida. Cualquier respuesta ≥ 1 genera automáticamente una **alerta de prioridad CRÍTICA**.

## Consideraciones de Seguridad

- Contraseñas almacenadas con hash PBKDF2-SHA256
- Protección CSRF en todos los formularios
- Control de acceso por roles en cada ruta
- Registro de auditoría para trazabilidad
- Sesiones con tiempo de expiración (2 horas)
- Cookies HttpOnly y SameSite

## Tecnologías Utilizadas

- **Backend**: Python 3, Flask 3.0
- **ORM**: SQLAlchemy 2.0
- **Base de Datos**: PostgreSQL (producción) / SQLite (desarrollo)
- **Frontend**: HTML5, Bootstrap 5.3, Bootstrap Icons
- **Seguridad**: Flask-Login, Flask-WTF, Werkzeug

## Licencia

Este proyecto es un prototipo académico desarrollado para fines de tesis. Uso exclusivo para demostración y evaluación académica.

---

**Nombre del Sistema**: Mentis Cura
**Versión**: 1.0.0
**Fecha**: 2026
