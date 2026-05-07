"""
================================================================================
MENTIS CURA - Servicio de Alertas
================================================================================
Archivo: services/alerta_service.py
Descripcion: Servicio que gestiona la generacion y manejo de alertas del sistema.
             Las alertas notifican al personal autorizado sobre casos que
             requieren atencion.

IMPORTANTE: Las alertas son SOLO indicadores para atencion profesional.
NO constituyen un diagnostico clinico.

Reglas de generacion de alertas:

1. ALERTA CRITICA (Pregunta 9 del PHQ-9):
   - Cualquier respuesta >= 1 en la pregunta sobre ideacion suicida
   - Prioridad: CRITICA
   - Requiere atencion INMEDIATA

2. ALERTA POR NIVEL DE RIESGO:
   - Leve: Prioridad BAJA
   - Moderado: Prioridad MEDIA
   - Moderadamente Severo: Prioridad ALTA
   - Severo: Prioridad ALTA

Las alertas criticas tienen prioridad sobre las de nivel de riesgo
para evitar duplicados.

Autor: Proyecto de Tesis
Fecha: 2024
================================================================================
"""

# =============================================================================
# IMPORTACIONES
# =============================================================================
from datetime import datetime  # Para fechas

from app import db  # Instancia de base de datos
from app.models.alerta import Alerta  # Modelo de alertas
from app.models.evaluacion import Evaluacion  # Modelo de evaluaciones


