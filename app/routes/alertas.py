"""
================================================================================
MENTIS CURA - Rutas de Alertas
================================================================================
Archivo: routes/alertas.py
Descripcion: Define las rutas para el modulo de alertas.
             Permite a orientadores y administradores ver y atender alertas.

Rutas disponibles:
    - /alertas/: Lista de alertas (con filtros)
    - /alertas/<id>: Ver detalle de una alerta
    - /alertas/<id>/atender: Marcar alerta como atendida
    - /alertas/<id>/en-revision: Marcar alerta en revision
    - /alertas/discentes: Lista de discentes para busqueda

IMPORTANTE: Todas las rutas de este modulo son solo para
orientadores y administradores. Los discentes no tienen acceso.

Control de acceso:
    - Solo usuarios con rol 'orientador' o 'administrador'

Autor: Proyecto de Tesis
Fecha: 2024
================================================================================
"""

# =============================================================================
# IMPORTACIONES
# =============================================================================
# Flask: Funciones para manejo de rutas web
from flask import Blueprint, render_template, redirect, url_for, flash, request

# Flask-Login: Verificacion de autenticacion y acceso al usuario actual
from flask_login import login_required, current_user

# Importaciones del proyecto
from app import db  # Base de datos
from app.models.alerta import Alerta  # Modelo de alertas
from app.models.usuario import Usuario  # Modelo de usuarios
from app.models.solicitud_ayuda import SolicitudAyuda  # Solicitudes de ayuda
from app.services.alerta_service import AlertaService  # Servicio de alertas

# Decorador para restringir acceso solo a orientadores/admins
from app.utils.decorators import solo_orientador


# =============================================================================
# CREAR BLUEPRINT
# =============================================================================
# Blueprint 'alertas' con prefijo de URL /alertas
alertas_bp = Blueprint('alertas', __name__)


# =============================================================================
# RUTA: LISTADO DE ALERTAS
# =============================================================================
@alertas_bp.route('/')
@login_required
@solo_orientador  # Solo orientadores y administradores pueden acceder
def listado():
    """
    Lista todas las alertas del sistema con filtros opcionales.

    Los filtros disponibles son:
    - estado: 'pendiente', 'en_revision', 'atendida'
    - prioridad: 'baja', 'media', 'alta', 'critica'

    Por defecto muestra las alertas pendientes ordenadas por:
    1. Prioridad (criticas primero)
    2. Fecha (mas recientes primero)

    Retorna:
        Pagina HTML con la lista de alertas filtradas
    """
    # -------------------------------------------------------------------------
    # Obtener filtros de los parametros de URL
    # -------------------------------------------------------------------------
    # Si no se especifica estado, mostrar solo pendientes
    estado = request.args.get('estado', 'pendiente')
    prioridad = request.args.get('prioridad', '')

    # -------------------------------------------------------------------------
    # Construir diccionario de filtros para el servicio
    # -------------------------------------------------------------------------
    filtros = {}
    if estado:
        filtros['estado'] = estado
    if prioridad:
        filtros['prioridad'] = prioridad

    # -------------------------------------------------------------------------
    # Obtener alertas y estadisticas
    # -------------------------------------------------------------------------
    alertas = AlertaService.obtener_alertas_pendientes(filtros)
    estadisticas = AlertaService.obtener_estadisticas()

    solicitudes_no_leidas = (SolicitudAyuda.query
                             .filter_by(leida=False)
                             .order_by(SolicitudAyuda.created_at.desc())
                             .all())

    # Mostrar la pagina de listado
    return render_template('alertas/listado.html',
                           alertas=alertas,
                           estadisticas=estadisticas,
                           filtro_estado=estado,
                           filtro_prioridad=prioridad,
                           solicitudes_no_leidas=solicitudes_no_leidas)


