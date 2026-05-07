"""
================================================================================
MENTIS CURA - Rutas de Autenticacion
================================================================================
Archivo: routes/auth.py
Descripcion: Define las rutas (URLs) para el modulo de autenticacion.
             Incluye login, logout y registro de nuevos discentes.

Rutas disponibles:
    - /login: Pagina de inicio de sesion
    - /logout: Cierre de sesion
    - /registro: Formulario de registro para discentes
    - /registro-exitoso: Confirmacion de registro exitoso

Este archivo actua como "controlador" en la arquitectura MVC.
Recibe las peticiones HTTP, las procesa y retorna respuestas.

Autor: Proyecto de Tesis
Fecha: 2024
================================================================================
"""

# =============================================================================
# IMPORTACIONES
# =============================================================================
import re  # Expresiones regulares para validar matricula

# Flask: Funciones para manejo de rutas web
from flask import Blueprint, render_template, redirect, url_for, flash, request

# Flask-Login: Manejo de sesiones de usuario
from flask_login import login_user, logout_user, login_required, current_user

# Importaciones del proyecto
from app import db  # Base de datos
from app.models.usuario import Usuario, Rol  # Modelos
from app.services.auth_service import AuthService  # Servicio de autenticacion


# =============================================================================
# CREAR BLUEPRINT
# =============================================================================
# Un Blueprint es un grupo de rutas relacionadas
# 'auth' es el nombre del blueprint, se usa en url_for('auth.login')
auth_bp = Blueprint('auth', __name__)