# =============================================================================
# CLASE DEL SERVICIO DE ALERTAS
# =============================================================================
class AlertaService:
    """
    Servicio para la gestion de alertas del sistema.

    Este servicio se encarga de:
    - Evaluar cuando se debe generar una alerta
    - Crear alertas con el mensaje y prioridad correctos
    - Consultar y filtrar alertas
    - Cambiar el estado de las alertas (pendiente -> atendida)
    """

    # -------------------------------------------------------------------------
    # CONSTANTE: PRIORIDAD SEGUN NIVEL DE RIESGO
    # -------------------------------------------------------------------------
    # Mapea cada nivel de riesgo a su prioridad de alerta correspondiente
    PRIORIDAD_POR_RIESGO = {
        'minimo': None,      # No genera alerta
        'bajo': None,        # No genera alerta (ASSIST/AUDIT)
        'leve': 'baja',      # Seguimiento normal
        'riesgo': 'media',   # Atencion pronta (AUDIT Zona II)
        'moderado': 'media', # Atencion pronta
        'perjudicial': 'alta',          # Atencion prioritaria (AUDIT Zona III)
        'moderado_severo': 'alta',      # Atencion prioritaria
        'alto': 'alta',                 # Atencion prioritaria (ASSIST)
        'posible_dependencia': 'alta',  # Atencion prioritaria (AUDIT Zona IV)
        'severo': 'alta'                # Atencion prioritaria
    }

    # -------------------------------------------------------------------------
    # METODO PRINCIPAL: EVALUAR Y GENERAR ALERTAS
    # -------------------------------------------------------------------------
    @classmethod
    def evaluar_y_generar_alertas(cls, evaluacion):
        """
        Evalua una evaluacion y genera las alertas correspondientes.

        Este metodo se llama automaticamente despues de procesar una evaluacion.
        Aplica las reglas de generacion de alertas y crea las que correspondan.

        Reglas:
        1. Si hay respuesta positiva (>=1) en pregunta 9: Alerta CRITICA
        2. Si el nivel de riesgo es leve o superior: Alerta segun nivel
           (solo si no hubo alerta critica, para evitar duplicados)

        Parametros:
            evaluacion (Evaluacion): Objeto de la evaluacion a evaluar

        Retorna:
            list: Lista de alertas generadas (puede estar vacia)

        Ejemplo:
            alertas = AlertaService.evaluar_y_generar_alertas(evaluacion)
            for alerta in alertas:
                print(f"Alerta creada: {alerta.tipo} - {alerta.prioridad}")
        """
        alertas_generadas = []

        # Delegar a logica ASSIST si corresponde
        if evaluacion.cuestionario.codigo == 'ASSIST':
            return cls._evaluar_alertas_assist(evaluacion)

        # ---------------------------------------------------------------------
        # REGLA 1: Verificar pregunta critica (ideacion suicida)
        # ---------------------------------------------------------------------
        # Esta es la alerta de maxima prioridad
        if evaluacion.alerta_pregunta_critica:
            alerta = cls._crear_alerta(
                evaluacion=evaluacion,
                tipo='pregunta_critica',
                prioridad='critica',
                mensaje=cls._generar_mensaje_critico(evaluacion)
            )
            alertas_generadas.append(alerta)

        # ---------------------------------------------------------------------
        # REGLA 2: Verificar nivel de riesgo
        # ---------------------------------------------------------------------
        # Solo si NO hubo alerta critica (para evitar duplicados)
        prioridad = cls.PRIORIDAD_POR_RIESGO.get(evaluacion.nivel_riesgo)
        if prioridad and not evaluacion.alerta_pregunta_critica:
            alerta = cls._crear_alerta(
                evaluacion=evaluacion,
                tipo='puntaje_riesgo',
                prioridad=prioridad,
                mensaje=cls._generar_mensaje_riesgo(evaluacion)
            )
            alertas_generadas.append(alerta)

        return alertas_generadas

    # -------------------------------------------------------------------------
    # METODO: EVALUAR ALERTAS ASSIST
    # -------------------------------------------------------------------------
    @classmethod
    def _evaluar_alertas_assist(cls, evaluacion):
        """
        Genera alertas especificas para evaluaciones ASSIST.

        Reglas (en orden de prioridad):
        1. Inyeccion reciente (Q8>=2): alerta critica
        2. Inyeccion alguna vez (Q8=1): alerta alta
        3. Sustancia con riesgo alto: alerta alta
        4. Sustancia con riesgo moderado: alerta media

        Parametros:
            evaluacion (Evaluacion): Evaluacion ASSIST completada

        Retorna:
            list: Alertas generadas
        """
        from app.models.evaluacion import PuntajeSustancia
        alertas_generadas = []

        # REGLA 1 y 2: Verificar inyeccion (Q8)
        if evaluacion.alerta_pregunta_critica:
            if evaluacion.puntaje_pregunta_critica >= 2:
                alerta = cls._crear_alerta(
                    evaluacion=evaluacion,
                    tipo='pregunta_critica',
                    prioridad='critica',
                    mensaje='ATENCIÓN PRIORITARIA: El discente ha reportado uso de sustancias '
                            'por vía inyectada en los últimos 3 meses. Se requiere intervención inmediata.'
                )
                alertas_generadas.append(alerta)
                return alertas_generadas
            else:
                alerta = cls._crear_alerta(
                    evaluacion=evaluacion,
                    tipo='pregunta_critica',
                    prioridad='alta',
                    mensaje='ATENCIÓN: El discente ha reportado uso de sustancias por vía '
                            'inyectada en algún momento de su vida. Se requiere seguimiento.'
                )
                alertas_generadas.append(alerta)
                return alertas_generadas

        # REGLA 3: Sustancia con riesgo alto
        puntajes = PuntajeSustancia.query.filter_by(evaluacion_id=evaluacion.id).all()
        sustancias_alto = [p for p in puntajes if p.nivel_riesgo == 'alto']
        if sustancias_alto:
            nombres = ', '.join(p.sustancia.capitalize() for p in sustancias_alto)
            alerta = cls._crear_alerta(
                evaluacion=evaluacion,
                tipo='puntaje_riesgo',
                prioridad='alta',
                mensaje=f'Evaluación ASSIST completada con riesgo ALTO en: {nombres}. '
                        f'Se requiere intervención breve o derivación a tratamiento especializado.'
            )
            alertas_generadas.append(alerta)
            return alertas_generadas

        # REGLA 4: Sustancia con riesgo moderado
        sustancias_moderado = [p for p in puntajes if p.nivel_riesgo == 'moderado']
        if sustancias_moderado:
            nombres = ', '.join(p.sustancia.capitalize() for p in sustancias_moderado)
            alerta = cls._crear_alerta(
                evaluacion=evaluacion,
                tipo='puntaje_riesgo',
                prioridad='media',
                mensaje=f'Evaluación ASSIST completada con riesgo MODERADO en: {nombres}. '
                        f'Se sugiere intervención breve según protocolo.'
            )
            alertas_generadas.append(alerta)

        return alertas_generadas

    # -------------------------------------------------------------------------
    # METODO AUXILIAR: CREAR ALERTA
    # -------------------------------------------------------------------------
    @classmethod
    def _crear_alerta(cls, evaluacion, tipo, prioridad, mensaje):
        """
        Crea y guarda una nueva alerta en la base de datos.

        Parametros:
            evaluacion (Evaluacion): Evaluacion que origina la alerta
            tipo (str): Tipo de alerta ('pregunta_critica' o 'puntaje_riesgo')
            prioridad (str): Nivel de prioridad ('baja', 'media', 'alta', 'critica')
            mensaje (str): Mensaje descriptivo de la alerta

        Retorna:
            Alerta: Objeto de la alerta creada
        """
        alerta = Alerta(
            usuario_id=evaluacion.usuario_id,  # Discente que genero la alerta
            evaluacion_id=evaluacion.id,       # Evaluacion de origen
            tipo=tipo,                         # Tipo de alerta
            prioridad=prioridad,               # Nivel de urgencia
            mensaje=mensaje,                   # Descripcion
            estado='pendiente'                 # Estado inicial
        )
        db.session.add(alerta)
        db.session.commit()
        return alerta

    # -------------------------------------------------------------------------
    # METODOS PARA GENERAR MENSAJES
    # -------------------------------------------------------------------------
    @classmethod
    def _generar_mensaje_critico(cls, evaluacion):
        """
        Genera el mensaje para una alerta de pregunta critica.

        Este mensaje se muestra cuando hay respuesta positiva
        en la pregunta 9 del PHQ-9 (ideacion suicida).

        Parametros:
            evaluacion (Evaluacion): Evaluacion con la alerta

        Retorna:
            str: Mensaje formateado para la alerta
        """
        return (
            f"ATENCIÓN PRIORITARIA: El discente ha indicado un valor de "
            f"{evaluacion.puntaje_pregunta_critica} en la pregunta sobre "
            f"pensamientos de hacerse daño (P9). Se requiere seguimiento inmediato."
        )

    @classmethod
    def _generar_mensaje_riesgo(cls, evaluacion):
        """
        Genera el mensaje para una alerta por nivel de riesgo.

        Parametros:
            evaluacion (Evaluacion): Evaluacion con la alerta

        Retorna:
            str: Mensaje formateado para la alerta
        """
        etiqueta = evaluacion.etiqueta_riesgo()  # Ej: "Moderadamente Severo"
        return (
            f"Evaluación {evaluacion.cuestionario.codigo} completada con "
            f"nivel de riesgo {etiqueta} (puntaje: {evaluacion.puntaje_total}). "
            f"Se sugiere seguimiento según protocolo."
        )

    # -------------------------------------------------------------------------
    # METODO: OBTENER ALERTAS CON FILTROS
    # -------------------------------------------------------------------------
    @classmethod
    def obtener_alertas_pendientes(cls, filtros=None):
        """
        Obtiene alertas con filtros opcionales.

        Las alertas se ordenan por:
        1. Prioridad (criticas primero)
        2. Fecha (mas recientes primero)

        Parametros:
            filtros (dict): Diccionario con filtros opcionales:
                - prioridad: 'baja', 'media', 'alta', 'critica'
                - estado: 'pendiente', 'en_revision', 'atendida'
                - fecha_desde: datetime
                - fecha_hasta: datetime

        Retorna:
            list: Lista de alertas ordenadas por prioridad y fecha

        Ejemplo:
            # Obtener alertas criticas pendientes
            alertas = AlertaService.obtener_alertas_pendientes({
                'estado': 'pendiente',
                'prioridad': 'critica'
            })
        """
        query = Alerta.query

        # Aplicar filtros si se proporcionan
        if filtros:
            if filtros.get('prioridad'):
                query = query.filter_by(prioridad=filtros['prioridad'])
            if filtros.get('estado'):
                query = query.filter_by(estado=filtros['estado'])
            if filtros.get('fecha_desde'):
                query = query.filter(Alerta.created_at >= filtros['fecha_desde'])
            if filtros.get('fecha_hasta'):
                query = query.filter(Alerta.created_at <= filtros['fecha_hasta'])

        # Ordenar: prioridad critica primero, luego por fecha
        return query.order_by(
            # db.case crea un ordenamiento personalizado
            db.case(
                (Alerta.prioridad == 'critica', 1),  # Critica = 1 (primero)
                (Alerta.prioridad == 'alta', 2),     # Alta = 2
                (Alerta.prioridad == 'media', 3),   # Media = 3
                (Alerta.prioridad == 'baja', 4),    # Baja = 4
                else_=5
            ),
            Alerta.created_at.desc()  # Mas recientes primero
        ).all()

    # -------------------------------------------------------------------------
    # METODO: MARCAR ALERTA COMO ATENDIDA
    # -------------------------------------------------------------------------
    @classmethod
    def marcar_alerta_atendida(cls, alerta_id, usuario_id, notas=''):
        """
        Marca una alerta como atendida por un orientador.

        Parametros:
            alerta_id (int): ID de la alerta a marcar
            usuario_id (int): ID del orientador que atiende
            notas (str): Notas sobre la atencion brindada

        Retorna:
            Alerta: Alerta actualizada, o None si no existe

        Ejemplo:
            alerta = AlertaService.marcar_alerta_atendida(
                alerta_id=5,
                usuario_id=2,
                notas="Se contacto al discente y se refirio a servicio medico."
            )
        """
        alerta = Alerta.query.get(alerta_id)
        if not alerta:
            return None

        # Usar el metodo del modelo para actualizar
        alerta.marcar_atendida(usuario_id, notas)
        db.session.commit()

        return alerta

    # -------------------------------------------------------------------------
    # METODO: OBTENER ESTADISTICAS DE ALERTAS
    # -------------------------------------------------------------------------
    @classmethod
    def obtener_estadisticas(cls):
        """
        Obtiene estadisticas generales de las alertas.

        Util para mostrar resumenes en el dashboard del orientador.

        Retorna:
            dict: Diccionario con estadisticas:
                - total: Total de alertas en el sistema
                - pendientes: Alertas sin atender
                - criticas_pendientes: Alertas criticas sin atender
                - atendidas: Alertas ya atendidas

        Ejemplo:
            stats = AlertaService.obtener_estadisticas()
            print(f"Pendientes: {stats['pendientes']}")
            print(f"Criticas: {stats['criticas_pendientes']}")
        """
        total = Alerta.query.count()

        return {
            'total': total,
            # Por estado
            'pendientes':   Alerta.query.filter_by(estado='pendiente').count(),
            'en_revision':  Alerta.query.filter_by(estado='en_revision').count(),
            'atendidas':    Alerta.query.filter_by(estado='atendida').count(),
            # Por prioridad (totales, independiente del estado)
            'criticas': Alerta.query.filter_by(prioridad='critica').count(),
            'altas':    Alerta.query.filter_by(prioridad='alta').count(),
            'medias':   Alerta.query.filter_by(prioridad='media').count(),
            'bajas':    Alerta.query.filter_by(prioridad='baja').count(),
            # Legado
            'criticas_pendientes': Alerta.query.filter_by(estado='pendiente', prioridad='critica').count(),
        }
