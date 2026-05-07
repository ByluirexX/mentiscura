# MENTIS CURA — Guía Completa de Desarrollo del Sistema
## Desde la instalación del entorno hasta el producto final

---

> **Propósito de este documento**
> Este texto describe, paso a paso y con el mayor nivel de detalle posible, cómo se construyó el sistema de monitoreo psicológico Mentis Cura: qué se instaló primero, por qué se tomaron ciertas decisiones, en qué orden se crearon los archivos, qué hace cada uno de ellos y cómo se verificó que todo funcionara. Está escrito para que cualquier persona con conocimientos básicos de programación pueda seguirlo sin perderse.

---

## PARTE 1 — PREPARACIÓN DEL ENTORNO DE DESARROLLO

### 1.1 ¿Por qué se necesita un entorno virtual?

Antes de escribir una sola línea de código del sistema, es necesario preparar el entorno donde va a correr. En Python existe una herramienta llamada **entorno virtual** (virtual environment). Su función es crear un espacio aislado donde todas las bibliotecas del proyecto se instalan sin interferir con otras aplicaciones Python que puedan existir en la misma computadora.

Sin un entorno virtual, instalar Flask para este proyecto podría romper otro proyecto que use una versión diferente. Con él, cada proyecto vive en su propia burbuja.

### 1.2 Herramientas que deben instalarse antes de comenzar

Para trabajar con este proyecto se necesita lo siguiente en la computadora:

**Python 3.11 o superior**
Python es el lenguaje de programación del backend. Se puede descargar desde python.org o instalarse con el gestor de paquetes del sistema operativo. Para verificar que está instalado, se abre una terminal y se ejecuta:

```
python3 --version
```

Si responde con `Python 3.11.x` o superior, está listo.

**pip**
pip es el instalador de paquetes de Python. Normalmente viene incluido con Python. Se verifica con:

```
pip --version
```

**PostgreSQL 14 o superior**
PostgreSQL es el motor de base de datos relacional que usa el sistema. Almacena todos los datos: usuarios, cuestionarios, evaluaciones y alertas. En macOS se puede instalar con Homebrew:

```
brew install postgresql@14
brew services start postgresql@14
```

En Ubuntu/Debian:

```
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**psql (cliente de PostgreSQL)**
psql es la herramienta de línea de comandos para administrar bases de datos PostgreSQL. Viene incluida con la instalación de PostgreSQL.

**Un editor de código**
Visual Studio Code es una buena opción gratuita. PyCharm también funciona bien para proyectos Python/Flask.

### 1.3 Creación de la base de datos

Una vez instalado PostgreSQL, se debe crear la base de datos y el usuario que el sistema va a utilizar. Se abre una terminal y se conecta a PostgreSQL como superusuario:

```
psql -U postgres
```

Dentro de la consola de PostgreSQL se ejecutan los siguientes comandos:

```sql
CREATE DATABASE psico_monitor;
CREATE USER psico_user WITH PASSWORD 'psico123';
GRANT ALL PRIVILEGES ON DATABASE psico_monitor TO psico_user;
```

Esto crea una base de datos llamada `psico_monitor` y un usuario llamado `psico_user` con contraseña `psico123`. El sistema se conectará usando esas credenciales.

### 1.4 Creación del entorno virtual y del proyecto

Con la terminal posicionada en la carpeta donde se quiere crear el proyecto, se ejecuta:

```
mkdir psico_monitor
cd psico_monitor
python3 -m venv venv
```

Esto crea una carpeta llamada `psico_monitor` (el directorio raíz del proyecto) y dentro de ella una carpeta `venv` que contiene el entorno virtual. Ahora se activa el entorno virtual:

En macOS y Linux:
```
source venv/bin/activate
```

En Windows:
```
venv\Scripts\activate
```

Cuando el entorno virtual está activo, el nombre del entorno aparece entre paréntesis al inicio del prompt de la terminal: `(venv) $`. Todos los comandos de instalación que se ejecuten a partir de aquí afectan solo a este entorno, no al sistema global.

### 1.5 Instalación de las bibliotecas del proyecto

En Python, las dependencias de un proyecto se listan en un archivo llamado `requirements.txt`. Este archivo permite que cualquier persona que clone el repositorio instale exactamente las mismas versiones de todas las bibliotecas con un solo comando.

El archivo `requirements.txt` del proyecto tiene el siguiente contenido:

```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-WTF==1.2.1
SQLAlchemy==2.0.23
Werkzeug==3.0.1
email-validator==2.1.0
python-dotenv==1.0.0
xhtml2pdf==0.2.11
psycopg2-binary==2.9.9
```

A continuación se explica para qué sirve cada una:

| Biblioteca | Versión | Propósito |
|---|---|---|
| Flask | 3.0.0 | El microframework web. Maneja rutas, solicitudes HTTP y respuestas. |
| Flask-SQLAlchemy | 3.1.1 | Extensión que integra SQLAlchemy con Flask para manejo de base de datos. |
| Flask-Login | 0.6.3 | Gestión de sesiones de usuario: autenticación, cierre de sesión, protección de rutas. |
| Flask-WTF | 1.2.1 | Integra WTForms con Flask. Proporciona protección CSRF en formularios. |
| SQLAlchemy | 2.0.23 | El ORM (Object Relational Mapper) que convierte clases Python en tablas de BD. |
| Werkzeug | 3.0.1 | Librería de utilidades WSGI que usa Flask internamente. |
| email-validator | 2.1.0 | Valida el formato de direcciones de correo electrónico en formularios. |
| python-dotenv | 1.0.0 | Lee variables de entorno desde un archivo `.env` para configuración. |
| xhtml2pdf | 0.2.11 | Convierte HTML a PDF. Se usa para generar reportes descargables. |
| psycopg2-binary | 2.9.9 | Driver Python para conectarse a PostgreSQL. |

Para instalar todo de una vez:

```
pip install -r requirements.txt
```

---

## PARTE 2 — ESTRUCTURA DEL PROYECTO

Antes de empezar a escribir código, se definió la estructura de carpetas del proyecto. Esta estructura sigue el patrón **Application Factory** de Flask y una organización modular por funcionalidad.

```
psico_monitor/
│
├── venv/                          # Entorno virtual (nunca se sube al repositorio)
│
├── app/                           # Paquete principal de la aplicación
│   ├── __init__.py                # Fábrica de la aplicación Flask
│   ├── config.py                  # Configuración del sistema
│   │
│   ├── models/                    # Modelos de datos (tablas de BD)
│   │   ├── __init__.py
│   │   ├── usuario.py
│   │   ├── cuestionario.py
│   │   ├── evaluacion.py
│   │   ├── alerta.py
│   │   └── material.py
│   │
│   ├── routes/                    # Controladores (rutas/vistas)
│   │   ├── auth.py
│   │   ├── main.py
│   │   ├── admin.py
│   │   ├── cuestionarios.py
│   │   ├── evaluaciones.py
│   │   ├── alertas.py
│   │   ├── reportes.py
│   │   └── materiales.py
│   │
│   ├── services/                  # Lógica de negocio
│   │   ├── auth_service.py
│   │   ├── evaluacion_service.py
│   │   └── alerta_service.py
│   │
│   ├── templates/                 # Plantillas HTML (Jinja2)
│   │   ├── base.html
│   │   ├── auth/
│   │   ├── main/
│   │   ├── admin/
│   │   ├── cuestionarios/
│   │   ├── evaluaciones/
│   │   ├── alertas/
│   │   ├── reportes/
│   │   └── materiales/
│   │
│   └── utils/                     # Utilidades compartidas
│       └── decorators.py
│
├── uploads/                       # Archivos subidos (materiales de apoyo)
├── requirements.txt               # Dependencias del proyecto
├── run.py                         # Punto de entrada para ejecutar el servidor
└── seed_data.py                   # Script para poblar la BD con datos iniciales
```

Esta organización permite que cada parte del sistema esté separada según su responsabilidad. Los modelos saben cómo se almacenan los datos, los servicios saben cómo procesarlos, y las rutas saben cómo responder a las peticiones del navegador.

---

## PARTE 3 — ORDEN DE CREACIÓN DE LOS ARCHIVOS

Los archivos se crearon en un orden específico que respeta las dependencias entre ellos: no se puede crear una ruta que use un modelo si el modelo aún no existe, y no se puede crear un modelo si la base de datos aún no está configurada.

### Fase 1: Configuración base del sistema

#### 3.1 Archivo: `app/config.py`

Este fue el primero en crearse porque todo lo demás depende de saber cómo está configurado el sistema. Define variables como la cadena de conexión a la base de datos, la clave secreta para las sesiones y parámetros específicos del negocio.

```python
from datetime import timedelta
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-mentis-cura-2024')
    SQLALCHEMY_DATABASE_URI = 'postgresql://psico_user:psico123@localhost:5432/psico_monitor'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Sesión dura 2 horas
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Umbrales de los cuestionarios
    PHQ2_UMBRAL_RIESGO = 3
    PHQ9_PREGUNTA_CRITICA = 9
    
    # Sustancias para el cuestionario ASSIST
    ASSIST_SUSTANCIAS = [
        'tabaco', 'alcohol', 'cannabis', 'cocaina',
        'anfetaminas', 'inhalantes', 'tranquilizantes',
        'alucinogenos', 'opiaceos'
    ]
    
    # Carpeta donde se guardan los materiales subidos
    MATERIALES_UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                             '..', 'uploads', 'materiales')
