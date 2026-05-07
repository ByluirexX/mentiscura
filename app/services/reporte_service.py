"""
================================================================================
MENTIS CURA - Servicio de Reportes
================================================================================
Archivo: services/reporte_service.py
Descripcion: Servicio que implementa la logica de negocio para la generacion
             de reportes del sistema. Provee datos agregados y filtrados para
             los reportes generales y de alertas.

Tipos de reporte:
    - General: totales, promedios, distribucion de riesgo por carrera/compania
    - Alertas: conteo por prioridad y estado, matriz cruzada

Filtros disponibles:
    - Periodicidad: diario, semanal, mensual, semestral
    - Anio que cursa: 1 a 6 (opcional, combinable con periodicidad)

Autor: Proyecto de Tesis
Fecha: 2024
================================================================================
"""

# =============================================================================
# IMPORTACIONES
# =============================================================================
from datetime import datetime, timedelta

from app import db
from app.models.alerta import Alerta
from app.models.evaluacion import Evaluacion
from app.models.usuario import Usuario


# =============================================================================
# CLASE DEL SERVICIO DE REPORTES
# =============================================================================
class ReporteService:
    """
    Servicio para la generacion de reportes del sistema.

    Provee metodos para:
    - Calcular rangos de fechas segun la periodicidad seleccionada
    - Generar datos agregados para el reporte general
    - Generar datos agregados para el reporte de alertas
    """

    # -------------------------------------------------------------------------
    # CONSTANTES
    # -------------------------------------------------------------------------
    # Orden de presentacion de niveles de riesgo (de menor a mayor)
    NIVELES_ORDEN = [
        'minimo', 'bajo', 'leve', 'riesgo', 'moderado',
        'perjudicial', 'moderado_severo', 'alto', 'posible_dependencia', 'severo'
    ]

    # Etiquetas legibles para cada nivel de riesgo
    ETIQUETAS_RIESGO = {
        'minimo': 'Mínimo o Ninguno',
        'bajo': 'Bajo',
        'leve': 'Leve',
        'riesgo': 'Consumo de Riesgo',
        'moderado': 'Moderado',
        'perjudicial': 'Consumo Perjudicial',
        'moderado_severo': 'Moderadamente Severo',
        'alto': 'Alto',
        'posible_dependencia': 'Posible Dependencia',
        'severo': 'Severo',
    }

    # Etiquetas para periodicidades
    ETIQUETAS_PERIODICIDAD = {
        'diario': 'Diario',
        'semanal': 'Semanal',
        'mensual': 'Mensual',
        'semestral': 'Semestral',
        'anual': 'Anual',
    }

    # -------------------------------------------------------------------------
    # METODO: CALCULAR RANGO DE FECHAS
    # -------------------------------------------------------------------------
    @classmethod
    def calcular_rango_fechas(cls, periodicidad):
        """
        Calcula el rango de fechas (desde, hasta) segun la periodicidad.

        Reglas:
            - diario:    desde las 00:00 de hoy hasta el momento actual
            - semanal:   ultimos 7 dias completos hasta hoy
            - mensual:   desde el primer dia del mes actual hasta hoy
            - semestral: desde hace 6 meses hasta hoy

        Parametros:
            periodicidad (str): 'diario' | 'semanal' | 'mensual' | 'semestral'

        Retorna:
            tuple: (fecha_desde: datetime, fecha_hasta: datetime)
        """
        ahora = datetime.utcnow()

        if periodicidad == 'diario':
            fecha_desde = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
            fecha_hasta = ahora

        elif periodicidad == 'semanal':
            fecha_desde = (ahora - timedelta(days=7)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            fecha_hasta = ahora

        elif periodicidad == 'mensual':
            fecha_desde = ahora.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            fecha_hasta = ahora

        elif periodicidad == 'semestral':
            mes = ahora.month - 6
            anio = ahora.year
            if mes <= 0:
                mes += 12
                anio -= 1
            fecha_desde = ahora.replace(
                year=anio, month=mes, day=1,
                hour=0, minute=0, second=0, microsecond=0
            )
            fecha_hasta = ahora

        elif periodicidad == 'anual':
            fecha_desde = ahora.replace(
                month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
            fecha_hasta = ahora

        else:
            # Por defecto: mensual
            fecha_desde = ahora.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            fecha_hasta = ahora

        return fecha_desde, fecha_hasta

    # -------------------------------------------------------------------------
    # METODO PRINCIPAL: REPORTE GENERAL
    # -------------------------------------------------------------------------
    @classmethod
    def generar_reporte_general(cls, periodicidad, anio_cursa=None):
        """
        Genera los datos del reporte general de evaluaciones.

        Incluye:
        - Total de evaluaciones y puntaje promedio en el periodo
        - Distribucion porcentual por nivel de riesgo
        - Desglose por carrera (promedio, count)
        - Desglose por compania (promedio, count)

        Parametros:
            periodicidad (str): Periodo del reporte ('diario', 'semanal', etc.)
            anio_cursa (int|None): Filtrar solo discentes de ese anio (1-6)

        Retorna:
            dict: Datos estructurados para renderizar en el template
        """
        fecha_desde, fecha_hasta = cls.calcular_rango_fechas(periodicidad)

        # Construir query base: evaluaciones en el rango, uniendo con usuario
        query = Evaluacion.query.join(
            Usuario, Evaluacion.usuario_id == Usuario.id
        ).filter(
            Evaluacion.fecha_evaluacion >= fecha_desde,
            Evaluacion.fecha_evaluacion <= fecha_hasta
        )

        # Filtro adicional por anio que cursa
        if anio_cursa:
            query = query.filter(Usuario.anio_cursa == anio_cursa)

        evaluaciones = query.all()
        total = len(evaluaciones)

        # Puntaje promedio
        puntaje_promedio = 0.0
        if total > 0:
            puntaje_promedio = round(
                sum(e.puntaje_total for e in evaluaciones) / total, 1
            )

        # Cuantas tuvieron alerta por pregunta critica
        con_alerta_critica = sum(
            1 for e in evaluaciones if e.alerta_pregunta_critica
        )

        # Distribucion por nivel de riesgo
        distribucion_riesgo = cls._calcular_distribucion_riesgo(evaluaciones, total)

        # Desglose por carrera
        desglose_carrera = cls._desglosar_por_campo(
            evaluaciones, 'carrera', Usuario.CARRERAS
        )

        # Desglose por compania
        desglose_compania = cls._desglosar_por_campo(
            evaluaciones, 'compania', Usuario.COMPANIAS
        )

        return {
            'periodo': {
                'periodicidad': periodicidad,
                'etiqueta': cls.ETIQUETAS_PERIODICIDAD.get(periodicidad, periodicidad),
                'fecha_desde': fecha_desde,
                'fecha_hasta': fecha_hasta,
                'anio_cursa': anio_cursa,
            },
            'totales': {
                'evaluaciones': total,
                'puntaje_promedio': puntaje_promedio,
                'con_alerta_critica': con_alerta_critica,
                'porcentaje_critica': round(con_alerta_critica / total * 100, 1) if total > 0 else 0,
            },
            'distribucion_riesgo': distribucion_riesgo,
            'desglose_carrera': desglose_carrera,
            'desglose_compania': desglose_compania,
        }

    # -------------------------------------------------------------------------
    # METODO AUXILIAR: DISTRIBUCION DE RIESGO
    # -------------------------------------------------------------------------
    @classmethod
    def _calcular_distribucion_riesgo(cls, evaluaciones, total):
        """
        Calcula la distribucion de evaluaciones por nivel de riesgo.

        Parametros:
            evaluaciones (list): Lista de objetos Evaluacion
            total (int): Total de evaluaciones (para calcular porcentaje)

        Retorna:
            list: Lista de dicts con nivel, etiqueta, count, porcentaje
        """
        conteo = {}
        for e in evaluaciones:
            conteo[e.nivel_riesgo] = conteo.get(e.nivel_riesgo, 0) + 1

        resultado = []
        for nivel in cls.NIVELES_ORDEN:
            count = conteo.get(nivel, 0)
            if count > 0:
                resultado.append({
                    'nivel': nivel,
                    'etiqueta': cls.ETIQUETAS_RIESGO.get(nivel, nivel),
                    'count': count,
                    'porcentaje': round(count / total * 100, 1) if total > 0 else 0,
                })

        return resultado

    # -------------------------------------------------------------------------
    # METODO AUXILIAR: DESGLOSE POR CAMPO DE USUARIO
    # -------------------------------------------------------------------------
    @classmethod
    def _desglosar_por_campo(cls, evaluaciones, campo, opciones_lista):
        """
        Agrupa las evaluaciones por un campo del usuario (carrera o compania).

        Parametros:
            evaluaciones (list): Lista de objetos Evaluacion (con usuario cargado)
            campo (str): Nombre del campo del modelo Usuario ('carrera' o 'compania')
            opciones_lista (list): Lista de (codigo, nombre) del modelo Usuario

        Retorna:
            list: Ordenada por cantidad de evaluaciones descendente, con:
                  codigo, etiqueta, count, promedio_puntaje, riesgo_dominante
        """
        acumulado = {}  # {codigo: {count, suma_puntaje, riesgo: {nivel: count}}}

        for e in evaluaciones:
            valor = getattr(e.usuario, campo) or 'sin_dato'
            if valor not in acumulado:
                acumulado[valor] = {'count': 0, 'suma_puntaje': 0, 'riesgo': {}}
            acumulado[valor]['count'] += 1
            acumulado[valor]['suma_puntaje'] += e.puntaje_total
            nivel = e.nivel_riesgo
            acumulado[valor]['riesgo'][nivel] = acumulado[valor]['riesgo'].get(nivel, 0) + 1

        etiquetas = {codigo: nombre for codigo, nombre in opciones_lista}

        resultado = []
        for codigo, datos in acumulado.items():
            count = datos['count']
            # Nivel de riesgo mas frecuente en este grupo
            riesgo_dom = max(datos['riesgo'], key=datos['riesgo'].get) if datos['riesgo'] else 'minimo'
            resultado.append({
                'codigo': codigo,
                'etiqueta': etiquetas.get(codigo, codigo.replace('_', ' ').title()),
                'count': count,
                'promedio': round(datos['suma_puntaje'] / count, 1) if count > 0 else 0,
                'riesgo_dominante': riesgo_dom,
                'etiqueta_riesgo': cls.ETIQUETAS_RIESGO.get(riesgo_dom, riesgo_dom),
            })

        resultado.sort(key=lambda x: x['count'], reverse=True)
        return resultado

    # -------------------------------------------------------------------------
    # METODO PRINCIPAL: REPORTE UNIFICADO
    # -------------------------------------------------------------------------
    @classmethod
    def generar_reporte_unificado(cls, periodicidad, anio_cursa=None, usuario_ids=None):
        """
        Genera el reporte unificado de monitoreo psicologico.

        Incluye:
        - Cuestionarios realizados en el periodo con conteo
        - Lista de discentes con sus evaluaciones agrupadas por cuestionario
        - Indicador de atencion psicologica requerida por discente
        - Alertas generadas en el periodo con estado y notas

        Umbral de atencion psicologica: nivel_riesgo NOT IN ('minimo', 'bajo')

        Parametros:
            periodicidad (str): Periodo del reporte ('diario', 'semanal', etc.)
            anio_cursa (int|None): Filtrar solo discentes de ese anio (1-6)

        Retorna:
            dict: Datos estructurados para renderizar el PDF
        """
        from app.models.cuestionario import Cuestionario  # noqa: PLC0415

        fecha_desde, fecha_hasta = cls.calcular_rango_fechas(periodicidad)

        # Niveles que indican necesidad de atencion psicologica
        NIVELES_REQUIEREN_ATENCION = {
            'leve', 'riesgo', 'moderado', 'perjudicial',
            'moderado_severo', 'alto', 'posible_dependencia', 'severo'
        }

        # 1. Evaluaciones en el periodo
        query_eval = Evaluacion.query.join(
            Usuario, Evaluacion.usuario_id == Usuario.id
        ).filter(
            Evaluacion.fecha_evaluacion >= fecha_desde,
            Evaluacion.fecha_evaluacion <= fecha_hasta,
        )
        if anio_cursa:
            query_eval = query_eval.filter(Usuario.anio_cursa == anio_cursa)
        if usuario_ids is not None:
            query_eval = query_eval.filter(Evaluacion.usuario_id.in_(usuario_ids))
        evaluaciones = query_eval.order_by(Evaluacion.fecha_evaluacion.asc()).all()

        # 2. Cuestionarios utilizados en el periodo
        cuestionario_ids = list({e.cuestionario_id for e in evaluaciones})
        cuestionarios_en_periodo = (
            Cuestionario.query.filter(Cuestionario.id.in_(cuestionario_ids)).all()
            if cuestionario_ids else []
        )
        mapa_cuestionarios = {c.id: c for c in cuestionarios_en_periodo}

        conteo_por_cuestionario = {}
        for e in evaluaciones:
            conteo_por_cuestionario[e.cuestionario_id] = (
                conteo_por_cuestionario.get(e.cuestionario_id, 0) + 1
            )

        cuestionarios_resumen = sorted(
            [
                {
                    'cuestionario': mapa_cuestionarios[cid],
                    'total_evaluaciones': conteo,
                }
                for cid, conteo in conteo_por_cuestionario.items()
            ],
            key=lambda x: x['cuestionario'].codigo,
        )

        # 3. Agrupar evaluaciones por discente y luego por cuestionario
        discentes_dict = {}
        for e in evaluaciones:
            uid = e.usuario_id
            if uid not in discentes_dict:
                discentes_dict[uid] = {
                    'usuario': e.usuario,
                    'evals_list': [],
                    'evals_por_cuestionario': {},
                }
            discentes_dict[uid]['evals_list'].append(e)

            cid = e.cuestionario_id
            if cid not in discentes_dict[uid]['evals_por_cuestionario']:
                discentes_dict[uid]['evals_por_cuestionario'][cid] = {
                    'cuestionario': mapa_cuestionarios[cid],
                    'evaluaciones': [],
                }
            discentes_dict[uid]['evals_por_cuestionario'][cid]['evaluaciones'].append({
                'evaluacion': e,
                'necesita_atencion': e.nivel_riesgo in NIVELES_REQUIEREN_ATENCION,
                'etiqueta_riesgo': cls.ETIQUETAS_RIESGO.get(e.nivel_riesgo, e.nivel_riesgo),
            })

        discentes_data = []
        for data in discentes_dict.values():
            usuario = data['usuario']
            evals_lista = sorted(
                data['evals_por_cuestionario'].values(),
                key=lambda x: x['cuestionario'].codigo,
            )
            necesita_atencion = any(
                e.nivel_riesgo in NIVELES_REQUIEREN_ATENCION
                for e in data['evals_list']
            )
            discentes_data.append({
                'usuario': usuario,
                'evaluaciones_por_cuestionario': evals_lista,
                'necesita_atencion': necesita_atencion,
            })

        discentes_data.sort(
            key=lambda x: (x['usuario'].apellido_paterno or '', x['usuario'].nombre or '')
        )

        # 4. Alertas en el periodo
        query_alertas = Alerta.query.join(
            Usuario, Alerta.usuario_id == Usuario.id
        ).filter(
            Alerta.created_at >= fecha_desde,
            Alerta.created_at <= fecha_hasta,
        )
        if anio_cursa:
            query_alertas = query_alertas.filter(Usuario.anio_cursa == anio_cursa)
        if usuario_ids is not None:
            query_alertas = query_alertas.filter(Alerta.usuario_id.in_(usuario_ids))
        alertas = query_alertas.all()

        orden_prioridad = {'critica': 0, 'alta': 1, 'media': 2, 'baja': 3}
        alertas.sort(key=lambda a: orden_prioridad.get(a.prioridad, 4))

        return {
            'periodo': {
                'periodicidad': periodicidad,
                'etiqueta': cls.ETIQUETAS_PERIODICIDAD.get(periodicidad, periodicidad),
                'fecha_desde': fecha_desde,
                'fecha_hasta': fecha_hasta,
                'anio_cursa': anio_cursa,
                'fecha_generacion': datetime.utcnow(),
            },
            'cuestionarios_resumen': cuestionarios_resumen,
            'discentes': discentes_data,
            'alertas': alertas,
            'total_evaluaciones': len(evaluaciones),
            'total_discentes': len(discentes_data),
            'total_alertas': len(alertas),
        }

    # -------------------------------------------------------------------------
    # METODO PRINCIPAL: REPORTE DE ALERTAS
    # -------------------------------------------------------------------------
    @classmethod
    def generar_reporte_alertas(cls, periodicidad, anio_cursa=None):
        """
        Genera los datos del reporte de alertas.

        Incluye:
        - Total de alertas en el periodo
        - Conteo por prioridad (critica, alta, media, baja)
        - Conteo por estado (pendiente, en_revision, atendida)
        - Matriz cruzada: prioridad x estado

        Parametros:
            periodicidad (str): Periodo del reporte
            anio_cursa (int|None): Filtrar alertas de discentes en ese anio

        Retorna:
            dict: Datos estructurados para el template
        """
        fecha_desde, fecha_hasta = cls.calcular_rango_fechas(periodicidad)

        query = Alerta.query.join(
            Usuario, Alerta.usuario_id == Usuario.id
        ).filter(
            Alerta.created_at >= fecha_desde,
            Alerta.created_at <= fecha_hasta
        )

        if anio_cursa:
            query = query.filter(Usuario.anio_cursa == anio_cursa)

        alertas = query.all()
        total = len(alertas)

        # Conteo por prioridad
        prioridades = ['critica', 'alta', 'media', 'baja']
        conteo_prioridad = {p: 0 for p in prioridades}
        for a in alertas:
            if a.prioridad in conteo_prioridad:
                conteo_prioridad[a.prioridad] += 1

        # Conteo por estado
        estados = ['pendiente', 'en_revision', 'atendida']
        conteo_estado = {e: 0 for e in estados}
        for a in alertas:
            if a.estado in conteo_estado:
                conteo_estado[a.estado] += 1

        # Matriz cruzada prioridad x estado
        matriz = {
            p: {e: 0 for e in estados}
            for p in prioridades
        }
        for a in alertas:
            if a.prioridad in matriz and a.estado in matriz[a.prioridad]:
                matriz[a.prioridad][a.estado] += 1

        # Porcentajes por prioridad
        porcentajes_prioridad = {
            p: round(c / total * 100, 1) if total > 0 else 0
            for p, c in conteo_prioridad.items()
        }

        # Porcentajes por estado
        porcentajes_estado = {
            e: round(c / total * 100, 1) if total > 0 else 0
            for e, c in conteo_estado.items()
        }

        return {
            'periodo': {
                'periodicidad': periodicidad,
                'etiqueta': cls.ETIQUETAS_PERIODICIDAD.get(periodicidad, periodicidad),
                'fecha_desde': fecha_desde,
                'fecha_hasta': fecha_hasta,
                'anio_cursa': anio_cursa,
            },
            'total': total,
            'conteo_prioridad': conteo_prioridad,
            'porcentajes_prioridad': porcentajes_prioridad,
            'conteo_estado': conteo_estado,
            'porcentajes_estado': porcentajes_estado,
            'matriz': matriz,
            'prioridades': prioridades,
            'estados': estados,
        }
