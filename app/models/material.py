"""
================================================================================
MENTIS CURA - Modelo de Material de Apoyo
================================================================================
Archivo: models/material.py
Descripcion: Define el modelo para los materiales de apoyo psicologico
             (documentos PDF e imagenes) que pueden subir orientadores
             y administradores.

Autor: Proyecto de Tesis
Fecha: 2024
================================================================================
"""

from datetime import datetime

from app import db


class Material(db.Model):
    """
    Modelo que representa un material de apoyo psicologico.

    Los materiales pueden ser documentos PDF o imagenes.
    Solo orientadores y administradores pueden subirlos o eliminarlos.
    Todos los usuarios autenticados pueden verlos y descargarlos.

    Tabla en BD: 'materiales'
    """
    __tablename__ = 'materiales'

    # -------------------------------------------------------------------------
    # COLUMNAS
    # -------------------------------------------------------------------------
    id = db.Column(db.Integer, primary_key=True)

    # Titulo descriptivo del material
    titulo = db.Column(db.String(200), nullable=False)

    # Descripcion opcional del contenido
    descripcion = db.Column(db.Text)

    # Tipo de archivo: 'pdf' o 'imagen'
    tipo_archivo = db.Column(db.String(10), nullable=False)

    # Nombre unico generado (uuid) con el que se guarda en disco
    nombre_archivo = db.Column(db.String(200), nullable=False, unique=True)

    # Nombre original del archivo subido por el usuario
    nombre_original = db.Column(db.String(200), nullable=False)

    # Quien subio el material
    subido_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    # Fecha de subida
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # -------------------------------------------------------------------------
    # RELACIONES
    # -------------------------------------------------------------------------
    subido_por = db.relationship('Usuario', foreign_keys=[subido_por_id])

    # -------------------------------------------------------------------------
    # EXTENSIONES PERMITIDAS POR TIPO
    # -------------------------------------------------------------------------
    EXTENSIONES_PDF = {'pdf'}
    EXTENSIONES_IMAGEN = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
    EXTENSIONES_PERMITIDAS = EXTENSIONES_PDF | EXTENSIONES_IMAGEN

    # -------------------------------------------------------------------------
    # METODOS
    # -------------------------------------------------------------------------
    @staticmethod
    def tipo_desde_extension(extension):
        """
        Determina el tipo de archivo ('pdf' o 'imagen') segun la extension.

        Parametros:
            extension (str): Extension sin punto, en minusculas (ej: 'pdf', 'jpg')

        Retorna:
            str: 'pdf', 'imagen', o None si no es valida
        """
        if extension in Material.EXTENSIONES_PDF:
            return 'pdf'
        if extension in Material.EXTENSIONES_IMAGEN:
            return 'imagen'
        return None

    def es_imagen(self):
        """Retorna True si el material es una imagen."""
        return self.tipo_archivo == 'imagen'

    def es_pdf(self):
        """Retorna True si el material es un PDF."""
        return self.tipo_archivo == 'pdf'

    def __repr__(self):
        return f'<Material {self.id} - {self.titulo}>'