```

Se definen tres clases de configuración: `DevelopmentConfig` (con `DEBUG=True`), `TestingConfig` (con base de datos en memoria) y `ProductionConfig` (con configuraciones de seguridad más estrictas). Un diccionario mapea el nombre del entorno a la clase correspondiente.

La razón de usar clases de configuración en lugar de variables sueltas es que permite cambiar fácilmente entre entornos (desarrollo, pruebas, producción) sin modificar el código.

#### 3.2 Archivo: `app/__init__.py` — La fábrica de la aplicación

Este es el archivo más importante del proyecto. Implementa el patrón **Application Factory**, que consiste en crear la aplicación Flask dentro de una función en lugar de hacerlo directamente al nivel del módulo.

¿Por qué usar este patrón? Porque permite crear múltiples instancias de la aplicación con diferentes configuraciones (por ejemplo, una para pruebas y otra para producción) sin que interfieran entre sí.

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# Se crean las extensiones sin inicializar (sin app todavía)
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app(config_name='development'):
    app = Flask(__name__)
    
    # Cargar configuración
    from app.config import config
    app.config.from_object(config[config_name])
    
    # Inicializar extensiones con la app
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Configurar Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Debe iniciar sesión para acceder a esta página.'
    login_manager.login_message_category = 'warning'
    
    # Función que Flask-Login usa para cargar un usuario desde la sesión
    from app.models.usuario import Usuario
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))
    
    # Registrar blueprints (módulos de rutas)
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.admin import admin_bp
    from app.routes.cuestionarios import cuestionarios_bp
    from app.routes.evaluaciones import evaluaciones_bp
    from app.routes.alertas import alertas_bp
    from app.routes.reportes import reportes_bp
    from app.routes.materiales import materiales_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(cuestionarios_bp, url_prefix='/cuestionarios')
    app.register_blueprint(evaluaciones_bp, url_prefix='/evaluaciones')
    app.register_blueprint(alertas_bp, url_prefix='/alertas')
    app.register_blueprint(reportes_bp, url_prefix='/reportes')
    app.register_blueprint(materiales_bp, url_prefix='/materiales')
    
    return app
```

El patrón que sigue es: primero se crean las extensiones (db, login_manager, csrf) a nivel de módulo sin asociarlas a ninguna aplicación. Luego, dentro de `create_app()`, se asocian con `init_app()`. Esto es lo que permite el uso de múltiples configuraciones.

#### 3.3 Archivo: `run.py` — El punto de entrada

Este archivo es el que se ejecuta para arrancar el servidor. Es muy corto pero es el primero que se llama desde la terminal.

```python
from app import create_app

app = create_app('development')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
```

Importa la función `create_app`, crea una instancia de la aplicación en modo desarrollo y la ejecuta en el puerto 5000 de localhost. `debug=True` hace que el servidor se reinicie automáticamente cuando se modifica un archivo, lo cual es muy útil durante el desarrollo.

---

### Fase 2: Creación de los modelos de datos

Los modelos son clases Python que SQLAlchemy convierte automáticamente en tablas de la base de datos. Cada atributo de la clase corresponde a una columna en la tabla.

#### 3.4 Archivo: `app/models/usuario.py`

Este fue el primer modelo en crearse porque es el núcleo del sistema de autenticación y control de acceso. Sin usuarios no puede haber sesiones, y sin sesiones el sistema no puede saber quién está usando el sistema.

El archivo define dos clases: `Rol` y `Usuario`.

**La clase `Rol`** representa los tres roles del sistema: `administrador`, `orientador` y `discente`. Cada rol define qué puede hacer el usuario. La tabla en la base de datos se llama `roles`.

```python
class Rol(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Un rol tiene muchos usuarios
    usuarios = db.relationship('Usuario', backref='rol', lazy='dynamic')
```

**La clase `Usuario`** hereda de dos clases: `UserMixin` (que viene de Flask-Login y agrega los métodos que Flask-Login necesita como `is_authenticated`, `is_active`, `get_id`) y `db.Model` (que viene de SQLAlchemy y le da capacidades de base de datos). La tabla se llama `usuarios`.

Los campos del usuario incluyen:
- Datos de acceso: `username`, `password_hash`
- Datos personales: `nombre`, `apellido_paterno`, `apellido_materno`
- Datos académicos (solo discentes): `matricula`, `edad`, `anio_cursa`, `carrera`, `compania`
- Estado: `rol_id` (referencia al rol), `activo` (permite desactivar sin borrar)
- Auditoría: `created_at`, `updated_at`, `ultimo_acceso`

Los métodos de verificación de rol (`es_administrador()`, `es_orientador()`, `es_discente()`, `puede_ver_alertas()`) simplemente comparan `self.rol.nombre` con el nombre esperado. Esto hace que el código de las rutas sea muy legible:

```python
if current_user.es_administrador():
    # mostrar panel de administración
```

Importante: en este prototipo académico, las contraseñas se almacenan en texto plano por simplicidad. En un sistema de producción real se usaría `werkzeug.security.generate_password_hash` y `check_password_hash`.

#### 3.5 Archivo: `app/models/cuestionario.py`

Define la estructura de los cuestionarios psicológicos. Se necesitaron tres clases para modelar correctamente un cuestionario: la cabecera del cuestionario, sus preguntas y las opciones de respuesta de cada pregunta.

**Clase `Cuestionario`** — La tabla `cuestionarios`. Almacena el nombre, código (`PHQ-2`, `PHQ-9`, `ASSIST`, `IDERE-E`, etc.), descripción, instrucciones, puntaje máximo y si está activo. El campo `activo` es importante: en lugar de borrar cuestionarios, se desactivan.

```python
class Cuestionario(db.Model):
    __tablename__ = 'cuestionarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.Text)
    instrucciones = db.Column(db.Text)
    puntaje_maximo = db.Column(db.Integer)
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    preguntas = db.relationship('Pregunta', backref='cuestionario', lazy='dynamic',
                                 order_by='Pregunta.numero_orden')
    
    def obtener_preguntas_ordenadas(self):
        return self.preguntas.order_by(Pregunta.numero_orden).all()
```

**Clase `Pregunta`** — La tabla `preguntas`. Cada pregunta pertenece a un cuestionario (`cuestionario_id`). Los campos especiales son:
- `es_item_inverso`: indica si la puntuación de este ítem se invierte (para cuestionarios como IDERE/IDARE donde algunos ítems van en sentido contrario)
- `sustancia`: campo usado solo por el cuestionario ASSIST para asociar cada pregunta a una sustancia específica (tabaco, alcohol, etc.)
- `grupo_pregunta`: también para ASSIST, indica a qué sección pertenece la pregunta (`Q1`, `Q2`, ... `Q8`)
- `numero_orden`: determina el orden de presentación

