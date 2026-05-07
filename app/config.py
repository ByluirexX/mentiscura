"""
================================================================================
MENTIS CURA - Configuracion del Sistema
================================================================================
Archivo: config.py
Descripcion: Define todas las configuraciones del sistema.
             Incluye configuracion de base de datos, seguridad y parametros
             de los cuestionarios PHQ-2, PHQ-9 y ASSIST.

Este archivo utiliza clases para organizar diferentes configuraciones:
    - Config: Configuracion base (compartida por todos los entornos)
    - DevelopmentConfig: Para desarrollo local
    - TestingConfig: Para pruebas automatizadas
    - ProductionConfig: Para el servidor de produccion

Autor: Proyecto de Tesis
Fecha: 2024
================================================================================
"""

# =============================================================================
# IMPORTACIONES
# =============================================================================
import os  # Para leer variables de entorno y rutas
from datetime import timedelta  # Para configurar tiempos de sesion

# Obtener la ruta del directorio actual (donde esta este archivo)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


# =============================================================================
# CLASE DE CONFIGURACION BASE
# =============================================================================
class Config:
    """
    Configuracion base del sistema.

    Esta clase contiene todas las configuraciones compartidas por todos
    los entornos (desarrollo, pruebas, produccion).

    Las clases hijas pueden sobrescribir estos valores segun necesiten.
    """

    # -------------------------------------------------------------------------
    # CONFIGURACION DE SEGURIDAD
    # -------------------------------------------------------------------------
    # SECRET_KEY: Clave secreta para firmar cookies y tokens
    # IMPORTANTE: En produccion, usar una clave aleatoria segura
    # Se puede configurar via variable de entorno SECRET_KEY
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-secreta-desarrollo-cambiar-en-produccion'

    # -------------------------------------------------------------------------
    # CONFIGURACION DE BASE DE DATOS
    # -------------------------------------------------------------------------
    # URI de conexion a PostgreSQL
    # Formato: postgresql://usuario:password@host:puerto/nombre_base_datos
    #
    # Componentes:
    #   - psico_user: Usuario de la base de datos
    #   - psico123: Contrasena del usuario
    #   - localhost: Servidor donde esta PostgreSQL
    #   - 5432: Puerto por defecto de PostgreSQL
    #   - psico_monitor: Nombre de la base de datos
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://psico_user:psico123@localhost:5432/psico_monitor'

    # Desactivar el seguimiento de modificaciones (mejora rendimiento)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # -------------------------------------------------------------------------
    # CONFIGURACION DE SESIONES
    # -------------------------------------------------------------------------
    # Tiempo de vida de la sesion: 2 horas
    # Despues de este tiempo, el usuario debe volver a iniciar sesion
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)

    # Configuracion de cookies de sesion
    SESSION_COOKIE_SECURE = False  # True en produccion con HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Evita acceso desde JavaScript
    SESSION_COOKIE_SAMESITE = 'Lax'  # Proteccion contra CSRF

    # -------------------------------------------------------------------------
    # INFORMACION DE LA APLICACION
    # -------------------------------------------------------------------------
    APP_NAME = 'Mentis Cura - Sistema de Monitoreo Psicológico'
    APP_VERSION = '1.0.0'

    # -------------------------------------------------------------------------
    # CONFIGURACION DE SUBIDA DE ARCHIVOS
    # -------------------------------------------------------------------------
    # Carpeta donde se guardan los materiales de apoyo
    MATERIALES_UPLOAD_FOLDER = os.path.join(BASE_DIR, '..', 'uploads', 'materiales')

    # Tamaño maximo de archivo: 16 MB
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # -------------------------------------------------------------------------
    # ROLES DEL SISTEMA
    # -------------------------------------------------------------------------
    # Define los tres roles disponibles y sus IDs
    ROLES = {
        'administrador': 1,  # Acceso total al sistema
        'orientador': 2,     # Gestiona alertas y ve evaluaciones
        'discente': 3        # Responde cuestionarios
    }

    # -------------------------------------------------------------------------
    # CONFIGURACION DE CUESTIONARIOS PHQ
    # -------------------------------------------------------------------------
    # PHQ-2: Cuestionario de tamizaje rapido (2 preguntas)
    # Un puntaje >= 3 indica posible riesgo y sugiere aplicar PHQ-9
    PHQ2_UMBRAL_RIESGO = 3

    # PHQ-9: Pregunta 9 evalua ideacion suicida
    # Cualquier respuesta >= 1 genera alerta critica automatica
    PHQ9_PREGUNTA_CRITICA = 9

    # -------------------------------------------------------------------------
    # CLASIFICACION DE NIVELES DE RIESGO PHQ-9
    # -------------------------------------------------------------------------
    # El puntaje total del PHQ-9 va de 0 a 27 (9 preguntas x 3 puntos max)
    # Cada rango indica un nivel de severidad diferente
    PHQ9_NIVELES = {
        'minimo': (0, 4),          # Sin indicadores significativos
        'leve': (5, 9),            # Sintomas leves
        'moderado': (10, 14),      # Requiere atencion
        'moderado_severo': (15, 19),  # Atencion prioritaria
        'severo': (20, 27)         # Atencion urgente
    }

    # -------------------------------------------------------------------------
    # CONFIGURACION DEL CUESTIONARIO ASSIST (OMS v3.1)
    # -------------------------------------------------------------------------
    # Lista de sustancias evaluadas por el ASSIST
    ASSIST_SUSTANCIAS = [
        'tabaco', 'alcohol', 'cannabis', 'cocaina', 'anfetaminas',
        'inhalantes', 'tranquilizantes', 'alucinogenos', 'opiaceos'
    ]

    # Clasificacion de riesgo ASSIST para alcohol (umbrales diferentes)
    ASSIST_NIVELES_ALCOHOL = {'bajo': (0, 10), 'moderado': (11, 26), 'alto': (27, 39)}

    # Clasificacion de riesgo ASSIST para todas las demas sustancias
    ASSIST_NIVELES_DEFAULT = {'bajo': (0, 3), 'moderado': (4, 26), 'alto': (27, 39)}



