"""
================================================================================
MENTIS CURA - Decoradores de Utilidad
================================================================================
Archivo: utils/decorators.py
Descripcion: Define decoradores personalizados para control de acceso.
             Los decoradores permiten restringir rutas segun el rol del usuario.

Que es un decorador?
    Un decorador es una funcion que envuelve a otra funcion para modificar
    su comportamiento. En Flask, se usan con el simbolo @ antes de una ruta.

    Ejemplo:
        @app.route('/admin')    # Decorador de Flask para definir URL
        @login_required         # Decorador para requerir autenticacion
        @solo_admin             # Nuestro decorador para requerir rol admin
        def panel_admin():
            return "Panel de admin"

Decoradores disponibles:
    - rol_requerido(*roles): Restringe a los roles especificados
    - solo_admin: Restringe acceso solo a administradores
    - solo_orientador: Restringe acceso a orientadores y administradores

Orden de los decoradores:
    Los decoradores se aplican de abajo hacia arriba. Ejemplo:

    @login_required    <- Se ejecuta PRIMERO (verifica que este logueado)
    @solo_admin        <- Se ejecuta DESPUES (verifica que sea admin)
    def mi_funcion():
        pass

Autor: Proyecto de Tesis
Fecha: 2024
================================================================================
"""

# =============================================================================
# IMPORTACIONES
# =============================================================================
# functools.wraps: Preserva los metadatos de la funcion original
# (nombre, documentacion, etc.) Esto es importante para que Flask
# pueda identificar correctamente la funcion decorada.
from functools import wraps

# Flask: Funciones para redireccion y mensajes
from flask import flash, redirect, url_for

# Flask-Login: Acceso al usuario actualmente autenticado
from flask_login import current_user


# =============================================================================
# DECORADOR GENERICO: ROL REQUERIDO
# =============================================================================
def rol_requerido(*roles):
    """
    Decorador generico para restringir acceso a roles especificos.

    Este decorador es flexible: permite especificar uno o mas roles
    que pueden acceder a la ruta.

    Parametros:
        *roles: Nombres de los roles permitidos (cadenas de texto)

    Uso:
        @rol_requerido('administrador')
        def solo_admin():
            ...

        @rol_requerido('administrador', 'orientador')
        def admin_o_orientador():
            ...

    Retorna:
        Decorador configurado con los roles especificados

    Nota: Este decorador asume que @login_required ya fue aplicado,
    pero verifica autenticacion por seguridad.
    """
    def decorator(f):
        """Funcion que recibe la funcion a decorar."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            """Funcion envuelta que verifica los permisos."""
            # Verificar que el usuario este autenticado
            # (por seguridad, aunque se espera que @login_required ya lo haga)
            if not current_user.is_authenticated:
                flash('Debe iniciar sesión para acceder.', 'warning')
                return redirect(url_for('auth.login'))

            # Verificar que el rol del usuario este en la lista permitida
            if current_user.rol.nombre not in roles:
                flash('No tiene permisos para acceder a esta sección.', 'danger')
                return redirect(url_for('main.inicio'))

            # Si tiene permiso, ejecutar la funcion original
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# =============================================================================
# DECORADOR: SOLO ORIENTADOR O ADMINISTRADOR
# =============================================================================
def solo_orientador(f):
    """
    Decorador que restringe el acceso a orientadores y administradores.

    Este decorador se usa en todas las rutas del modulo de alertas
    y otras funciones que solo deben ser accesibles por personal
    autorizado para ver informacion de salud mental.

    Los discentes NO pueden acceder a rutas protegidas con este decorador.
    Los administradores SI tienen acceso (tienen todos los permisos).

    IMPORTANTE: Este decorador debe usarse DESPUES de @login_required.

    Uso correcto:
        @app.route('/alertas/')
        @login_required        # PRIMERO: verificar autenticacion
        @solo_orientador       # DESPUES: verificar rol
        def listado_alertas():
            ...

    Uso incorrecto:
        @app.route('/alertas/')
        @solo_orientador       # ERROR: current_user puede no existir
        def listado_alertas():
            ...

    Retorna:
        La funcion envuelta con verificacion de permisos
    """
    @wraps(f)  # Preservar nombre y documentacion de la funcion original
    def decorated_function(*args, **kwargs):
        """Funcion envuelta que verifica permisos de orientador."""
        # Verificar autenticacion (seguridad adicional)
        if not current_user.is_authenticated:
            flash('Debe iniciar sesión para acceder.', 'warning')
            return redirect(url_for('auth.login'))

        # Verificar que pueda ver alertas (orientadores y admins)
        # El metodo puede_ver_alertas() esta definido en el modelo Usuario
        if not current_user.puede_ver_alertas():
            flash('Acceso restringido a personal autorizado.', 'danger')
            return redirect(url_for('main.inicio'))

        # Si tiene permiso, ejecutar la funcion original
        return f(*args, **kwargs)
    return decorated_function


# =============================================================================
# DECORADOR: SOLO ADMINISTRADOR
# =============================================================================
def solo_admin(f):
    """
    Decorador que restringe el acceso exclusivamente a administradores.

    Este decorador se usa en:
    - Panel de administracion
    - Gestion de usuarios
    - Bitacora de auditoria
    - Configuracion del sistema

    Ni orientadores ni discentes pueden acceder a estas rutas.

    IMPORTANTE: Este decorador debe usarse DESPUES de @login_required.

    Uso:
        @app.route('/admin/usuarios')
        @login_required
        @solo_admin
        def gestion_usuarios():
            ...

    Retorna:
        La funcion envuelta con verificacion de permisos de admin
    """
    @wraps(f)  # Preservar metadatos de la funcion original
    def decorated_function(*args, **kwargs):
        """Funcion envuelta que verifica permisos de administrador."""
        # Verificar autenticacion (seguridad adicional)
        if not current_user.is_authenticated:
            flash('Debe iniciar sesión para acceder.', 'warning')
            return redirect(url_for('auth.login'))

        # Verificar que sea administrador
        # El metodo es_administrador() esta definido en el modelo Usuario
        if not current_user.es_administrador():
            flash('Acceso restringido a administradores.', 'danger')
            return redirect(url_for('main.inicio'))

        # Si es admin, ejecutar la funcion original
        return f(*args, **kwargs)
    return decorated_function