**Clase `OpcionRespuesta`** — La tabla `opciones_respuesta`. Cada opción tiene un texto visible para el usuario y un valor numérico que se suma al puntaje total. Por ejemplo, para el PHQ-9:
- "Para nada" → valor 0
- "Varios días" → valor 1
- "Más de la mitad de los días" → valor 2
- "Casi todos los días" → valor 3

Para los cuestionarios IDERE/IDARE con ítems inversos, la estrategia fue pre-calcular los valores en la base de datos. Si un ítem inverso tiene escala 1-4 donde "Casi nunca" normalmente valdría 1, en la base de datos se almacena como 4 (el valor invertido). Así el servicio de evaluación simplemente suma todos los valores sin necesitar lógica de inversión.

#### 3.6 Archivo: `app/models/evaluacion.py`

Define cómo se almacenan los resultados cuando un usuario completa un cuestionario.

**Clase `Evaluacion`** — La tabla `evaluaciones`. Representa un intento completo de un usuario en un cuestionario. Campos importantes:
- `usuario_id`: quién la realizó
- `cuestionario_id`: qué cuestionario respondió
- `puntaje_total`: la suma de todas las respuestas
- `nivel_riesgo`: la clasificación textual ('minimo', 'leve', 'moderado', 'alto', etc.)
- `alerta_critica`: booleano que indica si se activó una condición crítica
- `fecha_evaluacion`: cuándo se realizó

Los métodos `color_riesgo()` y `etiqueta_riesgo()` convierten el nivel de riesgo en colores Bootstrap y etiquetas legibles para la interfaz:

```python
def color_riesgo(self):
    colores = {
        'minimo': 'success',
        'leve': 'info',
        'moderado': 'warning',
        'moderado_severo': 'orange',
        'severo': 'danger',
        'bajo': 'success',
        'alto': 'danger',
    }
    return colores.get(self.nivel_riesgo, 'secondary')
```

**Clase `Respuesta`** — La tabla `respuestas`. Almacena la respuesta individual a cada pregunta dentro de una evaluación: qué evaluación es, qué pregunta, qué opción se seleccionó y cuál fue el valor numérico de esa opción. Se configuró con `cascade='all, delete-orphan'` para que si se elimina una evaluación, sus respuestas también se eliminen.

**Clase `PuntajeSustancia`** — La tabla `puntajes_sustancia`. Es una tabla especializada solo para el cuestionario ASSIST, que requiere calcular un puntaje separado para cada sustancia (tabaco, alcohol, cannabis, etc.). Almacena el `nombre_sustancia` y su `puntaje` dentro de una evaluación.

#### 3.7 Archivo: `app/models/alerta.py`

Define el modelo de alertas de riesgo que el sistema genera automáticamente cuando un usuario obtiene un resultado preocupante en un cuestionario.

**Clase `Alerta`** — La tabla `alertas`. Campos principales:
- `usuario_id`: el discente que generó la alerta
- `evaluacion_id`: la evaluación que la originó
- `tipo`: qué tipo de alerta es (ej: `'PHQ-9 Severo'`, `'Ideación suicida'`)
- `prioridad`: `'baja'`, `'media'`, `'alta'` o `'critica'`
- `estado`: `'pendiente'`, `'en_revision'` o `'atendida'`
- `mensaje`: descripción detallada de la alerta
- `atendida_por_id`: referencia al orientador que la atendió
- `fecha_atencion`: cuándo fue atendida
- `notas_atencion`: observaciones del orientador

Los métodos `marcar_en_revision()` y `marcar_atendida()` actualizan el estado y registran quién y cuándo realizó la acción.

#### 3.8 Archivo: `app/models/material.py`

Define el modelo para los materiales de apoyo psicológico (documentos PDF e imágenes) que los orientadores pueden subir para que los discentes consulten.

**Clase `Material`** — La tabla `materiales`. Campos:
- `titulo`: nombre descriptivo del material
- `descripcion`: explicación opcional
- `tipo_archivo`: `'pdf'` o `'imagen'`
- `nombre_archivo`: nombre único generado con UUID para evitar colisiones en disco
- `nombre_original`: nombre con el que el usuario subió el archivo
- `subido_por_id`: referencia al orientador que lo subió

La constante `EXTENSIONES_PERMITIDAS = {'pdf', 'jpg', 'jpeg', 'png', 'gif', 'webp'}` define qué tipos de archivo se aceptan. El método `tipo_desde_extension()` clasifica la extensión en 'pdf' o 'imagen'.

#### 3.9 Archivo: `app/models/__init__.py`

Un archivo de inicialización simple que importa todos los modelos. Esto permite importarlos fácilmente desde otras partes del código con `from app.models import Usuario, Cuestionario` en lugar de especificar el submódulo exacto.

---

### Fase 3: Creación de los servicios (lógica de negocio)

Los servicios contienen la lógica de negocio del sistema. Son clases Python normales (sin relación con Flask ni con HTTP) que saben cómo procesar datos, calcular resultados y coordinar operaciones entre modelos. La razón de separarlos de las rutas es que así el mismo cálculo puede ser llamado desde múltiples puntos sin duplicar código.

#### 3.10 Archivo: `app/services/auth_service.py`

Contiene la clase `AuthService` con el método `autenticar()`, que es el único responsable de verificar si un usuario puede entrar al sistema.

El proceso de autenticación sigue tres pasos en secuencia:

1. **¿Existe el usuario?** Se busca por username en la base de datos. Si no existe, se retorna un error genérico (no se dice "el usuario no existe" para no dar pistas a atacantes).
2. **¿Está activo?** Si la cuenta fue desactivada por un administrador, se rechaza el acceso.
3. **¿Es correcta la contraseña?** Se llama a `check_password()` del modelo.

Si las tres verificaciones pasan, se actualiza el campo `ultimo_acceso` con la fecha y hora actuales y se hace commit a la base de datos. Esto registra cuándo fue el último inicio de sesión del usuario.

El servicio retorna la instancia del usuario si todo va bien, o `(None, mensaje_de_error)` si algo falla.

#### 3.11 Archivo: `app/services/alerta_service.py`

Es el servicio más complejo después de `evaluacion_service.py`. Su responsabilidad es determinar si una evaluación recién procesada debe generar alguna alerta de riesgo, y si es así, crearla.

La función principal es `evaluar_y_generar_alertas(evaluacion)`. Recibe una evaluación ya guardada en la base de datos y decide si generar alertas.

Para el PHQ-9, existen dos condiciones que generan alertas:
1. Si el nivel de riesgo es "moderado", "moderado_severo" o "severo" → se genera una alerta de prioridad "media", "alta" o "crítica" respectivamente.
2. Si la respuesta a la pregunta 9 (sobre ideación suicida) es mayor a 0 → se genera automáticamente una alerta de prioridad "crítica", independientemente del puntaje total.

El diccionario `PRIORIDAD_POR_RIESGO` mapea cada nivel al tipo de alerta:

```python
PRIORIDAD_POR_RIESGO = {
    'leve': 'baja',
    'moderado': 'media',
    'moderado_severo': 'alta',
    'severo': 'critica',
    'alto': 'alta',
}
```

Para el ASSIST, hay una función separada `_evaluar_alertas_assist()` que analiza los puntajes por sustancia y genera alertas cuando alguna sustancia supera el umbral de riesgo.

El método `obtener_alertas_pendientes(filtros)` usa SQLAlchemy con ordenamiento personalizado para mostrar las alertas más críticas primero usando `db.case()`:

```python
orden_prioridad = db.case(
    {'critica': 1, 'alta': 2, 'media': 3, 'baja': 4},
    value=Alerta.prioridad
)
query = query.order_by(orden_prioridad, Alerta.created_at.desc())
```

