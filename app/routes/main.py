"""
================================================================================
MENTIS CURA - Rutas Principales
================================================================================
Archivo: routes/main.py
Descripcion: Define las rutas principales de la aplicacion.
             Incluye la pagina de inicio y dashboards segun rol.

Rutas disponibles:
    - /: Redireccion inicial (a login o inicio segun autenticacion)
    - /inicio: Dashboard principal (varia segun rol del usuario)

Dashboards por rol:
    - Discente: Ve sus cuestionarios disponibles e historial
    - Orientador: Ve alertas pendientes y estadisticas
    - Administrador: Ve alertas pendientes y estadisticas

Autor: Proyecto de Tesis
Fecha: 2024
================================================================================
"""

# =============================================================================
# IMPORTACIONES
# =============================================================================
# Flask: Funciones para manejo de rutas web
from flask import Blueprint, render_template, redirect, url_for

# Flask-Login: Verificacion de autenticacion y acceso al usuario actual
from flask_login import login_required, current_user

# Modelos y servicios del proyecto
from app.models.cuestionario import Cuestionario
from app.services.evaluacion_service import EvaluacionService
from app.services.alerta_service import AlertaService


# =============================================================================
# CREAR BLUEPRINT
# =============================================================================
# Blueprint 'main' para las rutas principales
main_bp = Blueprint('main', __name__)


# =============================================================================
# RUTA: INDEX (Pagina raiz)
# =============================================================================
@main_bp.route('/')
def index():
    """
    Pagina de bienvenida / redireccion inicial.

    Esta es la primera pagina que ve un usuario al acceder al sistema.
    Simplemente redirige a otra pagina segun el estado de autenticacion:

    - Si esta autenticado: va al dashboard (/inicio)
    - Si no esta autenticado: va al login

    Retorna:
        Redireccion a /inicio o /login
    """
    if current_user.is_authenticated:
        # Usuario ya logueado, ir al dashboard
        return redirect(url_for('main.inicio'))
    # No logueado, ir al login
    return redirect(url_for('auth.login'))


# =============================================================================
# RUTA: INICIO (Dashboard principal)
# =============================================================================
@main_bp.route('/inicio')
@login_required  # Requiere que el usuario este autenticado
def inicio():
    """
    Dashboard principal de la aplicacion.

    Muestra contenido diferente segun el rol del usuario:

    Para DISCENTES:
        - Lista de cuestionarios disponibles
        - Historial de sus ultimas 5 evaluaciones
        - Estadisticas personales (total evaluaciones, promedio, etc.)

    Para ORIENTADORES y ADMINISTRADORES:
        - Estadisticas de alertas (pendientes, criticas, etc.)
        - Lista de las 5 alertas mas recientes
        - Acceso rapido a cuestionarios

    Retorna:
        Pagina HTML del dashboard correspondiente al rol
    """
    # -------------------------------------------------------------------------
    # Obtener cuestionarios disponibles (para todos los roles)
    # -------------------------------------------------------------------------
    # Solo cuestionarios activos
    cuestionarios = Cuestionario.query.filter_by(activo=True).all()

    # -------------------------------------------------------------------------
    # Dashboard para DISCENTES
    # -------------------------------------------------------------------------
    if current_user.es_discente():
        # Obtener historial de evaluaciones del discente (ultimas 5)
        historial = EvaluacionService.obtener_historial_usuario(
            current_user.id,
            limite=5
        )

        # Obtener estadisticas del discente
        estadisticas = EvaluacionService.obtener_estadisticas_usuario(
            current_user.id
        )

        # Mostrar dashboard de discente
        return render_template('main/inicio_discente.html',
                               cuestionarios=cuestionarios,
                               historial=historial,
                               estadisticas=estadisticas)

    # -------------------------------------------------------------------------
    # Dashboard para ORIENTADORES y ADMINISTRADORES
    # -------------------------------------------------------------------------
    elif current_user.puede_ver_alertas():
        # Obtener estadisticas de alertas
        alertas_stats = AlertaService.obtener_estadisticas()

        # Obtener las 5 alertas pendientes mas recientes
        alertas_recientes = AlertaService.obtener_alertas_pendientes(
            {'estado': 'pendiente'}
        )[:5]  # Solo las primeras 5

        # Mostrar dashboard de orientador
        return render_template('main/inicio_orientador.html',
                               alertas_stats=alertas_stats,
                               alertas_recientes=alertas_recientes,
                               cuestionarios=cuestionarios)

    # -------------------------------------------------------------------------
    # Dashboard generico (por si acaso)
    # -------------------------------------------------------------------------
    return render_template('main/inicio.html', cuestionarios=cuestionarios)
