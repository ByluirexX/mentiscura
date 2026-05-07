"""
================================================================================
MENTIS CURA - Modelo de Usuario y Rol
================================================================================
Archivo: models/usuario.py
Descripcion: Define los modelos Usuario y Rol para el control de acceso.

El sistema tiene tres roles:
    1. Administrador: Acceso completo al sistema
    2. Orientador: Puede ver alertas y evaluaciones de discentes
    3. Discente: Solo puede responder cuestionarios y ver sus resultados

Autor: Proyecto de Tesis
Fecha: 2024
================================================================================
"""

# =============================================================================
# IMPORTACIONES
# =============================================================================
from datetime import datetime  # Para fechas de creacion y ultimo acceso

# UserMixin: Clase base que proporciona metodos requeridos por Flask-Login
# (is_authenticated, is_active, is_anonymous, get_id)
from flask_login import UserMixin

# Importar la instancia de la base de datos
from app import db


# =============================================================================
# MODELO ROL
# =============================================================================
class Rol(db.Model):
    """
    Modelo que representa los roles del sistema.

    Los roles definen que acciones puede realizar cada usuario:
        - administrador: Gestion completa del sistema
        - orientador: Acceso a alertas y evaluaciones
        - discente: Responde cuestionarios

    Atributos:
        id (int): Identificador unico del rol (clave primaria)
        nombre (str): Nombre del rol (unico, ej: 'administrador')
        descripcion (str): Descripcion del rol
        created_at (datetime): Fecha de creacion del rol
        usuarios: Relacion con los usuarios que tienen este rol

    Tabla en BD: 'roles'
    """
    # Nombre de la tabla en la base de datos
    __tablename__ = 'roles'

    # -------------------------------------------------------------------------
    # COLUMNAS DE LA TABLA
    # -------------------------------------------------------------------------
    # Clave primaria: Identificador unico autoincrementable
    id = db.Column(db.Integer, primary_key=True)

    # Nombre del rol (debe ser unico)
    nombre = db.Column(db.String(50), unique=True, nullable=False)

    # Descripcion del rol
    descripcion = db.Column(db.String(200))

    # Fecha de creacion (se asigna automaticamente)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # -------------------------------------------------------------------------
    # RELACIONES
    # -------------------------------------------------------------------------
    # Relacion uno-a-muchos: Un rol puede tener muchos usuarios
    # backref='rol' permite acceder al rol desde el usuario: usuario.rol
    # lazy='dynamic' permite hacer consultas adicionales sobre los usuarios
    usuarios = db.relationship('Usuario', backref='rol', lazy='dynamic')

    # Mapeo de nombre interno a nombre visible en la interfaz
    NOMBRES_DISPLAY = {
        'administrador': 'Administrador',
        'orientador': 'Psicólogo',
        'discente': 'Discente',
    }

    @property
    def nombre_display(self):
        """Retorna el nombre visible del rol para la interfaz."""
        return self.NOMBRES_DISPLAY.get(self.nombre, self.nombre.title())

    def __repr__(self):
        """
        Representacion en texto del rol (para debugging).
        Ejemplo: <Rol administrador>
        """
        return f'<Rol {self.nombre}>'


