"""
================================================================================
MENTIS CURA - Modelo de Alertas
================================================================================
Archivo: models/alerta.py
Descripcion: Define el modelo para el sistema de alertas internas.
             Las alertas notifican al personal autorizado sobre casos
             que requieren atencion.

IMPORTANTE: Las alertas son solo indicadores de que se requiere atencion
profesional. NO constituyen un diagnostico clinico.

Tipos de alertas:
    1. pregunta_critica: Respuesta positiva en P9 (ideacion suicida)
       - Prioridad: CRITICA
       - Requiere atencion inmediata

    2. puntaje_riesgo: Puntaje elevado en el cuestionario
       - Prioridad: Segun nivel de riesgo
       - Requiere seguimiento segun protocolo

Estados de una alerta:
    - pendiente: Recien creada, sin atender
    - en_revision: Un orientador la esta revisando
    - atendida: Ya fue atendida y documentada

Autor: Proyecto de Tesis
Fecha: 2024
================================================================================
"""

# =============================================================================
# IMPORTACIONES
# =============================================================================
from datetime import datetime  # Para fechas

from app import db  # Instancia de SQLAlchemy


# =============================================================================
# MODELO ALERTA
# =============================================================================
class Alerta(db.Model):
    """
    Modelo que representa una alerta generada por el sistema.

    Las alertas se generan automaticamente cuando:
    1. Un discente responde >= 1 en la pregunta 9 del PHQ-9
    2. El puntaje total indica un nivel de riesgo que requiere atencion

    Los orientadores y administradores pueden:
    - Ver la lista de alertas pendientes
    - Marcar alertas como "en revision"
    - Marcar alertas como "atendidas" con notas

    Atributos principales:
        - tipo: Tipo de alerta (pregunta_critica, puntaje_riesgo)
        - prioridad: Nivel de urgencia (baja, media, alta, critica)
        - estado: Estado actual (pendiente, en_revision, atendida)
        - mensaje: Descripcion de la alerta

    Tabla en BD: 'alertas'
    """
    __tablename__ = 'alertas'

    # -------------------------------------------------------------------------
    # COLUMNAS PRINCIPALES
    # -------------------------------------------------------------------------
    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # -------------------------------------------------------------------------
    # REFERENCIAS
    # -------------------------------------------------------------------------
    # ID del discente que genero la alerta (para ver su historial)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)

    # ID de la evaluacion que origino la alerta
    evaluacion_id = db.Column(db.Integer, db.ForeignKey('evaluaciones.id'), nullable=False)

    # -------------------------------------------------------------------------
    # CLASIFICACION DE LA ALERTA
    # -------------------------------------------------------------------------
    # Tipo de alerta:
    #   - 'pregunta_critica': Respuesta positiva en pregunta 9 (ideacion suicida)
    #   - 'puntaje_riesgo': Puntaje elevado que indica riesgo
    tipo = db.Column(db.String(50), nullable=False)

    # Prioridad de la alerta:
    #   - 'baja': Riesgo leve, seguimiento normal
    #   - 'media': Riesgo moderado, atencion pronta
    #   - 'alta': Riesgo moderado-severo o severo, atencion prioritaria
    #   - 'critica': Pregunta 9 positiva, atencion INMEDIATA
    prioridad = db.Column(db.String(20), nullable=False)

    # Mensaje descriptivo de la alerta
    mensaje = db.Column(db.Text, nullable=False)

    # -------------------------------------------------------------------------
    # ESTADO DE ATENCION
    # -------------------------------------------------------------------------
    # Estado actual de la alerta:
    #   - 'pendiente': Sin atender
    #   - 'en_revision': Siendo revisada por un orientador
    #   - 'atendida': Ya fue atendida y cerrada
    estado = db.Column(db.String(20), default='pendiente')

    # ID del orientador/admin que atendio la alerta
    atendida_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))

    # Fecha en que fue atendida
    fecha_atencion = db.Column(db.DateTime)

    # Notas del orientador sobre la atencion brindada
    notas_atencion = db.Column(db.Text)

    # -------------------------------------------------------------------------
    # AUDITORIA
    # -------------------------------------------------------------------------
    # Fecha de creacion de la alerta
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Fecha de ultima actualizacion
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # -------------------------------------------------------------------------
    # RELACIONES
    # -------------------------------------------------------------------------
    # Relacion con el usuario que atendio la alerta
    atendida_por = db.relationship('Usuario', foreign_keys=[atendida_por_id])

    # -------------------------------------------------------------------------
    # METODOS DE UTILIDAD VISUAL
    # -------------------------------------------------------------------------
    def color_prioridad(self):
        """
        Retorna la clase CSS de Bootstrap segun la prioridad.

        Se usa para colorear visualmente la prioridad:
            - azul (info): prioridad baja
            - amarillo (warning): prioridad media
            - rojo (danger): prioridad alta
            - negro (dark): prioridad critica

        Retorna:
            str: Nombre de la clase CSS de Bootstrap
        """
        colores = {
            'baja': 'info',       # Azul claro
            'media': 'warning',   # Amarillo
            'alta': 'danger',     # Rojo
            'critica': 'dark'     # Negro (maximo impacto visual)
        }
        return colores.get(self.prioridad, 'secondary')

    def icono_prioridad(self):
        """
        Retorna el icono de Bootstrap Icons segun la prioridad.

        Se usa para mostrar un icono visual junto a la alerta:
            - info-circle: prioridad baja
            - exclamation-triangle: prioridad media
            - exclamation-circle-fill: prioridad alta
            - exclamation-octagon-fill: prioridad critica

        Retorna:
            str: Nombre de la clase del icono
        """
        iconos = {
            'baja': 'bi-info-circle',
            'media': 'bi-exclamation-triangle',
            'alta': 'bi-exclamation-circle-fill',
            'critica': 'bi-exclamation-octagon-fill'
        }
        return iconos.get(self.prioridad, 'bi-bell')

    # -------------------------------------------------------------------------
    # METODOS DE ESTADO
    # -------------------------------------------------------------------------
    def esta_pendiente(self):
        """
        Verifica si la alerta esta pendiente de atencion.

        Retorna:
            bool: True si esta pendiente, False si ya fue atendida
        """
        return self.estado == 'pendiente'

    def marcar_en_revision(self, usuario_id):
        """
        Marca la alerta como "en revision".

        Se usa cuando un orientador comienza a revisar una alerta
        pero aun no la ha cerrado.

        Parametros:
            usuario_id (int): ID del orientador que revisa
        """
        self.estado = 'en_revision'
        self.atendida_por_id = usuario_id
        self.updated_at = datetime.utcnow()

    def marcar_atendida(self, usuario_id, notas=''):
        """
        Marca la alerta como atendida y cerrada.

        Se usa cuando el orientador ha completado el seguimiento
        del caso y documenta las acciones tomadas.

        Parametros:
            usuario_id (int): ID del orientador que atendio
            notas (str): Notas sobre la atencion brindada
        """
        self.estado = 'atendida'
        self.atendida_por_id = usuario_id
        self.fecha_atencion = datetime.utcnow()
        self.notas_atencion = notas
        self.updated_at = datetime.utcnow()

    def __repr__(self):
        """Representacion en texto de la alerta."""
        return f'<Alerta {self.id} - {self.tipo} ({self.prioridad})>'