#### 3.12 Archivo: `app/services/evaluacion_service.py`

Este es el servicio más importante del sistema. Es quien "sabe" cómo procesar una evaluación de principio a fin.

La función principal es `procesar_evaluacion(usuario_id, cuestionario_id, respuestas_dict)`. Recibe el ID del usuario, el ID del cuestionario y un diccionario que mapea `{pregunta_id: valor_numerico}`. Realiza las siguientes operaciones en una transacción atómica:

1. **Calcula el puntaje total**: suma todos los valores del diccionario de respuestas.
2. **Para ASSIST**: calcula puntajes por sustancia mediante `_calcular_puntajes_assist()`, que agrupa las respuestas por sustancia y suma solo las preguntas Q2-Q7 para cada una.
3. **Clasifica el riesgo**: llama a `_clasificar_riesgo(codigo, puntaje)` que determina el nivel según rangos predefinidos.
4. **Detecta alertas críticas**: para PHQ-9, verifica si la pregunta 9 tiene una respuesta mayor a 0.
5. **Guarda la evaluación**: crea el registro en la tabla `evaluaciones`.
6. **Guarda las respuestas**: crea un registro en `respuestas` por cada pregunta.
7. **Genera alertas**: llama a `AlertaService.evaluar_y_generar_alertas()`.
8. **Hace commit**: confirma todo en la base de datos.

Si cualquier paso falla, se hace rollback y se lanza una excepción.

Las constantes de clasificación definen los rangos de puntaje para cada instrumento:

```python
# PHQ-9 (0-27)
CLASIFICACION_PHQ9 = {
    'minimo': (0, 4),
    'leve': (5, 9),
    'moderado': (10, 14),
    'moderado_severo': (15, 19),
    'severo': (20, 27)
}

# IDERE Estado y Rasgo (20-80)
CLASIFICACION_IDERE = {
    'bajo': (20, 24),
    'moderado': (25, 36),
    'alto': (37, 80),
}

# IDARE Estado y Rasgo (20-80)
CLASIFICACION_IDARE = {
    'bajo': (20, 30),
    'moderado': (31, 44),
    'alto': (45, 80),
}

# ADNM-8 (8-32)
CLASIFICACION_ADNM8 = {
    'bajo': (8, 19),
    'alto': (20, 32),
}

# ADNM-20 (20-80)
CLASIFICACION_ADNM20 = {
    'bajo': (20, 46),
    'alto': (47, 80),
}
```

El método `_clasificar_riesgo()` recibe el código del cuestionario y el puntaje, y determina qué tabla de clasificación usar con una cadena de `if/elif`:

```python
def _clasificar_riesgo(codigo, puntaje):
    if codigo == 'PHQ-9':
        tabla = EvaluacionService.CLASIFICACION_PHQ9
    elif codigo == 'PHQ-2':
        return 'riesgo' if puntaje >= 3 else 'sin_riesgo'
    elif codigo in ('IDERE-E', 'IDERE-R'):
        tabla = EvaluacionService.CLASIFICACION_IDERE
    elif codigo in ('IDARE-E', 'IDARE-R'):
        tabla = EvaluacionService.CLASIFICACION_IDARE
    elif codigo == 'ADNM-8':
        tabla = EvaluacionService.CLASIFICACION_ADNM8
    elif codigo == 'ADNM-20':
        tabla = EvaluacionService.CLASIFICACION_ADNM20
    # ... continúa con ASSIST
```

---

### Fase 4: Creación de los decoradores de control de acceso

#### 3.13 Archivo: `app/utils/decorators.py`

Antes de crear las rutas, se implementaron los decoradores de control de acceso. Un decorador en Python es una función que envuelve a otra función para añadirle comportamiento.

```python
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def rol_requerido(*roles):
    """Decorador que verifica que el usuario tenga uno de los roles especificados."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.rol.nombre in roles:
                flash('No tiene permisos para acceder a esta sección.', 'danger')
                return redirect(url_for('main.inicio'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Shortcuts para los roles más comunes
solo_orientador = rol_requerido('orientador', 'administrador')
solo_admin = rol_requerido('administrador')
```

`@wraps(f)` es importante porque preserva el nombre y la documentación de la función original. Sin él, todos los endpoints protegidos tendrían el mismo nombre (`decorated_function`), lo que causaría conflictos en Flask.

El uso en las rutas es muy limpio:

```python
@alertas_bp.route('/')
@login_required          # Flask-Login: el usuario debe estar autenticado
@solo_orientador         # Nuestro decorador: debe ser orientador o admin
def listado():
    ...
```

---

### Fase 5: Creación de las rutas (controladores)

Las rutas son las que conectan las URLs del navegador con el código Python. Se organizaron en "Blueprints" (planos), que son como mini-aplicaciones Flask que se registran en la aplicación principal.

#### 3.14 Archivo: `app/routes/auth.py` — Autenticación

Contiene las rutas de autenticación del sistema. Blueprint registrado con prefijo `/auth`.

**`/auth/login` (GET y POST)**

La ruta GET simplemente muestra el formulario de inicio de sesión. La ruta POST procesa las credenciales:

1. Toma `username` y `password` del formulario enviado.
2. Llama a `AuthService.autenticar(username, password)`.
3. Si la autenticación falla, muestra un mensaje de error y vuelve al formulario.
4. Si tiene éxito, llama a `login_user(usuario, remember=False)` de Flask-Login y marca la sesión como permanente (para que dure las 2 horas configuradas).
5. Redirige al inicio.

**`/auth/logout`**

Simplemente llama a `logout_user()` de Flask-Login (que limpia la sesión) y redirige al login.

**`/auth/registro` (GET y POST)**

Permite a nuevos discentes crear su cuenta. La validación del username usa una expresión regular `r'^[A-Z]\d+'` que valida el formato de matrícula: una letra mayúscula seguida de uno o más dígitos (ej: `A12345`). Si el username ya existe, muestra un error. Si todo está bien, crea el usuario con rol `discente`.

#### 3.15 Archivo: `app/routes/main.py` — Página principal

**`/` (index)**

Redirige a `/inicio` si el usuario está autenticado, o al login si no lo está.

**`/inicio`**

Es el dashboard principal. La misma URL muestra contenido diferente según el rol del usuario:
- **Discente**: ve sus últimas evaluaciones y el botón para hacer cuestionarios.
- **Orientador/Admin**: ve estadísticas globales: total de alertas pendientes, alertas críticas, evaluaciones del día y número de discentes registrados.

Esta lógica diferenciada se maneja con `if current_user.es_discente()` en la ruta, y los datos correspondientes se pasan a la plantilla.

#### 3.16 Archivo: `app/routes/admin.py` — Administración de usuarios

Contiene las rutas para gestionar usuarios. Solo accesible por administradores (`@solo_admin`). Blueprint registrado con prefijo `/admin`.

**`/admin/` (index)** — Panel con estadísticas: total de usuarios por rol, usuarios activos, últimas evaluaciones.

**`/admin/usuarios`** — Lista todos los usuarios del sistema.

**`/admin/usuarios/nuevo`** — Formulario para crear un nuevo usuario (de cualquier rol).

**`/admin/usuarios/<id>/editar`** — Formulario para modificar datos de un usuario existente. Permite cambiar nombre, rol, estado activo, etc.

**`/admin/usuarios/<id>/eliminar`** — Implementa el patrón de **borrado suave** (soft delete): en lugar de eliminar el registro de la base de datos, simplemente pone `usuario.activo = False`. Esto preserva el historial de evaluaciones y alertas del usuario, que siguen siendo visibles para fines de auditoría.

#### 3.17 Archivo: `app/routes/cuestionarios.py` — Presentación de cuestionarios

Este archivo maneja el flujo completo de responder un cuestionario. Blueprint registrado con prefijo `/cuestionarios`.

**`/cuestionarios/`** — Muestra la lista de todos los cuestionarios activos.