# =============================================================================
# CONFIGURACION PARA DESARROLLO
# =============================================================================
class DevelopmentConfig(Config):
    """
    Configuracion para entorno de desarrollo.

    Activa el modo debug para:
    - Ver errores detallados en el navegador
    - Recargar automaticamente cuando hay cambios en el codigo
    """
    DEBUG = True      # Activa modo debug
    TESTING = False   # No es entorno de pruebas


# =============================================================================
# CONFIGURACION PARA PRUEBAS
# =============================================================================
class TestingConfig(Config):
    """
    Configuracion para pruebas automatizadas.

    Usa una base de datos en memoria (SQLite) para:
    - Ejecutar pruebas rapidamente
    - No afectar datos reales
    - Empezar con una base limpia en cada prueba
    """
    DEBUG = True
    TESTING = True  # Activa modo de pruebas

    # Usar SQLite en memoria para pruebas (mas rapido)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

    # Desactivar CSRF para facilitar pruebas de formularios
    WTF_CSRF_ENABLED = False


# =============================================================================
# CONFIGURACION PARA PRODUCCION
# =============================================================================
class ProductionConfig(Config):
    """
    Configuracion para entorno de produccion.

    Desactiva debug y activa todas las medidas de seguridad.
    """
    DEBUG = False     # Nunca usar debug en produccion
    TESTING = False

    # Cookies seguras (solo se envian por HTTPS)
    SESSION_COOKIE_SECURE = True


# =============================================================================
# DICCIONARIO DE CONFIGURACIONES
# =============================================================================
# Este diccionario permite seleccionar la configuracion por nombre
# Ejemplo: config['development'] retorna DevelopmentConfig
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig  # Por defecto usa desarrollo
}
