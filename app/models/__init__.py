"""
================================================================================
MENTIS CURA - Modelos de Datos
================================================================================
Archivo: models/__init__.py
Descripcion: Archivo de inicializacion del paquete de modelos.
             Exporta todas las entidades para facilitar su importacion.

Los modelos representan las tablas de la base de datos usando SQLAlchemy ORM.
Cada clase define una tabla y sus columnas.

Modelos disponibles:
    - Usuario: Usuarios del sistema (discentes, orientadores, administradores)
    - Rol: Roles de acceso (administrador, orientador, discente)
    - Cuestionario: Cuestionarios PHQ-2 y PHQ-9
    - Pregunta: Preguntas de cada cuestionario
    - OpcionRespuesta: Opciones de respuesta (Nunca, Varios dias, etc.)
    - Evaluacion: Aplicacion de un cuestionario a un usuario
    - Respuesta: Respuesta individual a cada pregunta
    - Alerta: Alertas generadas por el sistema
Uso:
    from app.models import Usuario, Evaluacion, Alerta

Autor: Proyecto de Tesis
Fecha: 2024
================================================================================
"""

# =============================================================================
# IMPORTACIONES DE MODELOS
# =============================================================================
# Importar todos los modelos para que esten disponibles desde este paquete

# Modelos de usuarios y roles
from app.models.usuario import Usuario, Rol

# Modelos de cuestionarios
from app.models.cuestionario import Cuestionario, Pregunta, OpcionRespuesta

# Modelos de evaluaciones
from app.models.evaluacion import Evaluacion, Respuesta, PuntajeSustancia

# Modelo de alertas
from app.models.alerta import Alerta


# =============================================================================
# LISTA DE EXPORTACION
# =============================================================================
# __all__ define que nombres se exportan cuando se hace "from models import *"
__all__ = [
    'Usuario',          # Usuarios del sistema
    'Rol',              # Roles de acceso
    'Cuestionario',     # Cuestionarios PHQ
    'Pregunta',         # Preguntas de cuestionarios
    'OpcionRespuesta',  # Opciones de respuesta
    'Evaluacion',       # Evaluaciones realizadas
    'Respuesta',        # Respuestas individuales
    'PuntajeSustancia', # Puntajes por sustancia (ASSIST)
    'Alerta',           # Alertas del sistema
]