**`/cuestionarios/<codigo>`** — Muestra el formulario de respuesta de un cuestionario específico. Para el ASSIST (que tiene una estructura especial con preguntas por sustancia y grupos Q1-Q8), usa un template diferente (`responder_assist.html`) con lógica adicional para agrupar las preguntas por sustancia.

**`/cuestionarios/<codigo>/enviar` (POST)** — El endpoint que procesa el formulario enviado. El proceso es:

1. Valida que el cuestionario exista y esté activo.
2. Recoge todas las respuestas del formulario. Para ASSIST, la lógica es especial: primero determina qué sustancias fueron "usadas" (respuesta > 0 en Q1), y luego solo requiere respuestas para esas sustancias en Q2-Q7.
3. Valida que todas las preguntas obligatorias tengan respuesta.
4. Llama a `EvaluacionService.procesar_evaluacion()`.
5. Redirige a la página de resultado.

#### 3.18 Archivo: `app/routes/evaluaciones.py` — Visualización de resultados

**`/evaluaciones/resultado/<id>`** — Muestra el resultado detallado de una evaluación. Verificación de acceso: el usuario solo puede ver sus propias evaluaciones; orientadores y admins pueden ver cualquiera. Para ASSIST usa un template específico (`resultado_assist.html`) que muestra los puntajes por sustancia.

**`/evaluaciones/historial`** — Historial de evaluaciones del usuario actual. Llama a `EvaluacionService.obtener_historial_usuario()` y `obtener_estadisticas_usuario()`.

**`/evaluaciones/usuario/<id>`** — Historial de un discente específico. Solo para orientadores y admins. Muestra los mismos datos pero del discente indicado.

#### 3.19 Archivo: `app/routes/alertas.py` — Gestión de alertas

Todas las rutas de este módulo requieren rol de orientador o administrador.

**`/alertas/`** — Lista de alertas con filtros. Los parámetros de URL `estado` y `prioridad` permiten filtrar. Por defecto muestra alertas pendientes ordenadas por prioridad descendente.

**`/alertas/<id>`** — Detalle de una alerta: información del discente, tipo y prioridad, mensaje, estado.

**`/alertas/<id>/atender` (POST)** — Marca una alerta como atendida. Recibe las `notas` del formulario y llama a `AlertaService.marcar_alerta_atendida()`.

**`/alertas/<id>/en-revision` (POST)** — Marca una alerta como "en revisión". Indica que un orientador ya está trabajando en el caso.

**`/alertas/discentes`** — Lista todos los discentes del sistema para que el orientador pueda buscar uno específico y acceder a su historial.

#### 3.20 Archivo: `app/routes/reportes.py` — Generación de PDF

Solo accesible para orientadores y administradores.

**`/reportes/`** — Vista con filtros para seleccionar qué incluir en el reporte.

**`/reportes/pdf`** — Genera el reporte en formato PDF usando `xhtml2pdf`. El proceso:
1. Renderiza un template HTML específico para el reporte con los datos seleccionados.
2. Pasa el HTML a `xhtml2pdf` que lo convierte a bytes PDF.
3. Retorna la respuesta HTTP con `content_type='application/pdf'` y el nombre de archivo en el header, lo que hace que el navegador descargue el archivo.

#### 3.21 Archivo: `app/routes/materiales.py` — Materiales de apoyo

**`/materiales/`** — Lista todos los materiales disponibles. Accesible para todos los usuarios autenticados.

**`/materiales/subir` (GET/POST)** — Formulario para subir un nuevo material. Solo orientadores y admins. El proceso de subida:
1. Valida el título y que se haya seleccionado un archivo.
2. Verifica que la extensión sea permitida.
3. Genera un nombre único con UUID para evitar colisiones en disco.
4. Guarda el archivo físicamente en la carpeta `uploads/materiales/`.
5. Crea el registro en la base de datos.

**`/materiales/<id>/archivo`** — Sirve el archivo al usuario. Usa `send_from_directory()` de Flask para enviar el archivo de forma segura.

**`/materiales/<id>/eliminar` (POST)** — Elimina el archivo del disco y el registro de la base de datos.

---

### Fase 6: Creación de las plantillas HTML

Las plantillas (templates) son archivos HTML que Jinja2 procesa para insertar datos dinámicos. Siguen un patrón de herencia: existe un template base que define la estructura general, y los demás templates heredan de él.

#### 3.22 Archivo: `app/templates/base.html`

Es la plantilla madre del sistema. Todos los demás templates la extienden con `{% extends 'base.html' %}`. Define:

- La estructura HTML completa (`<head>`, `<body>`)
- Las importaciones de Bootstrap 5 CSS y JavaScript
- Las importaciones de Bootstrap Icons
- Las variables CSS de diseño (`--color-primary`, `--color-bg`, etc.)
- El navbar superior con los enlaces de navegación según el rol del usuario
- El área principal donde cada template hijo inserta su contenido (`{% block content %}`)
- El footer
- Los bloques para CSS y JS adicionales por template (`{% block extra_css %}`, `{% block extra_js %}`)

El diseño sigue una estética profesional y minimalista: fondo `#f9fafb` (gris muy claro), superficies blancas, bordes `#d1d5db` en lugar de sombras, tipografía del sistema operativo.

En el navbar, la visibilidad de los enlaces se controla con las mismas condiciones del backend:

```html
{% if current_user.puede_ver_alertas() %}
<li class="nav-item">
    <a class="nav-link" href="{{ url_for('alertas.listado') }}">Alertas</a>
</li>
{% endif %}
{% if current_user.es_administrador() %}
<li class="nav-item">
    <a class="nav-link" href="{{ url_for('admin.index') }}">Administración</a>
</li>
{% endif %}
```

#### 3.23 Archivo: `app/templates/auth/login.html`

Es el único template que **no extiende** `base.html`, porque la página de login es completamente independiente (el usuario aún no está autenticado, así que no hay navbar). Define su propio layout centrado en la pantalla.

Incluye: formulario de usuario y contraseña, manejo de mensajes flash de error, token CSRF (`{{ csrf_token() }}`), y enlace al registro de nuevos discentes.

#### 3.24 Archivo: `app/templates/evaluaciones/resultado.html`

Es uno de los templates más complejos. Extiende `base.html` y usa lógica Jinja2 para mostrar el resultado de la evaluación de forma diferente según el tipo de cuestionario.

Para cada instrumento psicométrico, el template tiene un bloque `{% elif evaluacion.cuestionario.codigo == 'NOMBRE' %}` que muestra:
- El puntaje obtenido vs. el puntaje máximo
- El nivel de riesgo con su color correspondiente
- Una interpretación textual del resultado
- Una escala de referencia que muestra todos los rangos posibles
- Si hay alerta crítica, un panel de advertencia destacado

---

### Fase 7: El script de datos iniciales

#### 3.25 Archivo: `seed_data.py`

Este script es fundamental para el proyecto. Crea toda la estructura inicial de datos que el sistema necesita para funcionar: roles, usuarios de prueba y todos los cuestionarios con sus preguntas y opciones.

El script se ejecuta una sola vez (o cuando se quiere reinicializar la base de datos):

```
python seed_data.py
```

La función `main()` coordina toda la ejecución:

```python
def main():
    with app.app_context():
        # Eliminar y recrear todas las tablas
        db.drop_all()
        db.create_all()
        
        # Crear roles
        roles = crear_roles()
        
        # Crear usuarios de prueba
        crear_usuarios(roles)
        
        # Crear cuestionarios
        crear_cuestionario_phq2()
        crear_cuestionario_phq9()
        crear_cuestionario_assist()
        crear_cuestionario_idere_e()
        crear_cuestionario_idere_r()
        crear_cuestionario_idare_e()
        crear_cuestionario_idare_r()
        crear_cuestionario_adnm8()
        crear_cuestionario_adnm20()
        
        db.session.commit()
        print("Base de datos inicializada correctamente.")
```

`db.drop_all()` elimina todas las tablas existentes. `db.create_all()` las recrea según las definiciones de los modelos. Esto garantiza una base de datos limpia en cada ejecución.

