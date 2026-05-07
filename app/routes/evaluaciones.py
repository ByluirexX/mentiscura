"""
================================================================================
MENTIS CURA - Rutas de Evaluaciones
================================================================================
Archivo: routes/evaluaciones.py
Descripcion: Define las rutas para visualizar evaluaciones y resultados.
             Permite ver el resultado de una evaluacion especifica y
             consultar el historial de evaluaciones.

Rutas disponibles:
    - /evaluaciones/resultado/<id>: Ver resultado de una evaluacion
    - /evaluaciones/historial: Ver historial del usuario actual
    - /evaluaciones/usuario/<id>: Ver historial de un discente (solo orientador)

Control de acceso:
    - Los discentes solo pueden ver sus propias evaluaciones
    - Los orientadores y admins pueden ver evaluaciones de cualquier discente

Autor: Proyecto de Tesis
Fecha: 2024
================================================================================
"""

# =============================================================================
# IMPORTACIONES
# =============================================================================
# Flask: Funciones para manejo de rutas web
import os
from io import BytesIO

from flask import (Blueprint, current_app, make_response, render_template,
                   redirect, url_for, flash)

# Flask-Login: Verificacion de autenticacion y acceso al usuario actual
from flask_login import login_required, current_user

# Modelos y servicios del proyecto
from app.models.evaluacion import Evaluacion, PuntajeSustancia
from app.models.cuestionario import Pregunta
from app.models.usuario import Usuario
from app.models.solicitud_ayuda import SolicitudAyuda
from app.services.evaluacion_service import EvaluacionService

# Decorador para restringir acceso a orientadores
from app.utils.decorators import solo_orientador


# =============================================================================
# CREAR BLUEPRINT
# =============================================================================
evaluaciones_bp = Blueprint('evaluaciones', __name__)


def _pdf_link_callback(uri, rel):
    """Resuelve rutas /static/... a rutas absolutas del filesystem para xhtml2pdf."""
    if uri.startswith('/static/'):
        return os.path.join(current_app.static_folder, uri[len('/static/'):])
    return uri


# =============================================================================
# RUTA: VER RESULTADO DE EVALUACION
# =============================================================================
@evaluaciones_bp.route('/resultado/<int:evaluacion_id>')
@login_required
def resultado(evaluacion_id):
    """
    Muestra el resultado detallado de una evaluacion especifica.

    Presenta:
    - Puntaje total obtenido
    - Nivel de riesgo clasificado
    - Indicador de alerta critica (si aplica)
    - Detalle de cada pregunta con su respuesta

    Control de acceso:
    - El usuario puede ver sus propias evaluaciones
    - Orientadores y admins pueden ver cualquier evaluacion

    Parametros de URL:
        evaluacion_id (int): ID de la evaluacion a mostrar

    Retorna:
        Pagina HTML con el resultado detallado
        O redireccion al inicio si no tiene permiso
    """
    # -------------------------------------------------------------------------
    # Obtener la evaluacion o mostrar error 404
    # -------------------------------------------------------------------------
    evaluacion = Evaluacion.query.get_or_404(evaluacion_id)

    # -------------------------------------------------------------------------
    # Verificar permisos de acceso
    # -------------------------------------------------------------------------
    # El usuario puede ver su propia evaluacion
    # O si es orientador/admin puede ver cualquiera
    if evaluacion.usuario_id != current_user.id and not current_user.puede_ver_alertas():
        flash('No tiene permisos para ver esta evaluación.', 'danger')
        return redirect(url_for('main.inicio'))

    # -------------------------------------------------------------------------
    # Obtener las respuestas ordenadas
    # -------------------------------------------------------------------------
    respuestas = evaluacion.obtener_respuestas_ordenadas()

    # Solo orientadores y admins pueden ver el detalle de respuestas
    puede_ver_respuestas = current_user.puede_ver_alertas()

    # Template especifico para ASSIST
    if evaluacion.cuestionario.codigo == 'ASSIST':
        puntajes = PuntajeSustancia.query.filter_by(evaluacion_id=evaluacion.id).all()
        return render_template('evaluaciones/resultado_assist.html',
                               evaluacion=evaluacion,
                               respuestas=respuestas,
                               puntajes_sustancia=puntajes,
                               puede_ver_respuestas=puede_ver_respuestas)

    # Mostrar la pagina de resultado
    return render_template('evaluaciones/resultado.html',
                           evaluacion=evaluacion,
                           respuestas=respuestas,
                           puede_ver_respuestas=puede_ver_respuestas)


