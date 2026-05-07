"""
================================================================================
MENTIS CURA - Modelos de Evaluacion y Respuesta
================================================================================
Archivo: models/evaluacion.py
Descripcion: Define los modelos para registrar las evaluaciones realizadas.
             Cada evaluacion representa la aplicacion de un cuestionario
             a un discente, incluyendo todas sus respuestas.

Flujo de datos:
    1. El discente responde un cuestionario
    2. Se crea una Evaluacion con el puntaje total
    3. Se crean Respuestas individuales para cada pregunta
    4. Se clasifica el nivel de riesgo
    5. Si corresponde, se genera una Alerta

Clasificacion de riesgo PHQ-9:
    - 0-4: Minimo o ninguno
    - 5-9: Leve
    - 10-14: Moderado
    - 15-19: Moderadamente severo
    - 20-27: Severo

Clasificacion de riesgo ASSIST (por sustancia):
    - bajo: Sin riesgo significativo
    - moderado: Riesgo moderado, se sugiere intervencion breve
    - alto: Alto riesgo, se requiere atencion especializada

Autor: Proyecto de Tesis
Fecha: 2024
================================================================================
"""

# =============================================================================
# IMPORTACIONES
# =============================================================================
from datetime import datetime  # Para fechas de evaluacion

from app import db  # Instancia de SQLAlchemy