# =============================================================================
# RUTA: LOGIN (Inicio de Sesion)
# =============================================================================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Pagina de inicio de sesion.

    Metodos HTTP:
        GET: Muestra el formulario de login
        POST: Procesa las credenciales enviadas

    Flujo:
        1. Si el usuario ya esta autenticado, redirige al inicio
        2. Si es POST, valida las credenciales
        3. Si son correctas, inicia sesion y redirige
        4. Si son incorrectas, muestra mensaje de error

    Retorna:
        GET: Pagina HTML del formulario de login
        POST exitoso: Redireccion al inicio o pagina solicitada
        POST fallido: Pagina de login con mensaje de error
    """
    # -------------------------------------------------------------------------
    # Si ya esta autenticado, redirigir al inicio
    # -------------------------------------------------------------------------
    if current_user.is_authenticated:
        return redirect(url_for('main.inicio'))

    # -------------------------------------------------------------------------
    # Procesar formulario de login (metodo POST)
    # -------------------------------------------------------------------------
    if request.method == 'POST':
        # Obtener datos del formulario
        # strip() elimina espacios en blanco al inicio y final
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # Validacion basica: campos no vacios
        if not username or not password:
            flash('Por favor ingrese usuario y contraseña.', 'warning')
            return render_template('auth/login.html')

        # Intentar autenticar usando el servicio
        # autenticar() retorna (usuario, error)
        usuario, error = AuthService.autenticar(username, password)

        # Si hubo error, mostrar mensaje y volver al formulario
        if error:
            flash(error, 'danger')
            return render_template('auth/login.html')

        # ---------------------------------------------------------------------
        # Login exitoso
        # ---------------------------------------------------------------------
        # login_user() de Flask-Login crea la sesion del usuario
        # remember=True mantiene la sesion activa por mas tiempo
        login_user(usuario, remember=True)

        # Mostrar mensaje de bienvenida
        flash(f'Bienvenido, {usuario.nombre}', 'success')

        # Verificar si habia una pagina solicitada antes del login
        # (por ejemplo, si intentaron acceder a /alertas sin estar logueados)
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)

        # Redirigir segun el rol del usuario
        if usuario.puede_ver_alertas():
            # Orientadores y admins van al listado de alertas
            return redirect(url_for('alertas.listado'))
        # Discentes van al inicio
        return redirect(url_for('main.inicio'))

    # -------------------------------------------------------------------------
    # Mostrar formulario de login (metodo GET)
    # -------------------------------------------------------------------------
    return render_template('auth/login.html')


# =============================================================================
# RUTA: LOGOUT (Cierre de Sesion)
# =============================================================================
@auth_bp.route('/logout')
@login_required  # Solo usuarios autenticados pueden cerrar sesion
def logout():
    """
    Cierre de sesion del usuario.

    Flujo:
        1. Cierra la sesion con Flask-Login
        2. Muestra mensaje de confirmacion
        3. Redirige al login

    Retorna:
        Redireccion a la pagina de login
    """
    # Cerrar la sesion con Flask-Login
    logout_user()

    # Mostrar mensaje de confirmacion
    flash('Sesión cerrada correctamente.', 'info')

    # Redirigir al login
    return redirect(url_for('auth.login'))


# =============================================================================
# RUTA: REGISTRO (Crear cuenta de discente)
# =============================================================================
@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    """
    Pagina de registro para nuevos discentes.

    Los discentes pueden auto-registrarse proporcionando:
    - Datos personales: nombre, apellidos, edad
    - Datos academicos: matricula, año, carrera, compañia
    - Credenciales: contraseña

    La matricula se convierte en el username para iniciar sesion.

    Metodos HTTP:
        GET: Muestra el formulario de registro
        POST: Procesa los datos y crea el usuario

    Validaciones:
        - Nombre y apellido paterno obligatorios (min 2 caracteres)
        - Matricula con formato letra + numeros (ej: A12345)
        - Edad entre 16 y 50 años
        - Año, carrera y compañia validos
        - Contraseña minimo 6 caracteres
        - Confirmacion de contraseña coincidente
        - Matricula no duplicada

    Retorna:
        GET: Pagina HTML del formulario de registro
        POST exitoso: Redireccion a pagina de exito
        POST fallido: Formulario con mensajes de error
    """
    # -------------------------------------------------------------------------
    # Si ya esta autenticado, redirigir al inicio
    # -------------------------------------------------------------------------
    if current_user.is_authenticated:
        return redirect(url_for('main.inicio'))

    # -------------------------------------------------------------------------
    # Procesar formulario de registro (metodo POST)
    # -------------------------------------------------------------------------
    if request.method == 'POST':
        # Obtener todos los datos del formulario
        nombre = request.form.get('nombre', '').strip()
        apellido_paterno = request.form.get('apellido_paterno', '').strip()
        apellido_materno = request.form.get('apellido_materno', '').strip()
        # Convertir matricula a mayusculas
        matricula = request.form.get('matricula', '').strip().upper()
        edad = request.form.get('edad', type=int)
        anio_cursa = request.form.get('anio_cursa', type=int)
        carrera = request.form.get('carrera', '').strip()
        compania = request.form.get('compania', '').strip()
        grupo = request.form.get('grupo', '').strip()
        sexo = request.form.get('sexo', '').strip()
        estado_civil = request.form.get('estado_civil', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')

        # ---------------------------------------------------------------------
        # Validaciones
        # ---------------------------------------------------------------------
        errores = []  # Lista para acumular errores

        # Validar nombre
        if not nombre or len(nombre) < 2:
            errores.append('El nombre es obligatorio (mínimo 2 caracteres).')

        # Validar apellido paterno
        if not apellido_paterno or len(apellido_paterno) < 2:
            errores.append('El apellido paterno es obligatorio (mínimo 2 caracteres).')

        # Validar formato de matricula (letra + numeros)
        if not matricula:
            errores.append('La matrícula es obligatoria.')
        elif not re.match(r'^[A-Z]\d+$', matricula):
            errores.append('La matrícula debe ser una letra seguida de números (ej: A12345).')

        # Validar edad (16-50 años)
        if not edad or edad < 16 or edad > 50:
            errores.append('La edad debe estar entre 16 y 50 años.')

        # Validar año que cursa (1-6)
        if not anio_cursa or anio_cursa not in Usuario.ANIOS:
            errores.append('Seleccione un año válido (1-6).')

        # Validar carrera (debe ser una de las opciones validas)
        if not carrera or carrera not in [c[0] for c in Usuario.CARRERAS]:
            errores.append('Seleccione una carrera válida.')

        # Validar compañia (debe ser una de las opciones validas)
        if not compania or compania not in [c[0] for c in Usuario.COMPANIAS]:
            errores.append('Seleccione una compañía válida.')

        # Validar grupo
        if not grupo or grupo not in Usuario.TODOS_GRUPOS:
            errores.append('Seleccione un grupo válido.')

        # Validar sexo
        if not sexo or sexo not in [s[0] for s in Usuario.SEXOS]:
            errores.append('Seleccione su sexo.')

        # Validar estado civil
        if not estado_civil or estado_civil not in [e[0] for e in Usuario.ESTADOS_CIVILES]:
            errores.append('Seleccione su estado civil.')

        # Validar contraseña (minimo 6 caracteres)
        if not password or len(password) < 6:
            errores.append('La contraseña debe tener al menos 6 caracteres.')

        # Validar que las contraseñas coincidan
        if password != password_confirm:
            errores.append('Las contraseñas no coinciden.')

        # Verificar que la matricula no este duplicada
        if Usuario.query.filter_by(matricula=matricula).first():
            errores.append('Esta matrícula ya está registrada.')

        # Verificar que el username no este duplicado
        if Usuario.query.filter_by(username=matricula).first():
            errores.append('Este usuario ya existe.')

        # ---------------------------------------------------------------------
        # Si hay errores, mostrarlos y volver al formulario
        # ---------------------------------------------------------------------
        if errores:
            for error in errores:
                flash(error, 'danger')
            return render_template('auth/registro.html',
                                   carreras=Usuario.CARRERAS,
                                   companias=Usuario.COMPANIAS,
                                   anios=Usuario.ANIOS,
                                   sexos=Usuario.SEXOS,
                                   estados_civiles=Usuario.ESTADOS_CIVILES)

        # ---------------------------------------------------------------------
        # Obtener el rol de discente
        # ---------------------------------------------------------------------
        rol_discente = Rol.query.filter_by(nombre='discente').first()
        if not rol_discente:
            flash('Error de configuración del sistema. Contacte al administrador.', 'danger')
            return render_template('auth/registro.html',
                                   carreras=Usuario.CARRERAS,
                                   companias=Usuario.COMPANIAS,
                                   anios=Usuario.ANIOS,
                                   sexos=Usuario.SEXOS,
                                   estados_civiles=Usuario.ESTADOS_CIVILES)

        # ---------------------------------------------------------------------
        # Crear el nuevo usuario
        # ---------------------------------------------------------------------
        try:
            usuario = Usuario(
                username=matricula,
                nombre=nombre,
                apellido_paterno=apellido_paterno,
                apellido_materno=apellido_materno or None,
                matricula=matricula,
                edad=edad,
                anio_cursa=anio_cursa,
                carrera=carrera,
                compania=compania,
                grupo=grupo,
                sexo=sexo,
                estado_civil=estado_civil,
                rol_id=rol_discente.id,
                activo=True
            )
            # Establecer contraseña (se guarda como hash)
            usuario.set_password(password)

            # Guardar en la base de datos
            db.session.add(usuario)
            db.session.commit()

            # Redirigir a pagina de exito
            return redirect(url_for('auth.registro_exitoso', matricula=matricula))

        except Exception as e:
            # Si hay error, revertir cambios y mostrar mensaje
            db.session.rollback()
            flash(f'Error al crear el usuario. Intente nuevamente.', 'danger')
            return render_template('auth/registro.html',
                                   carreras=Usuario.CARRERAS,
                                   companias=Usuario.COMPANIAS,
                                   anios=Usuario.ANIOS,
                                   sexos=Usuario.SEXOS,
                                   estados_civiles=Usuario.ESTADOS_CIVILES)

    # -------------------------------------------------------------------------
    # Mostrar formulario de registro (metodo GET)
    # -------------------------------------------------------------------------
    return render_template('auth/registro.html',
                           carreras=Usuario.CARRERAS,
                           companias=Usuario.COMPANIAS,
                           anios=Usuario.ANIOS,
                           sexos=Usuario.SEXOS,
                           estados_civiles=Usuario.ESTADOS_CIVILES)


# =============================================================================
# RUTA: REGISTRO EXITOSO
# =============================================================================
@auth_bp.route('/registro-exitoso')
def registro_exitoso():
    """
    Pagina de confirmacion de registro exitoso.

    Muestra al usuario su matricula (que es su username para login)
    y le proporciona un enlace para ir a iniciar sesion.

    Parametros de URL:
        matricula: La matricula del usuario recien registrado

    Retorna:
        Pagina HTML de confirmacion con la matricula
    """
    # Obtener la matricula de los parametros de URL
    matricula = request.args.get('matricula', '')

    # Mostrar pagina de exito
    return render_template('auth/registro_exitoso.html', matricula=matricula)
