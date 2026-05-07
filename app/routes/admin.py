"""
================================================================================
MENTIS CURA - Rutas de Administracion
================================================================================
Archivo: routes/admin.py
Descripcion: Define las rutas para el modulo de administracion del sistema.
             Incluye gestion de usuarios.

Rutas disponibles:
    - /admin/: Panel principal de administracion
    - /admin/usuarios: Lista de usuarios del sistema
    - /admin/usuarios/nuevo: Crear nuevo usuario
    - /admin/usuarios/<id>/editar: Editar usuario existente

IMPORTANTE: Todas las rutas de este modulo son solo para
administradores. Orientadores y discentes no tienen acceso.

Control de acceso:
    - Solo usuarios con rol 'administrador'
    - Se usa el decorador @solo_admin para verificar permisos

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
from app.models.alerta import Alerta
from app.models.usuario import Usuario, Rol  # Modelos de usuario y rol

# Decorador para restringir acceso solo a administradores
from app.utils.decorators import solo_admin


# =============================================================================
# CREAR BLUEPRINT
# =============================================================================
# Blueprint 'admin' con prefijo de URL /admin
admin_bp = Blueprint('admin', __name__)


# =============================================================================
# RUTA: PANEL PRINCIPAL DE ADMINISTRACION
# =============================================================================
@admin_bp.route('/')
@login_required
@solo_admin  # Solo administradores pueden acceder
def index():
    """
    Panel principal de administracion.

    Muestra estadisticas generales del sistema:
    - Total de usuarios registrados
    - Total de discentes
    - Actividad reciente (ultimos 7 dias)

    Retorna:
        Pagina HTML con el panel de administracion
    """
    # -------------------------------------------------------------------------
    # Obtener estadisticas generales
    # -------------------------------------------------------------------------
    total_usuarios    = Usuario.query.count()
    total_discentes   = Usuario.query.join(Usuario.rol).filter_by(nombre='discente').count()
    total_orientadores = Usuario.query.join(Usuario.rol).filter_by(nombre='orientador').count()

    total_alertas      = Alerta.query.count()
    alertas_pendientes = Alerta.query.filter_by(estado='pendiente').count()
    alertas_en_revision = Alerta.query.filter_by(estado='en_revision').count()
    alertas_atendidas  = Alerta.query.filter_by(estado='atendida').count()

    estado_filtro = request.args.get('estado', '')
    query_alertas = Alerta.query
    if estado_filtro in ('pendiente', 'en_revision', 'atendida'):
        query_alertas = query_alertas.filter_by(estado=estado_filtro)
    alertas = query_alertas.order_by(Alerta.created_at.desc()).all()

    orientadores = (
        Usuario.query.join(Usuario.rol)
        .filter(Rol.nombre == 'orientador')
        .order_by(Usuario.apellido_paterno, Usuario.nombre)
        .all()
    )

    psicologos_stats = []
    for o in orientadores:
        alertas_del_psicologo = Alerta.query.filter(Alerta.atendida_por_id == o.id).all()
        psicologos_stats.append({
            'orientador': o,
            'total_atendidas': len(alertas_del_psicologo),
            'discentes_atendidos': len({a.usuario_id for a in alertas_del_psicologo}),
            'en_revision': Alerta.query.filter_by(atendida_por_id=o.id, estado='en_revision').count(),
        })
    psicologos_stats.sort(key=lambda x: x['total_atendidas'], reverse=True)

    return render_template('admin/index.html',
                           total_usuarios=total_usuarios,
                           total_discentes=total_discentes,
                           total_orientadores=total_orientadores,
                           total_alertas=total_alertas,
                           alertas_pendientes=alertas_pendientes,
                           alertas_en_revision=alertas_en_revision,
                           alertas_atendidas=alertas_atendidas,
                           alertas=alertas,
                           estado_filtro=estado_filtro,
                           psicologos_stats=psicologos_stats)


# =============================================================================
# RUTA: LISTADO DE USUARIOS
# =============================================================================
@admin_bp.route('/usuarios')
@login_required
@solo_admin
def usuarios():
    """
    Lista todos los usuarios registrados en el sistema.

    Muestra informacion de:
    - Administradores
    - Orientadores
    - Discentes

    Para cada usuario se presenta:
    - Nombre completo
    - Username / Matricula
    - Rol
    - Estado (activo/inactivo)
    - Fecha de creacion

    Retorna:
        Pagina HTML con la lista de usuarios
    """
    # Obtener todos los usuarios ordenados por fecha de creacion (mas recientes primero)
    usuarios = Usuario.query.order_by(Usuario.created_at.desc()).all()

    # Mostrar la pagina de listado
    return render_template('admin/usuarios.html', usuarios=usuarios)


# =============================================================================
# RUTA: CREAR NUEVO USUARIO
# =============================================================================
@admin_bp.route('/usuarios/nuevo', methods=['GET', 'POST'])
@login_required
@solo_admin
def nuevo_usuario():
    """
    Formulario para crear un nuevo usuario.

    El administrador puede crear usuarios de cualquier rol:
    - Administradores
    - Orientadores
    - Discentes

    Metodos HTTP:
        GET: Muestra el formulario vacio
        POST: Procesa los datos y crea el usuario

    Retorna:
        GET: Pagina HTML con formulario de creacion
        POST exitoso: Redireccion al listado de usuarios
        POST fallido: Formulario con mensajes de error
    """
    # Obtener todos los roles para el select del formulario
    roles = Rol.query.all()

    # -------------------------------------------------------------------------
    # Procesar formulario (metodo POST)
    # -------------------------------------------------------------------------
    if request.method == 'POST':
        # Obtener datos basicos del formulario
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        nombre = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido_paterno', '').strip()
        identificacion = request.form.get('identificacion', '').strip()
        rol_id = request.form.get('rol_id', type=int)

        # ---------------------------------------------------------------------
        # Validaciones basicas
        # ---------------------------------------------------------------------
        errores = []

        # Validar username
        if not username or len(username) < 3:
            errores.append('El usuario debe tener al menos 3 caracteres.')

        # Validar contraseña
        if not password or len(password) < 6:
            errores.append('La contraseña debe tener al menos 6 caracteres.')

        # Validar nombre y apellido
        if not nombre or not apellido:
            errores.append('Nombre y apellido paterno son obligatorios.')

        # Validar que se selecciono un rol
        if not rol_id:
            errores.append('Debe seleccionar un rol.')

        # Verificar que el username no este duplicado
        if Usuario.query.filter_by(username=username).first():
            errores.append('El nombre de usuario ya existe.')

        # Verificar matricula duplicada (si se proporcionó)
        identificacion_check = request.form.get('identificacion', '').strip()
        if identificacion_check and Usuario.query.filter_by(matricula=identificacion_check).first():
            errores.append('La matrícula ingresada ya está registrada en el sistema.')

        # Si hay errores, mostrarlos y volver al formulario
        if errores:
            for error in errores:
                flash(error, 'danger')
            return render_template('admin/usuario_form.html', roles=roles, modo='nuevo')

        # ---------------------------------------------------------------------
        # Obtener campos adicionales (para discentes)
        # ---------------------------------------------------------------------
        apellido_materno = request.form.get('apellido_materno', '').strip()
        edad = request.form.get('edad', type=int)
        anio_cursa = request.form.get('anio_cursa', type=int)
        carrera = request.form.get('carrera', '').strip()
        compania = request.form.get('compania', '').strip()

        # ---------------------------------------------------------------------
        # Crear el usuario
        # ---------------------------------------------------------------------
        usuario = Usuario(
            username=username,
            nombre=nombre,
            apellido_paterno=apellido,
            apellido_materno=apellido_materno or None,
            matricula=identificacion or None,
            edad=edad,
            anio_cursa=anio_cursa,
            carrera=carrera or None,
            compania=compania or None,
            rol_id=rol_id,
            activo=True
        )
        usuario.set_password(password)

        # Guardar en la base de datos
        try:
            db.session.add(usuario)
            db.session.commit()
            flash(f'Usuario {username} creado exitosamente.', 'success')
            return redirect(url_for('admin.usuarios'))
        except Exception:
            db.session.rollback()
            flash('Error al guardar el usuario. Verifique que el usuario y la matrícula no estén duplicados.', 'danger')
            return render_template('admin/usuario_form.html', roles=roles, modo='nuevo')

    # -------------------------------------------------------------------------
    # Mostrar formulario vacio (metodo GET)
    # -------------------------------------------------------------------------
    return render_template('admin/usuario_form.html', roles=roles, modo='nuevo')


# =============================================================================
# RUTA: EDITAR USUARIO
# =============================================================================
@admin_bp.route('/usuarios/<int:usuario_id>/editar', methods=['GET', 'POST'])
@login_required
@solo_admin
def editar_usuario(usuario_id):
    """
    Formulario para editar un usuario existente.

    Permite modificar:
    - Datos personales (nombre, apellidos)
    - Rol
    - Estado (activo/inactivo)
    - Contraseña (opcional)
    - Datos academicos (para discentes)

    Parametros de URL:
        usuario_id (int): ID del usuario a editar

    Retorna:
        GET: Pagina HTML con formulario prellenado
        POST exitoso: Redireccion al listado de usuarios
    """
    # Obtener el usuario o mostrar error 404
    usuario = Usuario.query.get_or_404(usuario_id)

    # Obtener todos los roles para el select
    roles = Rol.query.all()

    # -------------------------------------------------------------------------
    # Procesar formulario (metodo POST)
    # -------------------------------------------------------------------------
    if request.method == 'POST':
        nueva_matricula = request.form.get('identificacion', '').strip() or None

        # Verificar matrícula duplicada (excluyendo al usuario que se está editando)
        if nueva_matricula:
            existente = Usuario.query.filter_by(matricula=nueva_matricula).first()
            if existente and existente.id != usuario_id:
                flash('La matrícula ingresada ya pertenece a otro usuario.', 'danger')
                return render_template('admin/usuario_form.html',
                                       usuario=usuario, roles=roles, modo='editar')

        # Actualizar datos basicos
        usuario.nombre = request.form.get('nombre', '').strip()
        usuario.apellido_paterno = request.form.get('apellido_paterno', '').strip()
        usuario.apellido_materno = request.form.get('apellido_materno', '').strip() or None
        usuario.matricula = nueva_matricula
        usuario.rol_id = request.form.get('rol_id', type=int)

        # El checkbox 'activo' se envia como 'on' si esta marcado
        usuario.activo = request.form.get('activo') == 'on'

        # Actualizar campos adicionales para discentes
        usuario.edad = request.form.get('edad', type=int)
        usuario.anio_cursa = request.form.get('anio_cursa', type=int)
        usuario.carrera = request.form.get('carrera', '').strip() or None
        usuario.compania = request.form.get('compania', '').strip() or None

        # Cambiar contraseña solo si se proporciona una nueva
        nueva_password = request.form.get('password', '')
        if nueva_password and len(nueva_password) >= 6:
            usuario.set_password(nueva_password)

        # Guardar cambios
        try:
            db.session.commit()
            flash('Usuario actualizado correctamente.', 'success')
            return redirect(url_for('admin.usuarios'))
        except Exception:
            db.session.rollback()
            flash('Error al actualizar el usuario. Verifique que los datos no estén duplicados.', 'danger')
            return render_template('admin/usuario_form.html',
                                   usuario=usuario, roles=roles, modo='editar')

    # -------------------------------------------------------------------------
    # Mostrar formulario con datos actuales (metodo GET)
    # -------------------------------------------------------------------------
    return render_template('admin/usuario_form.html',
                           usuario=usuario,
                           roles=roles,
                           modo='editar')


# =============================================================================
# RUTA: ELIMINAR USUARIO
# =============================================================================
# Esta ruta permite al administrador eliminar (desactivar) usuarios.
# Se usa el metodo POST para evitar eliminaciones accidentales por URL.
# La eliminacion es "blanda": no borra al usuario de la base de datos,
# sino que lo marca como inactivo (activo = False). De esta forma se
# conservan sus evaluaciones y alertas.
# =============================================================================
@admin_bp.route('/usuarios/<int:usuario_id>/eliminar', methods=['POST'])
@login_required      # El usuario debe haber iniciado sesion
@solo_admin          # Solo los administradores pueden eliminar usuarios
def eliminar_usuario(usuario_id):
    """
    Elimina (desactiva) un usuario del sistema.

    Realiza una eliminacion blanda: marca al usuario como inactivo
    en lugar de borrarlo de la base de datos. Esto preserva la
    integridad de evaluaciones y alertas.

    Validaciones:
        - El administrador no puede eliminarse a si mismo
        - El usuario debe existir

    Parametros de URL:
        usuario_id (int): ID del usuario a eliminar

    Retorna:
        Redireccion al listado de usuarios con mensaje de exito o error
    """
    # -------------------------------------------------------------------------
    # Buscar al usuario en la base de datos por su ID.
    # Si no existe, se muestra automaticamente una pagina de error 404.
    # -------------------------------------------------------------------------
    usuario = Usuario.query.get_or_404(usuario_id)

    # -------------------------------------------------------------------------
    # Proteccion: un administrador NO puede eliminarse a si mismo.
    # Esto evita que el sistema quede sin administradores activos.
    # -------------------------------------------------------------------------
    if usuario.id == current_user.id:
        flash('No puede eliminar su propia cuenta.', 'danger')
        return redirect(url_for('admin.usuarios'))

    # -------------------------------------------------------------------------
    # Guardar el nombre de usuario y nombre completo ANTES de desactivarlo,
    # ya que se usan en el mensaje flash.
    # -------------------------------------------------------------------------
    username = usuario.username
    nombre = usuario.nombre_completo()

    # -------------------------------------------------------------------------
    # Eliminacion blanda: se cambia el campo "activo" a False.
    # El usuario seguira existiendo en la base de datos pero no podra
    # iniciar sesion. Si en el futuro se necesita reactivar, se puede
    # hacer desde la pantalla de editar usuario.
    # -------------------------------------------------------------------------
    usuario.activo = False
    db.session.commit()

    flash(f'Usuario {username} eliminado correctamente.', 'success')
    return redirect(url_for('admin.usuarios'))

