"""
================================================================================
MENTIS CURA - Rutas del Modulo de Materiales de Apoyo
================================================================================
Archivo: routes/materiales.py
Descripcion: Define las rutas para el modulo de materiales de apoyo
             psicologico. Permite subir, ver y eliminar documentos PDF
             e imagenes.

Rutas disponibles:
    - GET  /materiales/              : Listado de materiales (todos los usuarios)
    - GET  /materiales/subir         : Formulario de subida (orientador/admin)
    - POST /materiales/subir         : Procesar subida (orientador/admin)
    - GET  /materiales/<id>/archivo  : Servir el archivo (todos los usuarios)
    - POST /materiales/<id>/eliminar : Eliminar material (orientador/admin)

Autor: Proyecto de Tesis
Fecha: 2024
================================================================================
"""

import os
import uuid

from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, send_from_directory, url_for)
from flask_login import current_user, login_required

from app import db
from app.models.material import Material
from app.utils.decorators import solo_orientador


# =============================================================================
# CREAR BLUEPRINT
# =============================================================================
materiales_bp = Blueprint('materiales', __name__)


# =============================================================================
# RUTA: LISTADO DE MATERIALES
# =============================================================================
@materiales_bp.route('/')
@login_required
def listado():
    """
    Muestra todos los materiales de apoyo disponibles.

    Accesible para todos los usuarios autenticados.
    Solo orientadores y admins ven el boton de subir y eliminar.

    Retorna:
        Pagina HTML con la lista de materiales
    """
    materiales = Material.query.order_by(Material.created_at.desc()).all()
    return render_template('materiales/listado.html', materiales=materiales)


# =============================================================================
# RUTA: SUBIR MATERIAL
# =============================================================================
@materiales_bp.route('/subir', methods=['GET', 'POST'])
@login_required
@solo_orientador
def subir():
    """
    Formulario y procesamiento para subir un nuevo material.

    GET:  Muestra el formulario de subida.
    POST: Procesa el archivo y guarda el registro en BD.

    Validaciones:
        - El archivo no puede estar vacio
        - Solo se permiten PDF, JPG, JPEG, PNG, GIF, WEBP
        - El titulo es obligatorio

    Retorna:
        GET:  Pagina HTML con el formulario
        POST: Redireccion al listado con mensaje de exito o error
    """
    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        archivo = request.files.get('archivo')

        # Validar titulo
        if not titulo:
            flash('El título es obligatorio.', 'warning')
            return render_template('materiales/subir.html')

        # Validar que se subio un archivo
        if not archivo or archivo.filename == '':
            flash('Debe seleccionar un archivo.', 'warning')
            return render_template('materiales/subir.html')

        # Obtener extension y validarla
        nombre_original = archivo.filename
        extension = nombre_original.rsplit('.', 1)[-1].lower() if '.' in nombre_original else ''

        if extension not in Material.EXTENSIONES_PERMITIDAS:
            flash(
                'Tipo de archivo no permitido. '
                'Use PDF, JPG, JPEG, PNG, GIF o WEBP.',
                'warning'
            )
            return render_template('materiales/subir.html')

        tipo = Material.tipo_desde_extension(extension)

        # Generar nombre unico para evitar colisiones
        nombre_unico = f'{uuid.uuid4().hex}.{extension}'

        # Guardar el archivo en disco
        upload_folder = current_app.config['MATERIALES_UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        archivo.save(os.path.join(upload_folder, nombre_unico))

        # Crear registro en BD
        material = Material(
            titulo=titulo,
            descripcion=descripcion or None,
            tipo_archivo=tipo,
            nombre_archivo=nombre_unico,
            nombre_original=nombre_original,
            subido_por_id=current_user.id,
        )
        db.session.add(material)
        db.session.commit()

        flash(f'Material "{titulo}" subido exitosamente.', 'success')
        return redirect(url_for('materiales.listado'))

    return render_template('materiales/subir.html')


# =============================================================================
# RUTA: SERVIR ARCHIVO
# =============================================================================
@materiales_bp.route('/<int:material_id>/archivo')
@login_required
def archivo(material_id):
    """
    Sirve el archivo del material al usuario autenticado.

    Los PDFs se abren en el navegador (inline).
    Las imagenes se muestran directamente.

    Parametros:
        material_id (int): ID del material a servir

    Retorna:
        El archivo con el Content-Type adecuado
    """
    material = Material.query.get_or_404(material_id)
    upload_folder = current_app.config['MATERIALES_UPLOAD_FOLDER']

    return send_from_directory(
        upload_folder,
        material.nombre_archivo,
        as_attachment=False,
        download_name=material.nombre_original,
    )


# =============================================================================
# RUTA: ELIMINAR MATERIAL
# =============================================================================
@materiales_bp.route('/<int:material_id>/eliminar', methods=['POST'])
@login_required
@solo_orientador
def eliminar(material_id):
    """
    Elimina un material del sistema (BD y disco).

    Solo orientadores y administradores pueden eliminar materiales.

    Parametros:
        material_id (int): ID del material a eliminar

    Retorna:
        Redireccion al listado con mensaje de resultado
    """
    material = Material.query.get_or_404(material_id)

    # Eliminar archivo del disco
    upload_folder = current_app.config['MATERIALES_UPLOAD_FOLDER']
    ruta_archivo = os.path.join(upload_folder, material.nombre_archivo)
    if os.path.exists(ruta_archivo):
        os.remove(ruta_archivo)

    titulo = material.titulo
    db.session.delete(material)
    db.session.commit()

    flash(f'Material "{titulo}" eliminado.', 'success')
    return redirect(url_for('materiales.listado'))
