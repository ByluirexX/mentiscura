"""
================================================================================
MENTIS CURA - Modelos de Cuestionario
================================================================================
Archivo: models/cuestionario.py
Descripcion: Define los modelos para los cuestionarios PHQ-2, PHQ-9 y ASSIST.

Estructura de datos:
    Cuestionario (PHQ-2, PHQ-9, ASSIST)
        └── Preguntas (1, 2, 3...)
            └── Opciones de Respuesta (Nunca, Varios dias, etc.)

Cuestionarios implementados:
    - PHQ-2: Tamizaje rapido con 2 preguntas (puntaje 0-6)
    - PHQ-9: Evaluacion completa con 9 preguntas (puntaje 0-27)
    - ASSIST: Evaluacion de consumo de sustancias (9 sustancias, puntaje por sustancia)

Nota sobre campos especificos de ASSIST (en modelo Pregunta):
    - sustancia: identifica la sustancia evaluada por la pregunta
    - grupo_pregunta: grupo al que pertenece (Q1-Q8) dentro del ASSIST

Autor: Proyecto de Tesis
Fecha: 2024
================================================================================
"""

# =============================================================================
# IMPORTACIONES
# =============================================================================
from datetime import datetime  # Para fechas de creacion

from app import db  # Instancia de SQLAlchemy


# =============================================================================
# MODELO CUESTIONARIO
# =============================================================================
class Cuestionario(db.Model):
    """
    Modelo que representa un cuestionario/instrumento de tamizaje.

    Un cuestionario es un instrumento estandarizado para evaluar
    sintomas de salud mental. Contiene multiples preguntas.

    Ejemplos: PHQ-2, PHQ-9, GAD-7 (ansiedad), etc.

    Atributos:
        id (int): Identificador unico
        codigo (str): Codigo corto del cuestionario (ej: 'PHQ-2')
        nombre (str): Nombre completo
        descripcion (str): Descripcion del proposito
        instrucciones (str): Instrucciones para el evaluado
        puntaje_minimo (int): Puntaje minimo posible
        puntaje_maximo (int): Puntaje maximo posible
        activo (bool): Si el cuestionario esta disponible
        preguntas: Relacion con las preguntas del cuestionario

    Tabla en BD: 'cuestionarios'
    """
    __tablename__ = 'cuestionarios'

    # -------------------------------------------------------------------------
    # COLUMNAS PRINCIPALES
    # -------------------------------------------------------------------------
    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Codigo unico del cuestionario (ej: 'PHQ-2', 'PHQ-9')
    codigo = db.Column(db.String(20), unique=True, nullable=False)

    # Nombre completo del cuestionario
    nombre = db.Column(db.String(100), nullable=False)

    # Descripcion del proposito y uso del cuestionario
    descripcion = db.Column(db.Text)

    # Instrucciones que se muestran al usuario antes de responder
    instrucciones = db.Column(db.Text)

    # -------------------------------------------------------------------------
    # CONFIGURACION DE PUNTUACION
    # -------------------------------------------------------------------------
    # Puntaje minimo posible (generalmente 0)
    puntaje_minimo = db.Column(db.Integer, default=0)

    # Puntaje maximo posible
    # PHQ-2: 6 (2 preguntas x 3 puntos)
    # PHQ-9: 27 (9 preguntas x 3 puntos)
    puntaje_maximo = db.Column(db.Integer, nullable=False)

    # -------------------------------------------------------------------------
    # ESTADO
    # -------------------------------------------------------------------------
    # Indica si el cuestionario esta activo (disponible para uso)
    activo = db.Column(db.Boolean, default=True)

    # Fecha de creacion
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # -------------------------------------------------------------------------
    # RELACIONES
    # -------------------------------------------------------------------------
    # Relacion con las preguntas del cuestionario
    # order_by='Pregunta.orden' ordena las preguntas por su numero
    preguntas = db.relationship('Pregunta', backref='cuestionario',
                                lazy='dynamic', order_by='Pregunta.orden')

    # Relacion con las evaluaciones que usan este cuestionario
    evaluaciones = db.relationship('Evaluacion', backref='cuestionario', lazy='dynamic')

    # -------------------------------------------------------------------------
    # METODOS
    # -------------------------------------------------------------------------
    def obtener_preguntas_ordenadas(self):
        """
        Obtiene todas las preguntas del cuestionario ordenadas por numero.

        Retorna:
            list: Lista de objetos Pregunta ordenados por su campo 'orden'

        Ejemplo:
            cuestionario = Cuestionario.query.filter_by(codigo='PHQ-9').first()
            preguntas = cuestionario.obtener_preguntas_ordenadas()
            for p in preguntas:
                print(f"Pregunta {p.orden}: {p.texto}")
        """
        return self.preguntas.order_by(Pregunta.orden).all()

    def __repr__(self):
        """Representacion en texto del cuestionario."""
        return f'<Cuestionario {self.codigo}>'