# =============================================================================
# MODELO USUARIO
# =============================================================================
class Usuario(UserMixin, db.Model):
    """
    Modelo que representa a los usuarios del sistema.

    Hereda de:
        - UserMixin: Proporciona metodos requeridos por Flask-Login
        - db.Model: Clase base de SQLAlchemy para modelos

    Tipos de usuario:
        - Administradores y orientadores: username y contrasena normales
        - Discentes: Usan su matricula como username

    Atributos principales:
        - Datos de acceso: username, password_hash
        - Datos personales: nombre, apellido_paterno, apellido_materno
        - Datos academicos (discentes): matricula, edad, anio_cursa, carrera, compania
        - Estado: rol_id, activo
        - Auditoria: created_at, updated_at, ultimo_acceso

    Tabla en BD: 'usuarios'
    """
    # Nombre de la tabla en la base de datos
    __tablename__ = 'usuarios'

    # -------------------------------------------------------------------------
    # COLUMNAS DE DATOS DE ACCESO
    # -------------------------------------------------------------------------
    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Nombre de usuario (unico, indexado para busquedas rapidas)
    # Los discentes usan su matricula como username
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)

    # Contrasena del usuario
    password_hash = db.Column(db.String(256), nullable=False)

    # -------------------------------------------------------------------------
    # COLUMNAS DE DATOS PERSONALES
    # -------------------------------------------------------------------------
    # Nombre(s) del usuario
    nombre = db.Column(db.String(100), nullable=False)

    # Apellido paterno (obligatorio)
    apellido_paterno = db.Column(db.String(100), nullable=False)

    # Apellido materno (opcional)
    apellido_materno = db.Column(db.String(100))

    # Matricula (solo para discentes, es su identificador unico)
    # Formato: Una letra seguida de numeros (ej: A12345)
    matricula = db.Column(db.String(50), unique=True, index=True)

    # -------------------------------------------------------------------------
    # COLUMNAS DE DATOS ACADEMICOS (Solo para discentes)
    # -------------------------------------------------------------------------
    # Edad del discente (entre 16 y 50 anos)
    edad = db.Column(db.Integer)

    # Ano que cursa (1 a 6)
    anio_cursa = db.Column(db.Integer)

    # Carrera que estudia (codigo de la carrera)
    carrera = db.Column(db.String(100))

    # Compania a la que pertenece (codigo de la compania)
    compania = db.Column(db.String(50))

    # Grupo al que pertenece (A-F para 1er año, IC/ICE/etc. para años superiores)
    grupo = db.Column(db.String(20))

    # Sexo del discente
    sexo = db.Column(db.String(10))

    # Estado civil del discente
    estado_civil = db.Column(db.String(20))

    # -------------------------------------------------------------------------
    # COLUMNAS DE ESTADO Y ROL
    # -------------------------------------------------------------------------
    # Referencia al rol del usuario (clave foranea a tabla 'roles')
    rol_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)

    # Indica si la cuenta esta activa (se puede desactivar sin eliminar)
    activo = db.Column(db.Boolean, default=True)

    # -------------------------------------------------------------------------
    # COLUMNAS DE AUDITORIA
    # -------------------------------------------------------------------------
    # Fecha de creacion de la cuenta
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Fecha de ultima modificacion (se actualiza automaticamente)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Fecha del ultimo inicio de sesion
    ultimo_acceso = db.Column(db.DateTime)

    # -------------------------------------------------------------------------
    # CONSTANTES PARA OPCIONES DE FORMULARIO
    # -------------------------------------------------------------------------
    # Lista de carreras disponibles (codigo, nombre_visible)
    CARRERAS = [
        ('tronco_comun', 'Tronco Común'),
        ('ing_computacion', 'Ingeniería en Computación e Informática'),
        ('ing_industrial', 'Ingeniería Industrial'),
        ('ing_comunicaciones', 'Ingeniería en Comunicaciones y Electrónica'),
        ('ing_construccion', 'Ingeniería en Construcción')
    ]

    # Lista de companias disponibles (codigo, nombre_visible)
    COMPANIAS = [
        ('primera', 'Primera Cía.'),
        ('segunda', 'Segunda Cía.'),
        ('tercera', 'Tercera Cía.'),
        ('cuarta', 'Cuarta Cía.'),
        ('oficiales', 'Cía. Oficiales')
    ]

    # Años que se pueden cursar
    ANIOS = [1, 2, 3, 4, 5, 6]

    # Grupos por año
    GRUPOS_PRIMER_ANO = [
        ('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E'), ('F', 'F'),
    ]
    GRUPOS_SEGUNDO_ANO = [
        ('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E'), ('F', 'F'),
        ('IC', 'I.C.'), ('ICE', 'I.C.E.'), ('IIM', 'I.I.M.'),
        ('IIQ', 'I.I.Q.'), ('IIE', 'I.I.E.'), ('ICI', 'I.C.I.'),
    ]
    GRUPOS_RESTO = [
        ('IC', 'I.C.'), ('ICE', 'I.C.E.'), ('IIM', 'I.I.M.'),
        ('IIQ', 'I.I.Q.'), ('IIE', 'I.I.E.'), ('ICI', 'I.C.I.'),
    ]

    # Todos los grupos posibles (para validación)
    TODOS_GRUPOS = {c for c, _ in GRUPOS_SEGUNDO_ANO}

    # Sexo
    SEXOS = [('hombre', 'Hombre'), ('mujer', 'Mujer')]

    # Estado civil
    ESTADOS_CIVILES = [
        ('soltero', 'Solter@'),
        ('casado', 'Casad@'),
        ('otro', 'Otro'),
    ]

    # -------------------------------------------------------------------------
    # RELACIONES CON OTROS MODELOS
    # -------------------------------------------------------------------------
    # Evaluaciones realizadas por este usuario
    evaluaciones = db.relationship('Evaluacion', backref='usuario', lazy='dynamic',
                                   foreign_keys='Evaluacion.usuario_id')

    # Alertas generadas por las evaluaciones de este usuario
    alertas_generadas = db.relationship('Alerta', backref='usuario',
                                        lazy='dynamic', foreign_keys='Alerta.usuario_id')

    # -------------------------------------------------------------------------
    # METODOS DE CONTRASENA
    # -------------------------------------------------------------------------
    def set_password(self, password):
        """
        Almacena la contrasena del usuario.

        Parametros:
            password (str): Contrasena
        """
        self.password_hash = password

    def check_password(self, password):
        """
        Verifica si la contrasena es correcta.

        Parametros:
            password (str): Contrasena a verificar

        Retorna:
            bool: True si la contrasena es correcta, False si no
        """
        return self.password_hash == password

    # -------------------------------------------------------------------------
    # METODOS DE VERIFICACION DE ROL
    # -------------------------------------------------------------------------
    def es_administrador(self):
        """
        Verifica si el usuario tiene rol de administrador.

        Retorna:
            bool: True si es administrador, False si no
        """
        return self.rol.nombre == 'administrador'

    def es_orientador(self):
        """
        Verifica si el usuario tiene rol de orientador.

        Retorna:
            bool: True si es orientador, False si no
        """
        return self.rol.nombre == 'orientador'

    def es_discente(self):
        """
        Verifica si el usuario tiene rol de discente.

        Retorna:
            bool: True si es discente, False si no
        """
        return self.rol.nombre == 'discente'

    def puede_ver_alertas(self):
        """
        Verifica si el usuario puede acceder al modulo de alertas.

        Solo administradores y orientadores pueden ver alertas.

        Retorna:
            bool: True si puede ver alertas, False si no
        """
        return self.rol.nombre in ['administrador', 'orientador']

    # -------------------------------------------------------------------------
    # METODOS DE UTILIDAD
    # -------------------------------------------------------------------------
    def nombre_completo(self):
        """
        Retorna el nombre completo del usuario.

        Formato: "Nombre ApellidoPaterno ApellidoMaterno"
        Si no tiene apellido materno, solo retorna nombre y paterno.

        Retorna:
            str: Nombre completo del usuario
        """
        if self.apellido_materno:
            return f'{self.nombre} {self.apellido_paterno} {self.apellido_materno}'
        return f'{self.nombre} {self.apellido_paterno}'

    def get_carrera_display(self):
        """
        Retorna el nombre legible de la carrera.

        Convierte el codigo interno (ej: 'ing_computacion')
        al nombre para mostrar (ej: 'Ingeniería en Computación e Informática')

        Retorna:
            str: Nombre de la carrera o '-' si no tiene
        """
        for codigo, nombre in self.CARRERAS:
            if codigo == self.carrera:
                return nombre
        return self.carrera or '-'

    def get_grupo_display(self):
        todos = dict(self.GRUPOS_SEGUNDO_ANO)
        return todos.get(self.grupo, self.grupo or '-')

    def get_sexo_display(self):
        return dict(self.SEXOS).get(self.sexo, self.sexo or '-')

    def get_estado_civil_display(self):
        return dict(self.ESTADOS_CIVILES).get(self.estado_civil, self.estado_civil or '-')

    def get_compania_display(self):
        """
        Retorna el nombre legible de la compania.

        Convierte el codigo interno (ej: 'primera')
        al nombre para mostrar (ej: 'Primera Cía.')

        Retorna:
            str: Nombre de la compania o '-' si no tiene
        """
        for codigo, nombre in self.COMPANIAS:
            if codigo == self.compania:
                return nombre
        return self.compania or '-'

    def __repr__(self):
        """
        Representacion en texto del usuario (para debugging).
        Ejemplo: <Usuario admin>
        """
        return f'<Usuario {self.username}>'