# =============================================================================
# MODELO EVALUACION
# =============================================================================
class Evaluacion(db.Model):
    """
    Modelo que representa una evaluacion (aplicacion de cuestionario).

    Una evaluacion registra cuando un discente responde un cuestionario.
    Almacena el puntaje total, el nivel de riesgo calculado, y si
    hubo respuesta positiva en la pregunta critica (P9 del PHQ-9).

    IMPORTANTE: Este sistema es de TAMIZAJE, no de diagnostico clinico.
    Los resultados solo indican que se requiere atencion profesional.

    Atributos:
        id (int): Identificador unico
        usuario_id (int): ID del discente que fue evaluado
        cuestionario_id (int): ID del cuestionario aplicado
        puntaje_total (int): Suma de todos los valores de respuesta
        nivel_riesgo (str): Clasificacion (minimo, leve, moderado, etc.)
        alerta_pregunta_critica (bool): Si P9 tuvo respuesta >= 1
        puntaje_pregunta_critica (int): Valor de la respuesta en P9
        observaciones (str): Notas opcionales del orientador
        fecha_evaluacion (datetime): Cuando se realizo la evaluacion
        respuestas: Relacion con las respuestas individuales
        alertas: Relacion con las alertas generadas

    Tabla en BD: 'evaluaciones'
    """
    __tablename__ = 'evaluaciones'

    # -------------------------------------------------------------------------
    # COLUMNAS PRINCIPALES
    # -------------------------------------------------------------------------
    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # -------------------------------------------------------------------------
    # REFERENCIAS (CLAVES FORANEAS)
    # -------------------------------------------------------------------------
    # ID del usuario (discente) que realizo la evaluacion
    # index=True para busquedas rapidas por usuario
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)

    # ID del cuestionario aplicado (PHQ-2 o PHQ-9)
    cuestionario_id = db.Column(db.Integer, db.ForeignKey('cuestionarios.id'), nullable=False)

    # -------------------------------------------------------------------------
    # RESULTADOS DE LA EVALUACION
    # -------------------------------------------------------------------------
    # Puntaje total (suma de todas las respuestas)
    # PHQ-2: 0-6, PHQ-9: 0-27
    puntaje_total = db.Column(db.Integer, nullable=False)

    # Nivel de riesgo clasificado segun el puntaje
    # Valores: 'minimo', 'leve', 'moderado', 'moderado_severo', 'severo'
    nivel_riesgo = db.Column(db.String(30), nullable=False)

    # -------------------------------------------------------------------------
    # INDICADORES DE PREGUNTA CRITICA (P9 DEL PHQ-9)
    # -------------------------------------------------------------------------
    # Indica si hubo respuesta positiva (>= 1) en la pregunta 9
    # La P9 evalua pensamientos de hacerse dano (ideacion suicida)
    alerta_pregunta_critica = db.Column(db.Boolean, default=False)

    # Valor especifico de la respuesta en P9 (0, 1, 2 o 3)
    puntaje_pregunta_critica = db.Column(db.Integer, default=0)

    # -------------------------------------------------------------------------
    # METADATOS
    # -------------------------------------------------------------------------
    # Notas u observaciones que puede agregar el orientador
    observaciones = db.Column(db.Text)

    # Fecha y hora de la evaluacion (indexado para busquedas por fecha)
    fecha_evaluacion = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # -------------------------------------------------------------------------
    # AUDITORIA
    # -------------------------------------------------------------------------
    # Fecha de creacion del registro
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # -------------------------------------------------------------------------
    # RELACIONES
    # -------------------------------------------------------------------------
    # Respuestas individuales a cada pregunta
    # cascade='all, delete-orphan' elimina las respuestas si se borra la evaluacion
    respuestas = db.relationship('Respuesta', backref='evaluacion',
                                 lazy='dynamic', cascade='all, delete-orphan')

    # Alertas generadas por esta evaluacion
    alertas = db.relationship('Alerta', backref='evaluacion', lazy='dynamic')

    # Puntajes por sustancia (solo para ASSIST)
    puntajes_sustancia = db.relationship('PuntajeSustancia', backref='evaluacion',
                                          lazy='dynamic', cascade='all, delete-orphan')

    # -------------------------------------------------------------------------
    # METODOS
    # -------------------------------------------------------------------------
    def obtener_respuestas_ordenadas(self):
        """
        Obtiene las respuestas ordenadas por numero de pregunta.

        Util para mostrar el detalle de la evaluacion en el orden
        correcto de las preguntas.

        Retorna:
            list: Lista de objetos Respuesta ordenados por pregunta.orden
        """
        from app.models.cuestionario import Pregunta
        return self.respuestas.join(Respuesta.pregunta).order_by(Pregunta.orden).all()

    def color_riesgo(self):
        """
        Retorna la clase CSS de Bootstrap segun el nivel de riesgo.

        Se usa para colorear visualmente el nivel de riesgo en la interfaz:
            - verde (success): riesgo minimo
            - azul (info): riesgo leve
            - amarillo (warning): riesgo moderado
            - naranja (orange): moderadamente severo
            - rojo (danger): riesgo severo

        Retorna:
            str: Nombre de la clase CSS de Bootstrap
        """
        colores = {
            'minimo': 'success',               # Verde
            'bajo': 'success',                 # Verde (ASSIST / AUDIT Zona I)
            'leve': 'info',                    # Azul claro
            'riesgo': 'info',                  # Azul (AUDIT Zona II)
            'moderado': 'warning',             # Amarillo
            'perjudicial': 'warning',          # Amarillo (AUDIT Zona III)
            'moderado_severo': 'orange',       # Naranja
            'alto': 'danger',                  # Rojo (ASSIST)
            'posible_dependencia': 'danger',   # Rojo (AUDIT Zona IV)
            'severo': 'danger'                 # Rojo
        }
        return colores.get(self.nivel_riesgo, 'secondary')

    def etiqueta_riesgo(self):
        """
        Retorna el texto legible del nivel de riesgo.

        Convierte el codigo interno (ej: 'moderado_severo')
        a texto para mostrar (ej: 'Moderadamente Severo')

        Retorna:
            str: Etiqueta legible del nivel de riesgo
        """
        etiquetas = {
            'minimo': 'Mínimo o Ninguno',
            'bajo': 'Bajo',
            'leve': 'Leve',
            'riesgo': 'Zona II — Consumo de Riesgo',
            'moderado': 'Moderado',
            'perjudicial': 'Zona III — Consumo Perjudicial',
            'moderado_severo': 'Moderadamente Severo',
            'alto': 'Alto',
            'posible_dependencia': 'Zona IV — Posible Dependencia',
            'severo': 'Severo'
        }
        return etiquetas.get(self.nivel_riesgo, self.nivel_riesgo)

    def __repr__(self):
        """Representacion en texto de la evaluacion."""
        return f'<Evaluacion {self.id} - Usuario {self.usuario_id}>'