**Creación de roles y usuarios de prueba:**

Se crean tres roles: `administrador`, `orientador` y `discente`. Luego se crean usuarios de prueba para cada rol:
- `admin` / `admin123` — Administrador del sistema
- `orientador1` / `orient123` — Orientador/psicólogo
- `A2024001` / `discente123` — Discente de prueba

**Creación de cuestionarios:**

Para cada cuestionario existe una función separada que:
1. Crea el registro `Cuestionario` con código, nombre, descripción e instrucciones.
2. Crea cada `Pregunta` con su número de orden y texto.
3. Crea las `OpcionRespuesta` de cada pregunta con su texto y valor numérico.

Por ejemplo, para el PHQ-2 (una versión corta de 2 preguntas del PHQ-9):

```python
def crear_cuestionario_phq2():
    cuest = Cuestionario(
        codigo='PHQ-2',
        nombre='PHQ-2 — Cuestionario de Salud del Paciente (versión corta)',
        descripcion='Tamizaje rápido de depresión con 2 preguntas.',
        instrucciones='Durante las últimas 2 semanas...',
        puntaje_maximo=6,
        activo=True
    )
    db.session.add(cuest)
    db.session.flush()  # Obtiene el ID asignado sin hacer commit
    
    opciones_base = [
        ('Para nada', 0),
        ('Varios días', 1),
        ('Más de la mitad de los días', 2),
        ('Casi todos los días', 3),
    ]
    
    preguntas = [
        (1, 'Poco interés o placer en hacer cosas'),
        (2, 'Sentirse desanimado/a, deprimido/a o sin esperanza'),
    ]
    
    for num, texto in preguntas:
        pregunta = Pregunta(
            cuestionario_id=cuest.id,
            numero_orden=num,
            texto=texto
        )
        db.session.add(pregunta)
        db.session.flush()
        
        for texto_op, valor in opciones_base:
            opcion = OpcionRespuesta(
                pregunta_id=pregunta.id,
                texto=texto_op,
                valor=valor
            )
            db.session.add(opcion)
```

`db.session.flush()` es importante: envía los objetos a la base de datos para que reciban su ID asignado automáticamente, pero sin hacer commit. Esto permite referenciar el ID del cuestionario al crear preguntas, y el ID de la pregunta al crear opciones, todo dentro de la misma transacción.

**Cuestionarios con ítems inversos (IDERE, IDARE):**

Para los cuestionarios de depresión y ansiedad que tienen ítems directos e inversos, la estrategia fue pre-calcular los valores en la base de datos. Así el servicio de evaluación puede simplemente sumar todos los valores sin lógica adicional.

Ejemplo de ítem directo con escala 1-4 (en IDARE-E):
```
"Me siento calmado/a" → inverso
  - Nada (valor almacenado: 4, porque si no te sientes calmado, sumas 4)
  - Algo (valor: 3)
  - Bastante (valor: 2)
  - Mucho (valor: 1)
```

Ejemplo de ítem directo (ansiedad directa):
```
"Me siento tenso/a" → directo
  - Nada (valor: 1)
  - Algo (valor: 2)
  - Bastante (valor: 3)
  - Mucho (valor: 4)
```

---

## PARTE 4 — PRIMERAS PRUEBAS DEL SISTEMA

### 4.1 Inicializar la base de datos

Con el entorno virtual activado y en la carpeta raíz del proyecto:

```bash
python seed_data.py
```

Si todo está bien, verá una salida como:
```
Creando roles...
Creando usuarios...
Creando cuestionario PHQ-2...
Creando cuestionario PHQ-9...
[...]
Base de datos inicializada correctamente.
```

### 4.2 Ejecutar el servidor de desarrollo

```bash
python run.py
```

La salida esperada:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
 * Restarting with stat
```

### 4.3 Verificar que el sistema funciona: lista de pruebas

Abrir el navegador en `http://127.0.0.1:5000` y seguir esta secuencia:

**Prueba 1: Acceso al login**
- La URL raíz `/` debe redirigir a `/auth/login`
- Debe aparecer el formulario de inicio de sesión

**Prueba 2: Autenticación como discente**
- Usuario: `A2024001` — Contraseña: `discente123`
- Debe redirigir al dashboard del discente
- El navbar debe mostrar solo "Inicio", "Cuestionarios" y "Material de Apoyo"

**Prueba 3: Responder un cuestionario**
- Ir a "Cuestionarios" y seleccionar PHQ-2
- Responder las 2 preguntas y enviar
- Debe mostrar la página de resultado con puntaje y nivel de riesgo

**Prueba 4: Ver historial**
- En el menú desplegable del usuario, ir a "Mi historial"
- Debe aparecer la evaluación recién realizada

**Prueba 5: Autenticación como orientador**
- Cerrar sesión y entrar con `orientador1` / `orient123`
- El navbar debe mostrar "Alertas", "Discentes" y "Reportes"
- Si el discente obtuvo riesgo elevado en el PHQ-2, debe aparecer en las alertas

**Prueba 6: Autenticación como administrador**
- Cerrar sesión y entrar con `admin` / `admin123`
- El navbar debe mostrar también "Administración"
- En `/admin/usuarios` debe aparecer la lista de usuarios

**Prueba 7: Cuestionario ASSIST**
- Como discente, ir al cuestionario ASSIST
- Debe mostrar la sección Q1 (uso alguna vez de sustancias)
- Si se marca "Sí" para alguna sustancia, deben aparecer las preguntas Q2-Q7 para esa sustancia
- Al enviar, debe mostrar puntajes por sustancia

**Prueba 8: Generación de PDF**
- Como orientador, ir a "Reportes"
- Seleccionar filtros y generar PDF
- El navegador debe descargar un archivo PDF

### 4.4 Problemas comunes durante las primeras pruebas

**Error: `could not connect to server`**
PostgreSQL no está corriendo. Ejecutar: `brew services start postgresql@14` (macOS) o `sudo systemctl start postgresql` (Linux).

**Error: `FATAL: password authentication failed for user "psico_user"`**
Las credenciales de la base de datos no coinciden. Verificar en `app/config.py` que la cadena de conexión tenga el usuario y contraseña correctos.

**Error: `ModuleNotFoundError: No module named 'flask'`**
El entorno virtual no está activado. Ejecutar `source venv/bin/activate`.

**Error al ejecutar `seed_data.py`: tablas no existen**
Normalmente `db.create_all()` crea las tablas. Si falla, verificar que la conexión a PostgreSQL funciona con `psql -U psico_user -d psico_monitor`.

---

## PARTE 5 — DESCRIPCIÓN DETALLADA DE TODOS LOS ARCHIVOS

Esta sección presenta un índice completo de todos los archivos del proyecto con su propósito.

### 5.1 Archivos raíz

| Archivo | Propósito |
|---|---|
| `run.py` | Punto de entrada. Crea la app Flask y arranca el servidor de desarrollo en `127.0.0.1:5000`. |
| `requirements.txt` | Lista todas las dependencias Python con sus versiones exactas. Se usa para reproducir el entorno. |
| `seed_data.py` | Script de inicialización de la BD. Crea roles, usuarios de prueba y todos los cuestionarios. |
| `.env` | (Si existe) Variables de entorno locales: `SECRET_KEY`, credenciales de BD. No se sube al repositorio. |

### 5.2 Paquete `app/`

| Archivo | Propósito |
|---|---|
| `app/__init__.py` | Fábrica de la aplicación. Inicializa extensiones (db, login_manager, csrf) y registra los 8 blueprints. |
| `app/config.py` | Configuración del sistema. Define `DevelopmentConfig`, `TestingConfig` y `ProductionConfig`. Incluye umbrales de cuestionarios y lista de sustancias ASSIST. |

### 5.3 Paquete `app/models/`

