"""
================================================================================
MENTIS CURA - Servicio de Evaluacion
================================================================================
Archivo: services/evaluacion_service.py
Descripcion: Servicio que implementa toda la logica de negocio para las
             evaluaciones. Incluye calculo de puntajes, clasificacion de
             riesgo y generacion de alertas.

Este servicio es el corazon del sistema de tamizaje. Implementa las reglas
oficiales de los cuestionarios PHQ-2, PHQ-9 y ASSIST.

Reglas de clasificacion:

PHQ-2 (Puntaje 0-6):
    - < 3: Sin indicador de riesgo
    - >= 3: Indicador positivo (sugiere aplicar PHQ-9)

PHQ-9 (Puntaje 0-27):
    - 0-4: Minimo o Ninguno
    - 5-9: Leve
    - 10-14: Moderado
    - 15-19: Moderadamente Severo
    - 20-27: Severo

IMPORTANTE: Pregunta 9 del PHQ-9
    Cualquier respuesta >= 1 en esta pregunta (sobre ideacion suicida)
    genera automaticamente una alerta de prioridad CRITICA.

Autor: Proyecto de Tesis
Fecha: 2024
================================================================================
"""

# =============================================================================
# IMPORTACIONES
# =============================================================================
from datetime import datetime  # Para fechas de evaluacion

from flask import current_app  # Para acceder a configuracion

from app import db  # Instancia de base de datos
from app.models.cuestionario import Cuestionario, Pregunta  # Modelos de cuestionarios
from app.models.evaluacion import Evaluacion, Respuesta, PuntajeSustancia  # Modelos de evaluaciones
from app.services.alerta_service import AlertaService  # Servicio de alertas