# =============================================================================
# MODELO RESPUESTA
# =============================================================================
class Respuesta(db.Model):
    """
    Modelo que representa la respuesta a una pregunta individual.

    Cada evaluacion tiene multiples respuestas (una por pregunta).
    La respuesta almacena el valor numerico seleccionado.

    Atributos:
        id (int): Identificador unico
        evaluacion_id (int): ID de la evaluacion a la que pertenece
        pregunta_id (int): ID de la pregunta respondida
        valor (int): Valor seleccionado (0, 1, 2, o 3)
        created_at (datetime): Fecha de creacion
        pregunta: Relacion con el objeto Pregunta

    Tabla en BD: 'respuestas'
    """
    __tablename__ = 'respuestas'

    # -------------------------------------------------------------------------
    # COLUMNAS
    # -------------------------------------------------------------------------
    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Clave foranea a la evaluacion
    evaluacion_id = db.Column(db.Integer, db.ForeignKey('evaluaciones.id'), nullable=False)

    # Clave foranea a la pregunta
    pregunta_id = db.Column(db.Integer, db.ForeignKey('preguntas.id'), nullable=False)

    # Valor numerico seleccionado (0=Nunca, 1=Varios dias, 2=Mas de la mitad, 3=Casi todos)
    valor = db.Column(db.Integer, nullable=False)

    # Fecha de creacion del registro
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # -------------------------------------------------------------------------
    # RELACIONES
    # -------------------------------------------------------------------------
    # Relacion con la pregunta (para acceder al texto de la pregunta)
    pregunta = db.relationship('Pregunta')

    def __repr__(self):
        """Representacion en texto de la respuesta."""
        return f'<Respuesta Pregunta {self.pregunta_id} = {self.valor}>'


# =============================================================================
# MODELO PUNTAJE POR SUSTANCIA (ASSIST)
# =============================================================================
class PuntajeSustancia(db.Model):
    """
    Modelo que representa el puntaje SSIS de una sustancia en ASSIST.

    Cada evaluacion ASSIST genera un PuntajeSustancia por cada sustancia
    que el usuario reporto haber usado (Q1=Si). El SSIS (Specific Substance
    Involvement Score) es la suma de Q2+Q3+Q4+Q5+Q6+Q7 para esa sustancia.

    Atributos:
        id (int): Identificador unico
        evaluacion_id (int): ID de la evaluacion ASSIST
        sustancia (str): Nombre de la sustancia evaluada
        puntaje (int): SSIS calculado (0-39)
        nivel_riesgo (str): Clasificacion ('bajo', 'moderado', 'alto')
        created_at (datetime): Fecha de creacion

    Tabla en BD: 'puntajes_sustancia'
    """
    __tablename__ = 'puntajes_sustancia'

    id = db.Column(db.Integer, primary_key=True)
    evaluacion_id = db.Column(db.Integer, db.ForeignKey('evaluaciones.id'), nullable=False)
    sustancia = db.Column(db.String(50), nullable=False)
    puntaje = db.Column(db.Integer, nullable=False, default=0)
    nivel_riesgo = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def color_riesgo(self):
        """Retorna clase CSS segun nivel de riesgo."""
        colores = {'bajo': 'success', 'moderado': 'warning', 'alto': 'danger'}
        return colores.get(self.nivel_riesgo, 'secondary')

    def etiqueta_riesgo(self):
        """Retorna texto legible del nivel de riesgo."""
        etiquetas = {'bajo': 'Bajo', 'moderado': 'Moderado', 'alto': 'Alto'}
        return etiquetas.get(self.nivel_riesgo, self.nivel_riesgo)

    def __repr__(self):
        return f'<PuntajeSustancia {self.sustancia}: {self.puntaje} ({self.nivel_riesgo})>'