| Archivo | Clases | Tablas en BD | Propósito |
|---|---|---|---|
| `__init__.py` | — | — | Exporta todos los modelos para importación simplificada. |
| `usuario.py` | `Rol`, `Usuario` | `roles`, `usuarios` | Usuarios del sistema con sus roles y datos académicos. RBAC mediante métodos como `es_administrador()`. |
| `cuestionario.py` | `Cuestionario`, `Pregunta`, `OpcionRespuesta` | `cuestionarios`, `preguntas`, `opciones_respuesta` | Estructura completa de los cuestionarios psicométricos y sus ítems. |
| `evaluacion.py` | `Evaluacion`, `Respuesta`, `PuntajeSustancia` | `evaluaciones`, `respuestas`, `puntajes_sustancia` | Resultados de evaluaciones. Métodos para colores y etiquetas de riesgo. |
| `alerta.py` | `Alerta` | `alertas` | Alertas de riesgo generadas automáticamente. Ciclo de vida: pendiente → en_revision → atendida. |
| `material.py` | `Material` | `materiales` | Documentos y archivos de apoyo psicológico subidos por orientadores. |

### 5.4 Paquete `app/routes/`

| Archivo | Blueprint | Prefijo URL | Rutas principales |
|---|---|---|---|
| `auth.py` | `auth_bp` | `/auth` | `GET/POST /login`, `GET /logout`, `GET/POST /registro` |
| `main.py` | `main_bp` | `/` | `GET /` (index), `GET /inicio` (dashboard) |
| `admin.py` | `admin_bp` | `/admin` | Index, CRUD completo de usuarios, soft delete |
| `cuestionarios.py` | `cuestionarios_bp` | `/cuestionarios` | Listado, ver cuestionario, enviar respuestas |
| `evaluaciones.py` | `evaluaciones_bp` | `/evaluaciones` | Ver resultado, historial propio, historial de discente |
| `alertas.py` | `alertas_bp` | `/alertas` | Listado con filtros, detalle, atender, en revisión, listado discentes |
| `reportes.py` | `reportes_bp` | `/reportes` | Index con filtros, generación de PDF con xhtml2pdf |
| `materiales.py` | `materiales_bp` | `/materiales` | Listado, subir archivo, servir archivo, eliminar |

### 5.5 Paquete `app/services/`

| Archivo | Clase | Responsabilidad |
|---|---|---|
| `auth_service.py` | `AuthService` | Autenticación en 3 pasos (existe → activo → contraseña). Actualiza `ultimo_acceso`. |
| `evaluacion_service.py` | `EvaluacionService` | Suma puntajes, clasifica riesgo, detecta críticos, guarda evaluación + respuestas, dispara alertas. |
| `alerta_service.py` | `AlertaService` | Evalúa si una evaluación genera alertas. Gestiona ciclo de vida de alertas. Estadísticas. |

### 5.6 Paquete `app/utils/`

| Archivo | Contenido | Propósito |
|---|---|---|
| `decorators.py` | `rol_requerido()`, `solo_orientador`, `solo_admin` | Decoradores de control de acceso por rol. Redirigen con mensaje si el usuario no tiene permiso. |

### 5.7 Paquete `app/templates/`

| Archivo / Carpeta | Propósito |
|---|---|
| `base.html` | Template madre. Define navbar, área de contenido, footer. Todos los demás heredan de este. |
| `auth/login.html` | Página independiente de inicio de sesión. Sin navbar. Formulario limpio. |
| `auth/registro.html` | Formulario de registro para nuevos discentes. |
| `auth/registro_exitoso.html` | Confirmación de registro exitoso. |
| `main/inicio.html` | Dashboard principal. Muestra contenido diferente según el rol del usuario. |
| `admin/index.html` | Panel de administración con estadísticas del sistema. |
| `admin/usuarios.html` | Lista de todos los usuarios del sistema. |
| `admin/nuevo_usuario.html` | Formulario para crear un nuevo usuario (cualquier rol). |
| `admin/editar_usuario.html` | Formulario para modificar datos de un usuario existente. |
| `cuestionarios/listado.html` | Tarjetas con los cuestionarios disponibles. |
| `cuestionarios/responder.html` | Formulario genérico para cuestionarios estándar (PHQ-2, PHQ-9, IDERE, IDARE, ADNM). |
| `cuestionarios/responder_assist.html` | Formulario especial para ASSIST con preguntas agrupadas por sustancia. |
| `evaluaciones/resultado.html` | Resultado detallado con interpretación por instrumento y escala de referencia. |
| `evaluaciones/resultado_assist.html` | Resultado del ASSIST con puntajes por sustancia y su clasificación individual. |
| `evaluaciones/historial.html` | Tabla con todas las evaluaciones del usuario actual. |
| `evaluaciones/historial_usuario.html` | Igual al anterior pero para un discente específico (vista del orientador). |
| `alertas/listado.html` | Lista de alertas con filtros por estado y prioridad. |
| `alertas/detalle.html` | Detalle completo de una alerta con formulario para atenderla. |
| `alertas/listado_discentes.html` | Lista de discentes con buscador en el cliente (JavaScript). |
| `reportes/index.html` | Formulario de filtros para el reporte. |
| `reportes/reporte_pdf.html` | Template HTML usado para generar el PDF. Sin Bootstrap, solo CSS inline. |
| `materiales/listado.html` | Lista de materiales disponibles. Botones de subir/eliminar según rol. |
| `materiales/subir.html` | Formulario para subir un nuevo archivo. |

### 5.8 Directorio `uploads/`

| Directorio | Contenido |
|---|---|
| `uploads/materiales/` | Archivos físicos subidos por los orientadores. Los nombres son UUID hexadecimales para evitar conflictos. Este directorio se crea automáticamente si no existe cuando se sube el primer archivo. |

---

## PARTE 6 — CUESTIONARIOS IMPLEMENTADOS

El sistema implementa nueve cuestionarios psicométricos validados internacionalmente:

### 6.1 PHQ-2 — Patient Health Questionnaire (versión corta)
- **Propósito**: Tamizaje rápido de depresión con solo 2 preguntas.
- **Escala**: 0-6 (0=Para nada, 3=Casi todos los días por pregunta).
- **Clasificación**: Puntaje < 3 = sin indicador; ≥ 3 = indicador positivo (se sugiere aplicar PHQ-9).
- **Ítems**: 2 ítems directos.

### 6.2 PHQ-9 — Patient Health Questionnaire
- **Propósito**: Evaluación de depresión mayor con 9 preguntas basadas en los criterios DSM-5.
- **Escala**: 0-27.
- **Clasificación**: Mínimo (0-4), Leve (5-9), Moderado (10-14), Moderadamente Severo (15-19), Severo (20-27).
- **Alerta especial**: Cualquier respuesta ≥ 1 en la pregunta 9 (ideación suicida) genera automáticamente una alerta crítica.
- **Ítems**: 9 ítems directos.

### 6.3 ASSIST — Alcohol, Smoking and Substance Involvement Screening Test
- **Propósito**: Tamizaje de consumo de sustancias psicoactivas para 9 categorías.
- **Estructura especial**: 8 grupos de preguntas (Q1-Q8) aplicados a 9 sustancias: tabaco, alcohol, cannabis, cocaína, anfetaminas, inhalantes, tranquilizantes, alucinógenos y opiáceos.
- **Lógica condicional**: Q2-Q7 solo se muestran para las sustancias que el usuario dijo haber usado en Q1.
- **Puntaje**: Se calcula un puntaje independiente para cada sustancia (suma de Q2-Q7).
- **Clasificación por sustancia**: Bajo/Moderado/Alto (umbrales diferentes para alcohol vs. otras sustancias).

### 6.4 IDERE-E — Inventario de Depresión Estado-Rasgo (Estado)
- **Propósito**: Mide el estado depresivo en el momento presente ("¿Cómo me siento ahora?").
- **Escala**: 1-4 por ítem, rango total 20-80.
- **Opciones**: Casi nunca / Algunas veces / Frecuentemente / Casi siempre.
- **Ítems**: 20 ítems (mezcla de directos e inversos pre-calculados en BD).
- **Clasificación**: Bajo (20-24), Moderado (25-36), Alto (37-80).