# =============================================================================
# CLASE DEL SERVICIO DE EVALUACION
# =============================================================================
class EvaluacionService:
    """
    Servicio para procesamiento de evaluaciones.

    Esta clase implementa:
    - Calculo de puntajes totales
    - Clasificacion de niveles de riesgo
    - Deteccion de respuestas criticas (P9)
    - Generacion automatica de alertas
    - Consulta de historial y estadisticas
    """

    # -------------------------------------------------------------------------
    # CONSTANTES: ESCALA DE CLASIFICACION PHQ-9
    # -------------------------------------------------------------------------
    # Cada tupla define (puntaje_minimo, puntaje_maximo) para cada nivel
    CLASIFICACION_PHQ9 = {
        'minimo': (0, 4),           # Riesgo minimo o ninguno
        'leve': (5, 9),             # Riesgo leve
        'moderado': (10, 14),       # Riesgo moderado
        'moderado_severo': (15, 19), # Riesgo moderadamente severo
        'severo': (20, 27)          # Riesgo severo
    }

    # Umbral para PHQ-2: puntaje >= 3 indica riesgo
    UMBRAL_PHQ2 = 3

    # -------------------------------------------------------------------------
    # CONSTANTES: CLASIFICACION AUDIT (OMS)
    # Rango de puntaje: 0-40
    # -------------------------------------------------------------------------
    CLASIFICACION_AUDIT = {
        'bajo':                (0,  7),   # Zona I  - Bajo riesgo
        'riesgo':              (8,  15),  # Zona II - Consumo de riesgo
        'perjudicial':         (16, 19),  # Zona III - Consumo perjudicial
        'posible_dependencia': (20, 40),  # Zona IV  - Posible dependencia
    }

    # -------------------------------------------------------------------------
    # CONSTANTES: CLASIFICACION ASSIST POR SUSTANCIA
    # -------------------------------------------------------------------------
    CLASIFICACION_ASSIST_ALCOHOL = {'bajo': (0, 10), 'moderado': (11, 26), 'alto': (27, 39)}
    CLASIFICACION_ASSIST_DEFAULT = {'bajo': (0, 3), 'moderado': (4, 26), 'alto': (27, 39)}

    # -------------------------------------------------------------------------
    # CONSTANTES: CLASIFICACION IDERE (Estado y Rasgo)
    # Rango de puntaje: 20-80
    # -------------------------------------------------------------------------
    CLASIFICACION_IDERE = {
        'bajo':     (20, 24),   # Sin indicador significativo de depresion
        'moderado': (25, 36),   # Indicador leve a moderado
        'alto':     (37, 80),   # Indicador severo
    }

    # -------------------------------------------------------------------------
    # CONSTANTES: CLASIFICACION IDARE (Estado y Rasgo)
    # Rango de puntaje: 20-80
    # -------------------------------------------------------------------------
    CLASIFICACION_IDARE = {
        'bajo':     (20, 30),   # Sin indicador significativo de ansiedad
        'moderado': (31, 44),   # Ansiedad moderada
        'alto':     (45, 80),   # Ansiedad elevada
    }

    # -------------------------------------------------------------------------
    # CONSTANTES: CLASIFICACION ADNM-8
    # Rango de puntaje: 8-32
    # -------------------------------------------------------------------------
    CLASIFICACION_ADNM8 = {
        'bajo':  (8,  19),   # Sin indicador significativo
        'alto':  (20, 32),   # Indicador positivo (sugiere aplicar ADNM-20)
    }

    # -------------------------------------------------------------------------
    # CONSTANTES: CLASIFICACION ADNM-20
    # Rango de puntaje: 20-80
    # -------------------------------------------------------------------------
    CLASIFICACION_ADNM20 = {
        'bajo':  (20, 46),   # Sin indicador significativo
        'alto':  (47, 80),   # Probable trastorno adaptativo
    }

    # -------------------------------------------------------------------------
    # METODO PRINCIPAL: PROCESAR EVALUACION
    # -------------------------------------------------------------------------
    @classmethod
    def procesar_evaluacion(cls, usuario_id, cuestionario_id, respuestas_dict):
        """
        Procesa una evaluacion completa de un cuestionario.

        Este es el metodo principal que se llama cuando un discente
        termina de responder un cuestionario. Realiza los siguientes pasos:

        1. Calcula el puntaje total sumando todas las respuestas
        2. Detecta si hay respuesta positiva en pregunta critica (P9)
        3. Clasifica el nivel de riesgo segun el puntaje
        4. Guarda la evaluacion y todas las respuestas
        5. Genera alertas si corresponde

        Parametros:
            usuario_id (int): ID del discente que responde
            cuestionario_id (int): ID del cuestionario (PHQ-2 o PHQ-9)
            respuestas_dict (dict): Diccionario {pregunta_id: valor}
                                   Ejemplo: {1: 2, 2: 1, 3: 0, ...}

        Retorna:
            Evaluacion: Objeto de la evaluacion creada

        Excepciones:
            ValueError: Si el cuestionario no existe

        Ejemplo:
            respuestas = {1: 0, 2: 1, 3: 2, 4: 1, 5: 0, 6: 1, 7: 2, 8: 1, 9: 0}
            evaluacion = EvaluacionService.procesar_evaluacion(
                usuario_id=5,
                cuestionario_id=2,  # PHQ-9
                respuestas_dict=respuestas
            )
            print(f"Puntaje: {evaluacion.puntaje_total}")
            print(f"Nivel: {evaluacion.nivel_riesgo}")
        """
        # ---------------------------------------------------------------------
        # PASO 1: Obtener el cuestionario
        # ---------------------------------------------------------------------
        cuestionario = Cuestionario.query.get(cuestionario_id)
        if not cuestionario:
            raise ValueError('Cuestionario no encontrado')

        # Delegar a procesamiento especifico si es ASSIST
        if cuestionario.codigo == 'ASSIST':
            return cls._procesar_assist(usuario_id, cuestionario, respuestas_dict)

        # ---------------------------------------------------------------------
        # PASO 2: Calcular puntaje total
        # ---------------------------------------------------------------------
        # El puntaje es la suma de todos los valores de respuesta
        puntaje_total = sum(respuestas_dict.values())

        # ---------------------------------------------------------------------
        # PASO 3: Detectar respuesta en pregunta critica (P9 del PHQ-9)
        # ---------------------------------------------------------------------
        alerta_critica = False  # Indica si hay respuesta positiva en P9
        puntaje_critica = 0     # Valor de la respuesta en P9

        # Revisar cada respuesta para detectar pregunta critica
        for pregunta_id, valor in respuestas_dict.items():
            pregunta = Pregunta.query.get(pregunta_id)
            # Si la pregunta esta marcada como critica y tiene valor >= 1
            if pregunta and pregunta.es_critica and valor >= 1:
                alerta_critica = True
                puntaje_critica = valor

        # ---------------------------------------------------------------------
        # PASO 4: Clasificar nivel de riesgo
        # ---------------------------------------------------------------------
        nivel_riesgo = cls._clasificar_riesgo(cuestionario.codigo, puntaje_total)

        # ---------------------------------------------------------------------
        # PASO 5: Crear y guardar la evaluacion
        # ---------------------------------------------------------------------
        evaluacion = Evaluacion(
            usuario_id=usuario_id,
            cuestionario_id=cuestionario_id,
            puntaje_total=puntaje_total,
            nivel_riesgo=nivel_riesgo,
            alerta_pregunta_critica=alerta_critica,
            puntaje_pregunta_critica=puntaje_critica,
            fecha_evaluacion=datetime.utcnow()
        )
        db.session.add(evaluacion)
        db.session.flush()  # Obtener el ID de la evaluacion sin hacer commit

        # ---------------------------------------------------------------------
        # PASO 6: Guardar cada respuesta individual
        # ---------------------------------------------------------------------
        for pregunta_id, valor in respuestas_dict.items():
            respuesta = Respuesta(
                evaluacion_id=evaluacion.id,
                pregunta_id=pregunta_id,
                valor=valor
            )
            db.session.add(respuesta)

        # Confirmar todos los cambios en la base de datos
        db.session.commit()

        # ---------------------------------------------------------------------
        # PASO 7: Generar alertas si corresponde
        # ---------------------------------------------------------------------
        # El servicio de alertas evaluara si se deben crear alertas
        AlertaService.evaluar_y_generar_alertas(evaluacion)

        return evaluacion

    # -------------------------------------------------------------------------
    # METODO AUXILIAR: CLASIFICAR NIVEL DE RIESGO
    # -------------------------------------------------------------------------
    @classmethod
    def _clasificar_riesgo(cls, codigo_cuestionario, puntaje):
        """
        Clasifica el nivel de riesgo segun el puntaje obtenido.

        Aplica las reglas oficiales de clasificacion de PHQ-2 y PHQ-9.

        PHQ-2 (Puntaje 0-6):
            - < 3: Sin indicador de riesgo (retorna 'minimo')
            - >= 3: Indicador positivo (retorna 'moderado')
                    Nota: Sugiere aplicar PHQ-9 para evaluacion completa

        PHQ-9 (Puntaje 0-27):
            - 0-4: Minimo o ninguno
            - 5-9: Leve
            - 10-14: Moderado
            - 15-19: Moderadamente severo
            - 20-27: Severo

        Parametros:
            codigo_cuestionario (str): 'PHQ-2' o 'PHQ-9'
            puntaje (int): Puntaje total obtenido (suma de respuestas)

        Retorna:
            str: Nivel de riesgo ('minimo', 'leve', 'moderado',
                                 'moderado_severo', 'severo')
        """
        if codigo_cuestionario == 'PHQ-2':
            # PHQ-2: Clasificacion binaria (con/sin indicador de riesgo)
            if puntaje >= cls.UMBRAL_PHQ2:
                # Puntaje >= 3 indica que se deberia aplicar PHQ-9
                return 'moderado'
            return 'minimo'

        elif codigo_cuestionario == 'PHQ-9':
            # PHQ-9: Clasificacion en 5 niveles
            for nivel, (min_val, max_val) in cls.CLASIFICACION_PHQ9.items():
                if min_val <= puntaje <= max_val:
                    return nivel
            # Si por alguna razon excede el rango, es severo
            return 'severo'

        elif codigo_cuestionario == 'AUDIT':
            # AUDIT (OMS): 4 zonas de riesgo (puntaje 0-40)
            for nivel, (min_val, max_val) in cls.CLASIFICACION_AUDIT.items():
                if min_val <= puntaje <= max_val:
                    return nivel
            return 'posible_dependencia'

        elif codigo_cuestionario == 'ASSIST':
            # ASSIST: La clasificacion global se determina en _procesar_assist
            return 'bajo'

        elif codigo_cuestionario in ('IDERE-E', 'IDERE-R'):
            # IDERE: Clasificacion en 3 niveles (puntaje 20-80)
            for nivel, (min_val, max_val) in cls.CLASIFICACION_IDERE.items():
                if min_val <= puntaje <= max_val:
                    return nivel
            return 'alto'

        elif codigo_cuestionario in ('IDARE-E', 'IDARE-R'):
            # IDARE: Clasificacion en 3 niveles (puntaje 20-80)
            for nivel, (min_val, max_val) in cls.CLASIFICACION_IDARE.items():
                if min_val <= puntaje <= max_val:
                    return nivel
            return 'alto'

        elif codigo_cuestionario == 'ADNM-8':
            # ADNM-8: Clasificacion binaria (puntaje 8-32)
            for nivel, (min_val, max_val) in cls.CLASIFICACION_ADNM8.items():
                if min_val <= puntaje <= max_val:
                    return nivel
            return 'alto'

        elif codigo_cuestionario == 'ADNM-20':
            # ADNM-20: Clasificacion binaria (puntaje 20-80)
            for nivel, (min_val, max_val) in cls.CLASIFICACION_ADNM20.items():
                if min_val <= puntaje <= max_val:
                    return nivel
            return 'alto'

        # Si es un cuestionario desconocido
        return 'no_clasificado'

    # -------------------------------------------------------------------------
    # METODO: PROCESAR EVALUACION ASSIST
    # -------------------------------------------------------------------------
    @classmethod
    def _procesar_assist(cls, usuario_id, cuestionario, respuestas_dict):
        """
        Procesa una evaluacion ASSIST completa.

        Calcula el SSIS (Specific Substance Involvement Score) por cada
        sustancia reportada, clasifica el riesgo por sustancia y genera
        alertas correspondientes.

        Parametros:
            usuario_id (int): ID del discente
            cuestionario (Cuestionario): Objeto del cuestionario ASSIST
            respuestas_dict (dict): {pregunta_id: valor}

        Retorna:
            Evaluacion: Objeto de la evaluacion creada
        """
        preguntas = cuestionario.obtener_preguntas_ordenadas()

        # Construir mapa de preguntas con sus campos ASSIST
        preguntas_map = {}
        for p in preguntas:
            preguntas_map[p.id] = p

        # Determinar que sustancias tienen Q1 > 0 (fueron usadas)
        sustancias_usadas = set()
        for pid, valor in respuestas_dict.items():
            p = preguntas_map.get(pid)
            if p and p.grupo_pregunta == 'Q1' and valor > 0:
                sustancias_usadas.add(p.sustancia)

        # Calcular SSIS por sustancia (suma de Q2+Q3+Q4+Q5+Q6+Q7)
        ssis_por_sustancia = {}
        for sustancia in sustancias_usadas:
            ssis = 0
            for pid, valor in respuestas_dict.items():
                p = preguntas_map.get(pid)
                if p and p.sustancia == sustancia and p.grupo_pregunta in ('Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7'):
                    ssis += valor
            ssis_por_sustancia[sustancia] = ssis

        # Clasificar riesgo por sustancia
        riesgo_por_sustancia = {}
        for sustancia, ssis in ssis_por_sustancia.items():
            riesgo_por_sustancia[sustancia] = cls._clasificar_riesgo_assist(sustancia, ssis)

        # Determinar nivel_riesgo global = el mas alto entre todas las sustancias
        jerarquia = {'bajo': 0, 'moderado': 1, 'alto': 2}
        nivel_global = 'bajo'
        for nivel in riesgo_por_sustancia.values():
            if jerarquia.get(nivel, 0) > jerarquia.get(nivel_global, 0):
                nivel_global = nivel

        # Detectar Q8 (inyeccion)
        alerta_critica = False
        puntaje_critica = 0
        for pid, valor in respuestas_dict.items():
            p = preguntas_map.get(pid)
            if p and p.grupo_pregunta == 'Q8':
                puntaje_critica = valor
                if valor >= 1:
                    alerta_critica = True

        # Calcular puntaje_total = suma de todos los SSIS
        puntaje_total = sum(ssis_por_sustancia.values())

        # Crear la evaluacion
        evaluacion = Evaluacion(
            usuario_id=usuario_id,
            cuestionario_id=cuestionario.id,
            puntaje_total=puntaje_total,
            nivel_riesgo=nivel_global,
            alerta_pregunta_critica=alerta_critica,
            puntaje_pregunta_critica=puntaje_critica,
            fecha_evaluacion=datetime.utcnow()
        )
        db.session.add(evaluacion)
        db.session.flush()

        # Guardar respuestas individuales
        for pregunta_id, valor in respuestas_dict.items():
            respuesta = Respuesta(
                evaluacion_id=evaluacion.id,
                pregunta_id=pregunta_id,
                valor=valor
            )
            db.session.add(respuesta)

        # Crear PuntajeSustancia por cada sustancia usada
        for sustancia, ssis in ssis_por_sustancia.items():
            ps = PuntajeSustancia(
                evaluacion_id=evaluacion.id,
                sustancia=sustancia,
                puntaje=ssis,
                nivel_riesgo=riesgo_por_sustancia[sustancia]
            )
            db.session.add(ps)

        db.session.commit()

        # Generar alertas
        AlertaService.evaluar_y_generar_alertas(evaluacion)

        return evaluacion

    # -------------------------------------------------------------------------
    # METODO: CLASIFICAR RIESGO ASSIST POR SUSTANCIA
    # -------------------------------------------------------------------------
    @classmethod
    def _clasificar_riesgo_assist(cls, sustancia, puntaje):
        """
        Clasifica el nivel de riesgo ASSIST para una sustancia especifica.

        El alcohol tiene umbrales diferentes al resto de sustancias segun
        la guia de la OMS.

        Parametros:
            sustancia (str): Nombre de la sustancia
            puntaje (int): SSIS calculado

        Retorna:
            str: 'bajo', 'moderado' o 'alto'
        """
        if sustancia == 'alcohol':
            rangos = cls.CLASIFICACION_ASSIST_ALCOHOL
        else:
            rangos = cls.CLASIFICACION_ASSIST_DEFAULT

        for nivel, (min_val, max_val) in rangos.items():
            if min_val <= puntaje <= max_val:
                return nivel
        return 'alto'

    # -------------------------------------------------------------------------
    # METODO: OBTENER HISTORIAL DE USUARIO
    # -------------------------------------------------------------------------
    @classmethod
    def obtener_historial_usuario(cls, usuario_id, limite=10):
        """
        Obtiene el historial de evaluaciones de un usuario.

        Retorna las evaluaciones mas recientes primero.

        Parametros:
            usuario_id (int): ID del usuario (discente)
            limite (int): Cantidad maxima de evaluaciones a retornar

        Retorna:
            list: Lista de objetos Evaluacion ordenados por fecha descendente

        Ejemplo:
            historial = EvaluacionService.obtener_historial_usuario(5, limite=5)
            for eval in historial:
                print(f"{eval.fecha_evaluacion}: {eval.puntaje_total} pts")
        """
        return Evaluacion.query.filter_by(usuario_id=usuario_id)\
            .order_by(Evaluacion.fecha_evaluacion.desc())\
            .limit(limite)\
            .all()

    # -------------------------------------------------------------------------
    # METODO: OBTENER ESTADISTICAS DE USUARIO
    # -------------------------------------------------------------------------
    @classmethod
    def obtener_estadisticas_usuario(cls, usuario_id):
        """
        Calcula estadisticas de las evaluaciones de un usuario.

        Util para mostrar un resumen en el dashboard del discente
        o para el analisis del orientador.

        Parametros:
            usuario_id (int): ID del usuario (discente)

        Retorna:
            dict: Diccionario con estadisticas:
                - total_evaluaciones: Numero total de evaluaciones
                - ultima_evaluacion: Fecha de la ultima evaluacion
                - promedio_puntaje: Promedio de puntajes
                - alertas_criticas: Numero de alertas por P9

        Ejemplo:
            stats = EvaluacionService.obtener_estadisticas_usuario(5)
            print(f"Total evaluaciones: {stats['total_evaluaciones']}")
            print(f"Promedio: {stats['promedio_puntaje']:.1f}")
        """
        # Obtener todas las evaluaciones del usuario
        evaluaciones = Evaluacion.query.filter_by(usuario_id=usuario_id).all()

        # Si no tiene evaluaciones, retornar valores por defecto
        if not evaluaciones:
            return {
                'total_evaluaciones': 0,
                'ultima_evaluacion': None,
                'promedio_puntaje': 0,
                'alertas_criticas': 0
            }

        # Calcular estadisticas
        return {
            'total_evaluaciones': len(evaluaciones),
            'ultima_evaluacion': max(e.fecha_evaluacion for e in evaluaciones),
            'promedio_puntaje': sum(e.puntaje_total for e in evaluaciones) / len(evaluaciones),
            'alertas_criticas': sum(1 for e in evaluaciones if e.alerta_pregunta_critica)
        }

    # -------------------------------------------------------------------------
    # METODO: VALIDAR RESPUESTAS
    # -------------------------------------------------------------------------
    @classmethod
    def validar_respuestas(cls, cuestionario_id, respuestas_dict):
        """
        Valida que las respuestas de un cuestionario sean completas y validas.

        Se ejecuta antes de procesar la evaluacion para asegurar
        que los datos son correctos.

        Validaciones:
        1. El cuestionario debe existir
        2. Todas las preguntas deben tener respuesta
        3. Los valores deben estar en el rango 0-3

        Parametros:
            cuestionario_id (int): ID del cuestionario
            respuestas_dict (dict): Diccionario {pregunta_id: valor}

        Retorna:
            tuple: (es_valido, mensaje_error)
                - Si valido: (True, None)
                - Si invalido: (False, "mensaje de error")

        Ejemplo:
            valido, error = EvaluacionService.validar_respuestas(2, respuestas)
            if not valido:
                print(f"Error: {error}")
        """
        # Verificar que el cuestionario exista
        cuestionario = Cuestionario.query.get(cuestionario_id)
        if not cuestionario:
            return False, 'Cuestionario no encontrado'

        # Validacion especifica para ASSIST
        if cuestionario.codigo == 'ASSIST':
            return cls._validar_respuestas_assist(cuestionario, respuestas_dict)

        # Obtener todas las preguntas del cuestionario
        preguntas = cuestionario.obtener_preguntas_ordenadas()
        preguntas_ids = {p.id for p in preguntas}

        # Verificar que todas las preguntas tengan respuesta
        respuestas_ids = set(respuestas_dict.keys())

        if preguntas_ids != respuestas_ids:
            faltantes = preguntas_ids - respuestas_ids
            return False, f'Faltan respuestas para {len(faltantes)} pregunta(s)'

        # Verificar que los valores esten en el rango valido
        # Se obtiene el maximo dinamicamente de las opciones de cada pregunta
        for pregunta_id, valor in respuestas_dict.items():
            if not isinstance(valor, int) or valor < 0:
                return False, f'Valor inválido para pregunta {pregunta_id}'
            pregunta = Pregunta.query.get(pregunta_id)
            if pregunta:
                valores_validos = {op.valor for op in pregunta.opciones.all()}
                if valores_validos and valor not in valores_validos:
                    return False, f'Valor inválido para pregunta {pregunta_id}'

        return True, None

    # -------------------------------------------------------------------------
    # METODO: VALIDAR RESPUESTAS ASSIST
    # -------------------------------------------------------------------------
    @classmethod
    def _validar_respuestas_assist(cls, cuestionario, respuestas_dict):
        """
        Valida respuestas del cuestionario ASSIST.

        Reglas:
        - Q1 (9 preguntas): Todas obligatorias
        - Q2-Q7: Solo obligatorias para sustancias con Q1 > 0
        - Q8: Siempre obligatoria
        - Valores validos varian por grupo

        Parametros:
            cuestionario (Cuestionario): Cuestionario ASSIST
            respuestas_dict (dict): {pregunta_id: valor}

        Retorna:
            tuple: (es_valido, mensaje_error)
        """
        preguntas = cuestionario.obtener_preguntas_ordenadas()

        # Determinar sustancias con Q1 > 0
        sustancias_usadas = set()
        for p in preguntas:
            if p.grupo_pregunta == 'Q1':
                valor = respuestas_dict.get(p.id)
                if valor is None:
                    return False, 'Debe responder todas las preguntas de la sección inicial (Q1)'
                if not isinstance(valor, int) or valor not in (0, 1):
                    return False, f'Valor inválido para pregunta Q1'
                if valor > 0:
                    sustancias_usadas.add(p.sustancia)

        # Validar Q2-Q7 para sustancias usadas
        valores_q2_q5 = {0, 2, 3, 4, 6}
        valores_q6_q7 = {0, 3, 6}
        for p in preguntas:
            if p.grupo_pregunta in ('Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7'):
                if p.sustancia in sustancias_usadas:
                    valor = respuestas_dict.get(p.id)
                    if valor is None:
                        return False, f'Faltan respuestas para {p.sustancia}'
                    if p.grupo_pregunta in ('Q2', 'Q3', 'Q4', 'Q5'):
                        if valor not in valores_q2_q5:
                            return False, f'Valor inválido para pregunta {p.grupo_pregunta}'
                    else:
                        if valor not in valores_q6_q7:
                            return False, f'Valor inválido para pregunta {p.grupo_pregunta}'

        # Validar Q8 (siempre obligatoria)
        for p in preguntas:
            if p.grupo_pregunta == 'Q8':
                valor = respuestas_dict.get(p.id)
                if valor is None:
                    return False, 'Debe responder la pregunta sobre uso por vía inyectada (Q8)'
                if not isinstance(valor, int) or valor not in (0, 1, 2):
                    return False, 'Valor inválido para Q8'

        return True, None