# =============================================================================
# RUTA: HISTORIAL DEL USUARIO ACTUAL
# =============================================================================
@evaluaciones_bp.route('/historial')
@login_required
def historial():
    """
    Muestra el historial de evaluaciones del usuario actual.

    Presenta:
    - Lista de todas las evaluaciones realizadas (hasta 50)
    - Fecha, cuestionario, puntaje y nivel de riesgo de cada una
    - Estadisticas generales (total, promedio, alertas criticas)

    Retorna:
        Pagina HTML con el historial de evaluaciones
    """
    # Obtener historial del usuario actual (maximo 50 evaluaciones)
    historial = EvaluacionService.obtener_historial_usuario(
        current_user.id,
        limite=50
    )

    # Obtener estadisticas del usuario
    estadisticas = EvaluacionService.obtener_estadisticas_usuario(
        current_user.id
    )

    solicitudes = (SolicitudAyuda.query
                   .filter_by(usuario_id=current_user.id)
                   .order_by(SolicitudAyuda.created_at.desc())
                   .all())

    # Mostrar la pagina de historial
    return render_template('evaluaciones/historial.html',
                           historial=historial,
                           estadisticas=estadisticas,
                           solicitudes=solicitudes)


# =============================================================================
# RUTA: HISTORIAL DE UN DISCENTE ESPECIFICO
# =============================================================================
@evaluaciones_bp.route('/usuario/<int:usuario_id>')
@login_required
@solo_orientador  # Solo orientadores y admins pueden acceder
def historial_usuario(usuario_id):
    """
    Muestra el historial de evaluaciones de un discente especifico.

    Esta ruta es solo para orientadores y administradores.
    Permite consultar el historial completo de un discente.

    Parametros de URL:
        usuario_id (int): ID del discente a consultar

    Presenta:
    - Datos del discente (nombre, matricula, carrera, etc.)
    - Lista de todas sus evaluaciones
    - Estadisticas de sus evaluaciones

    Retorna:
        Pagina HTML con el historial del discente
        O error 404 si el usuario no existe
    """
    # -------------------------------------------------------------------------
    # Obtener el usuario o mostrar error 404
    # -------------------------------------------------------------------------
    usuario = Usuario.query.get_or_404(usuario_id)

    # -------------------------------------------------------------------------
    # Obtener historial y estadisticas
    # -------------------------------------------------------------------------
    historial = EvaluacionService.obtener_historial_usuario(
        usuario_id,
        limite=50
    )

    estadisticas = EvaluacionService.obtener_estadisticas_usuario(usuario_id)

    solicitudes = (SolicitudAyuda.query
                   .filter_by(usuario_id=usuario_id)
                   .order_by(SolicitudAyuda.created_at.desc())
                   .all())

    # Mostrar la pagina de historial del usuario
    return render_template('evaluaciones/historial_usuario.html',
                           usuario=usuario,
                           historial=historial,
                           estadisticas=estadisticas,
                           solicitudes=solicitudes)


# =============================================================================
# RUTA: IMPRIMIR TAMIZAJE COMPLETO
# =============================================================================
@evaluaciones_bp.route('/imprimir/<int:evaluacion_id>')
@login_required
@solo_orientador
def imprimir_tamizaje(evaluacion_id):
    """
    Genera una vista imprimible del tamizaje completo para orientadores/admins.

    Muestra:
    - Datos personales del discente
    - Cada pregunta con todas sus opciones y la respuesta seleccionada marcada
    - Guia de calculo del puntaje total
    - Escala de riesgo de referencia

    Parametros de URL:
        evaluacion_id (int): ID de la evaluacion a imprimir

    Retorna:
        Pagina HTML optimizada para impresion
    """
    evaluacion = Evaluacion.query.get_or_404(evaluacion_id)

    preguntas = Pregunta.query.filter_by(
        cuestionario_id=evaluacion.cuestionario_id
    ).order_by(Pregunta.orden).all()

    respuestas = evaluacion.obtener_respuestas_ordenadas()
    respuestas_dict = {r.pregunta_id: r.valor for r in respuestas}

    puntajes_sustancia = None
    if evaluacion.cuestionario.codigo == 'ASSIST':
        puntajes_sustancia = PuntajeSustancia.query.filter_by(
            evaluacion_id=evaluacion.id
        ).all()

    html = render_template('evaluaciones/pdf_tamizaje.html',
                           evaluacion=evaluacion,
                           preguntas=preguntas,
                           respuestas_dict=respuestas_dict,
                           puntajes_sustancia=puntajes_sustancia)

    try:
        from xhtml2pdf import pisa  # noqa: PLC0415

        pdf_buffer = BytesIO()
        resultado = pisa.CreatePDF(
            html.encode('utf-8'),
            dest=pdf_buffer,
            encoding='utf-8',
            link_callback=_pdf_link_callback
        )

        if resultado.err:
            flash('Error al generar el PDF. Intente nuevamente.', 'danger')
            return redirect(url_for('evaluaciones.resultado', evaluacion_id=evaluacion_id))

        pdf_buffer.seek(0)
        matricula = evaluacion.usuario.matricula or str(evaluacion.usuario_id)
        codigo = evaluacion.cuestionario.codigo
        fecha = evaluacion.fecha_evaluacion.strftime('%Y%m%d')
        nombre_archivo = f'tamizaje_{codigo}_{matricula}_{fecha}.pdf'

        response = make_response(pdf_buffer.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename={nombre_archivo}'
        return response

    except ImportError:
        flash('La librería xhtml2pdf no está instalada. Ejecute: pip install xhtml2pdf', 'danger')
        return redirect(url_for('evaluaciones.resultado', evaluacion_id=evaluacion_id))