### 6.5 IDERE-R — Inventario de Depresión Estado-Rasgo (Rasgo)
- **Propósito**: Mide la tendencia estable hacia la depresión ("¿Cómo me siento generalmente?").
- **Escala**: 1-4 por ítem, rango total 20-80.
- **Ítems**: 20 ítems con ítems inversos pre-calculados.
- **Clasificación**: Igual que IDERE-E.

### 6.6 IDARE-E — Inventario de Ansiedad Estado-Rasgo (Estado)
- **Propósito**: Mide la ansiedad como estado emocional transitorio ("¿Cómo me siento ahora?").
- **Escala**: 1-4 por ítem (Nada/Algo/Bastante/Mucho), rango total 20-80.
- **Ítems**: 20 ítems con ítems inversos pre-calculados en BD.
- **Clasificación**: Bajo (20-30), Moderado (31-44), Alto (45-80).

### 6.7 IDARE-R — Inventario de Ansiedad Estado-Rasgo (Rasgo)
- **Propósito**: Mide la ansiedad como rasgo de personalidad estable.
- **Escala**: 1-4 por ítem (Casi nunca/Algunas veces/Frecuentemente/Casi siempre), rango total 20-80.
- **Ítems**: 20 ítems con ítems inversos pre-calculados.
- **Clasificación**: Igual que IDARE-E.

### 6.8 ADNM-8 — Adjustment Disorder New Module (versión corta)
- **Propósito**: Tamizaje del trastorno de adaptación.
- **Escala**: 1-4 por ítem (Nunca/Raramente/A veces/A menudo), rango total 8-32.
- **Ítems**: 8 ítems directos. Sin ítems inversos.
- **Clasificación**: Bajo (8-19), Alto (20-32).

### 6.9 ADNM-20 — Adjustment Disorder New Module (versión completa)
- **Propósito**: Evaluación completa del trastorno de adaptación con 3 subescalas.
- **Subescalas**: Preocupación (7 ítems), Falta de adaptación (7 ítems), Evitación (6 ítems).
- **Escala**: 1-4 por ítem, rango total 20-80.
- **Ítems**: 20 ítems directos.
- **Clasificación**: Bajo (20-46), Alto (47-80).

---

## PARTE 7 — DECISIONES TÉCNICAS Y SU JUSTIFICACIÓN

### 7.1 ¿Por qué Flask y no Django?

Flask es un microframework: proporciona lo mínimo necesario (enrutamiento HTTP, sistema de plantillas) y permite agregar solo lo que el proyecto necesita. Para un sistema académico de alcance definido, esto es una ventaja: hay menos código automático que entender y menos convenciones que aprender. Django incluye muchas más funcionalidades integradas (ORM propio, admin automático, formularios) que en este proyecto se reimplementaron de forma más controlada.

### 7.2 ¿Por qué el patrón Application Factory?

Permite crear múltiples instancias de la aplicación con diferentes configuraciones. En el contexto de este proyecto, permite ejecutar pruebas automatizadas con una configuración distinta a la de producción, o ejecutar varias instancias con distintas bases de datos.

### 7.3 ¿Por qué Blueprints?

Los Blueprints dividen el código de rutas en archivos separados por dominio funcional. Sin ellos, todo el código de rutas estaría en un solo archivo que crecería indefinidamente. Con ellos, cada módulo (autenticación, cuestionarios, alertas, etc.) es independiente y puede desarrollarse y probarse por separado.

### 7.4 ¿Por qué SQLAlchemy y no SQL directo?

SQLAlchemy (ORM) permite trabajar con la base de datos usando clases y objetos Python en lugar de escribir SQL directamente. Ventajas: el código es más legible y mantenible, es más fácil cambiar de motor de BD si se necesita, y SQLAlchemy protege automáticamente contra inyección SQL en las consultas parametrizadas.

### 7.5 ¿Por qué soft delete para usuarios?

En lugar de eliminar un usuario con `db.session.delete(usuario)`, se establece `usuario.activo = False`. Esto preserva el historial: las evaluaciones y alertas del usuario siguen siendo accesibles para auditoría. Si se elimina un usuario de la BD, todas sus evaluaciones (por la restricción de clave foránea) también se eliminarían, perdiendo datos históricos.

### 7.6 ¿Por qué pre-calcular los valores inversos de IDERE/IDARE en la BD?

La alternativa habría sido agregar lógica de inversión en `EvaluacionService._calcular_puntaje_total()`. Pero eso habría requerido modificar el servicio para cada nuevo instrumento con ítems inversos. Al pre-calcular los valores en la base de datos (en el script `seed_data.py`), el servicio puede seguir haciendo una simple suma de todos los valores sin cambios. La complejidad está donde los datos se definen, no donde se procesan.

### 7.7 ¿Por qué cuestionarios separados para Estado y Rasgo (IDERE-E/IDERE-R)?

La arquitectura del sistema asocia un único puntaje a cada evaluación. Los instrumentos IDERE e IDARE tienen dos subescalas (Estado y Rasgo) que producen puntajes independientes. La solución más simple fue tratarlas como dos cuestionarios separados, cada uno con su propio ciclo de vida de evaluación y sus propias alertas. La alternativa (modificar la arquitectura para soportar múltiples puntajes por evaluación) habría requerido cambios más profundos en modelos, servicios y plantillas.

### 7.8 ¿Por qué xhtml2pdf para la generación de reportes?

Es una biblioteca Python pura que convierte HTML a PDF. La ventaja es que el reporte se puede diseñar como un template HTML normal de Jinja2, y la conversión es transparente. Alternativas como WeasyPrint o reportlab ofrecen más control pero requieren más dependencias del sistema. Para un prototipo académico, xhtml2pdf es suficiente.

---

## PARTE 8 — FLUJO COMPLETO DE UNA EVALUACIÓN

Para cerrar el documento, se describe el recorrido completo de datos desde que un discente abre un cuestionario hasta que el orientador atiende la alerta generada.

1. El discente abre `http://127.0.0.1:5000/cuestionarios/PHQ-9`.
2. `cuestionarios.ver('PHQ-9')` busca el cuestionario en BD por código, obtiene sus preguntas ordenadas y renderiza `responder.html`.
3. El discente selecciona una respuesta por pregunta y hace clic en "Enviar".
4. El navegador hace POST a `/cuestionarios/PHQ-9/enviar`.
5. `cuestionarios.enviar('PHQ-9')` recoge las respuestas del `request.form`, valida que no falte ninguna y llama a `EvaluacionService.procesar_evaluacion()`.
6. `EvaluacionService.procesar_evaluacion()` calcula el puntaje total sumando los valores de las opciones seleccionadas.
7. `_clasificar_riesgo('PHQ-9', puntaje)` determina el nivel de riesgo según los rangos definidos.
8. Se verifica si la respuesta a la pregunta 9 es ≥ 1 (alerta crítica por ideación suicida).
9. Se crea el registro `Evaluacion` y los registros `Respuesta` en la BD. Se hace `db.session.flush()` para obtener el ID de la evaluación.
10. `AlertaService.evaluar_y_generar_alertas(evaluacion)` determina si se debe generar una alerta y la crea en caso afirmativo.
11. Se hace `db.session.commit()` confirmando toda la transacción.
12. La ruta redirige a `/evaluaciones/resultado/<id>`.
13. `evaluaciones.resultado(id)` carga la evaluación de la BD y renderiza `resultado.html` con el puntaje, nivel, interpretación y escala de referencia.
14. El orientador abre `/alertas/` y ve la alerta generada con prioridad según el nivel de riesgo.
15. El orientador hace clic en la alerta, lee el detalle, y puede marcarla como "En revisión" o "Atendida", ingresando notas sobre la intervención realizada.

---

*Documento generado el 2026-04-07.*
*Sistema Mentis Cura — Prototipo de Tesis Académica.*
*Todos los instrumentos psicométricos son de dominio público o de libre uso académico.*
