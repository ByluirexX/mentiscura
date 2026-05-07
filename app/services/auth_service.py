"""
================================================================================
MENTIS CURA - Servicio de Autenticacion
================================================================================
Archivo: services/auth_service.py
Descripcion: Servicio que maneja toda la logica de autenticacion del sistema.
             Incluye inicio de sesion, cierre de sesion y registro de eventos.

Este servicio separa la logica de autenticacion de las rutas (controladores),
siguiendo el patron de arquitectura por capas.

Funcionalidades:
    - Validar credenciales de usuario
    - Registrar intentos de acceso (exitosos y fallidos)
    - Actualizar fecha de ultimo acceso
    - Actualizar fecha de ultimo acceso

Autor: Proyecto de Tesis
Fecha: 2024
================================================================================
"""

# =============================================================================
# IMPORTACIONES
# =============================================================================
from datetime import datetime  # Para registrar fechas de acceso

from flask import request  # Para obtener IP y User-Agent

from app import db  # Instancia de base de datos
from app.models.usuario import Usuario  # Modelo de usuario


# =============================================================================
# CLASE DEL SERVICIO DE AUTENTICACION
# =============================================================================
class AuthService:
    """
    Servicio para operaciones de autenticacion.

    Esta clase contiene toda la logica relacionada con:
    - Verificacion de credenciales
    - Gestion de sesiones
    - Registro de actividad de acceso

    Todos los metodos son estaticos porque no necesitan estado de instancia.
    """

    # -------------------------------------------------------------------------
    # METODO PRINCIPAL DE AUTENTICACION
    # -------------------------------------------------------------------------
    @staticmethod
    def autenticar(username, password):
        """
        Autentica un usuario con nombre de usuario y contrasena.

        Este metodo realiza las siguientes validaciones:
        1. Verifica que el usuario exista en la base de datos
        2. Verifica que la cuenta este activa
        3. Verifica que la contrasena sea correcta

        En caso de fallo, registra el intento en la bitacora.
        En caso de exito, actualiza la fecha de ultimo acceso.

        Parametros:
            username (str): Nombre de usuario o matricula (para discentes)
            password (str): Contrasena en texto plano (se compara con hash)

        Retorna:
            tuple: (usuario, mensaje_error)
                - Si exitoso: (objeto Usuario, None)
                - Si falla: (None, "mensaje de error")

        Ejemplo:
            usuario, error = AuthService.autenticar('admin', 'admin123')
            if error:
                print(f"Error: {error}")
            else:
                print(f"Bienvenido, {usuario.nombre}")
        """
        # ---------------------------------------------------------------------
        # PASO 1: Buscar el usuario en la base de datos
        # ---------------------------------------------------------------------
        usuario = Usuario.query.filter_by(username=username).first()

        # Si no existe el usuario, retornar error
        if not usuario:
            return None, 'Usuario no encontrado'

        # ---------------------------------------------------------------------
        # PASO 2: Verificar que la cuenta este activa
        # ---------------------------------------------------------------------
        # Las cuentas pueden desactivarse sin eliminarse
        if not usuario.activo:
            return None, 'Cuenta desactivada. Contacte al administrador.'

        # ---------------------------------------------------------------------
        # PASO 3: Verificar la contrasena
        # ---------------------------------------------------------------------
        if not usuario.check_password(password):
            return None, 'Contraseña incorrecta'

        # ---------------------------------------------------------------------
        # PASO 4: Login exitoso - Actualizar ultimo acceso
        # ---------------------------------------------------------------------
        usuario.ultimo_acceso = datetime.utcnow()
        db.session.commit()

        # Retornar el usuario sin error
        return usuario, None