# =============================================================================
# RUTA: VER DETALLE DE ALERTA
# =============================================================================
@alertas_bp.route('/<int:alerta_id>')
@login_required
@solo_orientador
def detalle(alerta_id):
    """
    Muestra el detalle completo de una alerta.

    Presenta:
    - Informacion del discente (nombre, matricula, carrera)
    - Tipo y prioridad de la alerta
    - Mensaje descriptivo
    - Estado actual y quien la atendio (si aplica)
    - Enlace a la evaluacion que genero la alerta

    Parametros de URL:
        alerta_id (int): ID de la alerta a ver

    Retorna:
        Pagina HTML con el detalle de la alerta
        O error 404 si no existe
    """
    # Obtener la alerta o mostrar error 404
    alerta = Alerta.query.get_or_404(alerta_id)

    # Mostrar la pagina de detalle
    return render_template('alertas/detalle.html', alerta=alerta)


# =============================================================================
# RUTA: ATENDER ALERTA
# =============================================================================
@alertas_bp.route('/<int:alerta_id>/atender', methods=['POST'])
@login_required
@solo_orientador
def atender(alerta_id):
    """
    Marca una alerta como atendida.

    Esta accion registra:
    - Quien atendio la alerta (orientador/admin actual)
    - Cuando la atendio
    - Las notas de atencion proporcionadas

    Datos del formulario:
        notas: Texto con las notas sobre la atencion brindada

    Parametros de URL:
        alerta_id (int): ID de la alerta a atender

    Retorna:
        Redireccion al listado de alertas con mensaje de confirmacion
    """
    # Obtener la alerta o mostrar error 404
    alerta = Alerta.query.get_or_404(alerta_id)

    # Obtener las notas del formulario (limpiar espacios)
    notas = request.form.get('notas', '').strip()

    # -------------------------------------------------------------------------
    # Marcar la alerta como atendida usando el servicio
    # -------------------------------------------------------------------------
    alerta = AlertaService.marcar_alerta_atendida(alerta_id, current_user.id, notas)

    if alerta:
        flash('Alerta marcada como atendida.', 'success')
    else:
        flash('Error al actualizar la alerta.', 'danger')

    # Redirigir al listado de alertas
    return redirect(url_for('alertas.listado'))


# =============================================================================
# RUTA: MARCAR EN REVISION
# =============================================================================
@alertas_bp.route('/<int:alerta_id>/en-revision', methods=['POST'])
@login_required
@solo_orientador
def en_revision(alerta_id):
    """
    Marca una alerta como "en revision".

    Se usa cuando un orientador comienza a revisar una alerta
    pero aun no la ha cerrado. Esto indica a otros orientadores
    que alguien ya esta trabajando en el caso.

    Parametros de URL:
        alerta_id (int): ID de la alerta

    Retorna:
        Redireccion a la pagina de detalle de la alerta
    """
    # Obtener la alerta o mostrar error 404
    alerta = Alerta.query.get_or_404(alerta_id)

    # Marcar como en revision (usando el metodo del modelo)
    alerta.marcar_en_revision(current_user.id)
    db.session.commit()

    # Mostrar mensaje informativo
    flash('Alerta marcada como en revisión.', 'info')

    # Redirigir al detalle de la alerta
    return redirect(url_for('alertas.detalle', alerta_id=alerta_id))


# =============================================================================
# RUTA: LISTADO DE DISCENTES
# =============================================================================
@alertas_bp.route('/discentes')
@login_required
@solo_orientador
def listado_discentes():
    """
    Lista todos los discentes registrados para busqueda.

    Permite a los orientadores buscar discentes por:
    - Nombre
    - Matricula
    - Compania

    Esta ruta es util para:
    - Consultar el historial de un discente especifico
    - Verificar si un discente ha respondido cuestionarios
    - Buscar discentes por diferentes criterios

    La busqueda se realiza en el cliente con JavaScript
    para una experiencia mas fluida.

    Retorna:
        Pagina HTML con la lista de discentes y buscador
    """
    # Obtener todos los discentes (usuarios con rol 'discente')
    # Usando join para filtrar por el nombre del rol
    discentes = Usuario.query.join(Usuario.rol).filter_by(nombre='discente').all()

    # Mostrar la pagina de listado de discentes
    return render_template('alertas/listado_discentes.html', discentes=discentes)
