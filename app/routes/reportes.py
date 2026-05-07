"""
================================================================================
MENTIS CURA - Rutas del Modulo de Reportes
================================================================================
Archivo: routes/reportes.py
Descripcion: Define las rutas para el modulo de reportes.
             Permite a orientadores y administradores filtrar y exportar
             el reporte unificado de monitoreo psicologico en PDF.

Rutas disponibles:
    - /reportes/     : Pagina principal (formulario de filtros)
    - /reportes/pdf  : Genera y descarga el reporte unificado en PDF

Control de acceso:
    - Solo orientadores y administradores pueden acceder a este modulo.

Autor: Proyecto de Tesis
Fecha: 2024
================================================================================
"""

# =============================================================================
# IMPORTACIONES
# =============================================================================
import os
from io import BytesIO

from flask import (Blueprint, current_app, flash, make_response, redirect,
                   render_template, request, url_for)
from flask_login import login_required
from sqlalchemy import or_

from app.models.usuario import Usuario
from app.services.reporte_service import ReporteService
from app.utils.decorators import solo_orientador


# =============================================================================
# CREAR BLUEPRINT
# =============================================================================
reportes_bp = Blueprint('reportes', __name__)


def _pdf_link_callback(uri, rel):
    """Resuelve rutas /static/... a rutas absolutas del sistema de archivos para xhtml2pdf."""
    if uri.startswith('/static/'):
        return os.path.join(current_app.static_folder, uri[len('/static/'):])
    return uri

# Opciones validas de periodicidad
PERIODICIDADES = [
    ('diario',    'Diario'),
    ('semanal',   'Semanal'),
    ('mensual',   'Mensual'),
    ('semestral', 'Semestral'),
    ('anual',     'Anual'),
]

# Opciones de anio que cursa (1 a 6)
ANIOS_CURSA = list(range(1, 7))


# =============================================================================
# RUTA: PAGINA PRINCIPAL DEL MODULO
# =============================================================================
@reportes_bp.route('/')
@login_required
@solo_orientador
def index():
    """
    Pagina principal del modulo de reportes.

    Si se recibe el parametro 'buscar', realiza una busqueda de discentes
    por nombre o matricula y muestra los resultados en la misma pagina.

    Parametros de URL (query string):
        buscar (str): Termino de busqueda para encontrar discentes. Opcional.

    Retorna:
        Pagina HTML con el formulario y, si aplica, los resultados de busqueda.
    """
    buscar = request.args.get('buscar', '').strip()
    discentes_encontrados = []

    if buscar:
        termino = f'%{buscar}%'
        discentes_encontrados = Usuario.query.filter(
            or_(
                Usuario.matricula.ilike(termino),
                Usuario.nombre.ilike(termino),
                Usuario.apellido_paterno.ilike(termino),
                Usuario.apellido_materno.ilike(termino),
            )
        ).order_by(Usuario.apellido_paterno, Usuario.nombre).all()

    return render_template(
        'reportes/index.html',
        periodicidades=PERIODICIDADES,
        anios_cursa=ANIOS_CURSA,
        buscar=buscar,
        discentes_encontrados=discentes_encontrados,
    )


# =============================================================================
# RUTA: EXPORTAR REPORTE UNIFICADO A PDF
# =============================================================================
@reportes_bp.route('/pdf')
@login_required
@solo_orientador
def pdf():
    """
    Genera y descarga el reporte unificado de monitoreo psicologico en PDF.

    Utiliza xhtml2pdf para convertir el template HTML a PDF.
    Si la libreria no esta instalada, muestra un mensaje de error.

    Parametros de URL (query string):
        periodicidad (str): Periodo del reporte. Por defecto 'mensual'.
        anio_cursa (int):   Filtrar por anio que cursa (1-6). Opcional.

    Retorna:
        Archivo PDF como descarga (Content-Disposition: attachment)
        O redireccion con mensaje de error si falta la libreria
    """
    periodicidad = request.args.get('periodicidad', 'mensual')
    anio_cursa = request.args.get('anio_cursa', type=int)
    usuario_id = request.args.get('usuario_id', type=int)

    if periodicidad not in [p[0] for p in PERIODICIDADES]:
        periodicidad = 'mensual'

    usuario_ids = [usuario_id] if usuario_id else None

    datos = ReporteService.generar_reporte_unificado(periodicidad, anio_cursa, usuario_ids=usuario_ids)
    html = render_template('reportes/pdf_unificado.html', datos=datos)

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
            return redirect(url_for('reportes.index'))

        pdf_buffer.seek(0)
        if usuario_id:
            discente = Usuario.query.get(usuario_id)
            matricula = discente.matricula if discente else str(usuario_id)
            nombre_archivo = f'reporte_{matricula}_{periodicidad}.pdf'
        else:
            nombre_archivo = f'reporte_monitoreo_{periodicidad}.pdf'

        response = make_response(pdf_buffer.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename={nombre_archivo}'
        return response

    except ImportError:
        flash(
            'La librería xhtml2pdf no está instalada. '
            'Ejecute: pip install xhtml2pdf',
            'danger'
        )
        return redirect(url_for('reportes.index'))
