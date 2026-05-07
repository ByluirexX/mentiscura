"""
================================================================================
MENTIS CURA - Sistema de Monitoreo Psicologico
================================================================================
Archivo: __init__.py
Descripcion: Archivo de inicializacion de la aplicacion Flask.
             Configura todas las extensiones y registra los blueprints (rutas).

Este archivo implementa el patron "Application Factory" de Flask, que permite
crear multiples instancias de la aplicacion con diferentes configuraciones
(desarrollo, pruebas, produccion).

Arquitectura del sistema:
    - Capa de Presentacion: Templates HTML + Rutas (Blueprints)
    - Capa de Servicios: Logica de negocio
    - Capa de Datos: Modelos ORM con SQLAlchemy

Autor: Proyecto de Tesis
Fecha: 2024
================================================================================
"""

# =============================================================================
# IMPORTACIONES
# =============================================================================
import os  # Para operaciones del sistema operativo (crear directorios)

# Flask: Framework web principal
from flask import Flask

# SQLAlchemy: ORM para manejo de base de datos
from flask_sqlalchemy import SQLAlchemy

# Flask-Login: Manejo de sesiones de usuario
from flask_login import LoginManager

# Flask-WTF: Proteccion CSRF para formularios
from flask_wtf.csrf import CSRFProtect

# Importar configuraciones del sistema
from app.config import config


# =============================================================================
# INICIALIZACION DE EXTENSIONES
# =============================================================================
# Las extensiones se crean aqui sin asociarlas a una app especifica.
# Esto permite usar el patron "Application Factory".

# SQLAlchemy: Maneja la conexion y operaciones con la base de datos
db = SQLAlchemy()

# LoginManager: Gestiona las sesiones de usuario (login/logout)
login_manager = LoginManager()

# CSRFProtect: Protege formularios contra ataques Cross-Site Request Forgery
csrf = CSRFProtect()


# =============================================================================
# FUNCION FACTORY (CREADORA DE LA APLICACION)
# =============================================================================
def create_app(config_name='default'):
    """
    Crea y configura una instancia de la aplicacion Flask.

    Esta funcion implementa el patron "Application Factory", que permite:
    - Crear multiples instancias con diferentes configuraciones
    - Facilitar las pruebas unitarias
    - Separar la creacion de la configuracion

    Parametros:
        config_name (str): Nombre de la configuracion a usar.
                          Opciones: 'development', 'testing', 'production'
                          Por defecto: 'default' (que es 'development')

    Retorna:
        Flask: Instancia configurada de la aplicacion Flask

    Ejemplo de uso:
        app = create_app('development')
        app.run()
    """
    # -------------------------------------------------------------------------
    # PASO 1: Crear la instancia de Flask
    # -------------------------------------------------------------------------
    # __name__ indica el modulo actual, Flask lo usa para encontrar recursos
    app = Flask(__name__)

    # Cargar configuracion desde el diccionario 'config' definido en config.py
    app.config.from_object(config[config_name])

    # -------------------------------------------------------------------------
    # PASO 2: Crear directorio de datos si no existe
    # -------------------------------------------------------------------------
    # Este directorio almacena la base de datos SQLite (si se usa)
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)  # Crear el directorio 'data'

    # -------------------------------------------------------------------------
    # PASO 3: Inicializar extensiones con la aplicacion
    # -------------------------------------------------------------------------
    # init_app() asocia cada extension con esta instancia especifica de Flask

    db.init_app(app)          # Base de datos
    login_manager.init_app(app)  # Manejo de sesiones
    csrf.init_app(app)        # Proteccion CSRF

    # -------------------------------------------------------------------------
    # PASO 4: Configurar Flask-Login
    # -------------------------------------------------------------------------
    # login_view: Ruta a donde redirigir usuarios no autenticados
    login_manager.login_view = 'auth.login'

    # login_message: Mensaje a mostrar cuando se requiere autenticacion
    login_manager.login_message = 'Por favor inicie sesión para acceder a esta página.'

    # login_message_category: Tipo de mensaje flash (para estilo CSS)
    login_manager.login_message_category = 'warning'

    # -------------------------------------------------------------------------
    # PASO 5: Registrar Blueprints (modulos de rutas)
    # -------------------------------------------------------------------------
    # Los Blueprints organizan las rutas en modulos separados

    # Importar blueprints (se hace aqui para evitar importaciones circulares)
    from app.routes.auth import auth_bp           # Autenticacion
    from app.routes.main import main_bp           # Paginas principales
    from app.routes.cuestionarios import cuestionarios_bp  # Cuestionarios PHQ
    from app.routes.evaluaciones import evaluaciones_bp    # Resultados
    from app.routes.alertas import alertas_bp     # Alertas del sistema
    from app.routes.admin import admin_bp         # Administracion
    from app.routes.reportes import reportes_bp       # Reportes
    from app.routes.materiales import materiales_bp   # Materiales de apoyo
    from app.routes.ayuda import ayuda_bp             # Solicitudes de ayuda

    # Registrar cada blueprint en la aplicacion
    # url_prefix define el prefijo de URL para ese modulo
    app.register_blueprint(auth_bp)                    # /login, /logout, etc.
    app.register_blueprint(main_bp)                    # /, /inicio
    app.register_blueprint(cuestionarios_bp, url_prefix='/cuestionarios')
    app.register_blueprint(evaluaciones_bp, url_prefix='/evaluaciones')
    app.register_blueprint(alertas_bp, url_prefix='/alertas')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(reportes_bp, url_prefix='/reportes')
    app.register_blueprint(materiales_bp, url_prefix='/materiales')
    app.register_blueprint(ayuda_bp, url_prefix='/ayuda')

    # -------------------------------------------------------------------------
    # PASO 6: Crear directorio de uploads si no existe
    # -------------------------------------------------------------------------
    uploads_dir = app.config['MATERIALES_UPLOAD_FOLDER']
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)

    # -------------------------------------------------------------------------
    # PASO 7: Crear tablas en la base de datos
    # -------------------------------------------------------------------------
    # app_context() permite ejecutar codigo que requiere contexto de aplicacion
    with app.app_context():
        # Importar todos los modelos para que create_all() los detecte
        from app.models import material  # noqa: F401
        from app.models import solicitud_ayuda  # noqa: F401
        db.create_all()

    # Retornar la aplicacion configurada
    return app


# =============================================================================
# FUNCION PARA CARGAR USUARIO (Requerida por Flask-Login)
# =============================================================================
@login_manager.user_loader
def load_user(user_id):
    """
    Funcion requerida por Flask-Login para cargar un usuario de la sesion.

    Flask-Login almacena el ID del usuario en la sesion. Esta funcion
    convierte ese ID en un objeto Usuario completo.

    Parametros:
        user_id (str): ID del usuario almacenado en la sesion

    Retorna:
        Usuario: Objeto usuario correspondiente, o None si no existe

    Nota: El decorador @login_manager.user_loader registra esta funcion
          automaticamente con Flask-Login.
    """
    # Importar aqui para evitar importacion circular
    from app.models.usuario import Usuario

    # Buscar usuario por ID y retornarlo
    # get() retorna None si no encuentra el usuario
    return Usuario.query.get(int(user_id))