# =============================================================================
# MODELO PREGUNTA
# =============================================================================
class Pregunta(db.Model):
    """
    Modelo que representa una pregunta individual de un cuestionario.

    Cada pregunta tiene un texto y multiples opciones de respuesta.
    El campo 'es_critica' marca preguntas que requieren atencion especial
    (como la pregunta 9 del PHQ-9 sobre ideacion suicida).

    Atributos:
        id (int): Identificador unico
        cuestionario_id (int): ID del cuestionario al que pertenece
        orden (int): Numero de pregunta (1, 2, 3...)
        texto (str): Texto de la pregunta
        es_critica (bool): Si es pregunta critica (genera alerta)
        opciones: Relacion con las opciones de respuesta

    Tabla en BD: 'preguntas'
    """
    __tablename__ = 'preguntas'

    # -------------------------------------------------------------------------
    # COLUMNAS PRINCIPALES
    # -------------------------------------------------------------------------
    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Clave foranea al cuestionario
    cuestionario_id = db.Column(db.Integer, db.ForeignKey('cuestionarios.id'), nullable=False)

    # Numero de orden de la pregunta (1, 2, 3, etc.)
    orden = db.Column(db.Integer, nullable=False)

    # Texto de la pregunta que se muestra al usuario
    texto = db.Column(db.Text, nullable=False)

    # Indica si es una pregunta critica
    # La pregunta 9 del PHQ-9 (ideacion suicida) es critica
    # Cualquier respuesta >= 1 genera alerta automatica
    es_critica = db.Column(db.Boolean, default=False)

    # -------------------------------------------------------------------------
    # CAMPOS ESPECIFICOS PARA ASSIST
    # -------------------------------------------------------------------------
    # Sustancia asociada (solo ASSIST): 'tabaco', 'alcohol', 'cannabis', etc.
    sustancia = db.Column(db.String(50), nullable=True)

    # Grupo de pregunta (solo ASSIST): 'Q1', 'Q2', ..., 'Q8'
    grupo_pregunta = db.Column(db.String(10), nullable=True)

    # Fecha de creacion
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # -------------------------------------------------------------------------
    # RELACIONES
    # -------------------------------------------------------------------------
    # Opciones de respuesta para esta pregunta
    opciones = db.relationship('OpcionRespuesta', backref='pregunta',
                               lazy='dynamic', order_by='OpcionRespuesta.valor')

    # -------------------------------------------------------------------------
    # METODOS
    # -------------------------------------------------------------------------
    def obtener_opciones_ordenadas(self):
        """
        Obtiene las opciones de respuesta ordenadas por valor.

        Las opciones se ordenan de menor a mayor valor (0, 1, 2, 3)
        para mostrarlas en el orden correcto en el formulario.

        Retorna:
            list: Lista de opciones ordenadas por valor
        """
        return self.opciones.order_by(OpcionRespuesta.valor).all()

    def __repr__(self):
        """Representacion en texto de la pregunta."""
        return f'<Pregunta {self.orden} - Cuestionario {self.cuestionario_id}>'


# =============================================================================
# MODELO OPCION DE RESPUESTA
# =============================================================================
class OpcionRespuesta(db.Model):
    """
    Modelo que representa una opcion de respuesta para una pregunta.

    Los cuestionarios PHQ usan una escala Likert de 4 puntos:
        0 = Nunca
        1 = Varios dias
        2 = Mas de la mitad de los dias
        3 = Casi todos los dias

    Atributos:
        id (int): Identificador unico
        pregunta_id (int): ID de la pregunta a la que pertenece
        texto (str): Texto de la opcion (ej: "Nunca")
        valor (int): Valor numerico de la opcion (0, 1, 2, 3)

    Tabla en BD: 'opciones_respuesta'
    """
    __tablename__ = 'opciones_respuesta'

    # -------------------------------------------------------------------------
    # COLUMNAS
    # -------------------------------------------------------------------------
    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Clave foranea a la pregunta
    pregunta_id = db.Column(db.Integer, db.ForeignKey('preguntas.id'), nullable=False)

    # Texto de la opcion que se muestra al usuario
    texto = db.Column(db.String(200), nullable=False)

    # Valor numerico de la opcion (para calcular el puntaje)
    valor = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        """Representacion en texto de la opcion."""
        return f'<Opcion {self.texto} ({self.valor})>'
