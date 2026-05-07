from flask import Blueprint, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app import db
from app.models.solicitud_ayuda import SolicitudAyuda
from app.utils.decorators import solo_orientador

ayuda_bp = Blueprint('ayuda', __name__)


@ayuda_bp.route('/solicitar', methods=['POST'])
@login_required
def solicitar():
    """Recibe el mensaje de ayuda enviado por un discente."""
    if not current_user.es_discente():
        flash('Solo los discentes pueden enviar solicitudes de ayuda.', 'danger')
        return redirect(url_for('main.inicio'))

    mensaje = request.form.get('mensaje', '').strip()
    if not mensaje:
        flash('El mensaje no puede estar vacío.', 'warning')
        return redirect(url_for('main.inicio'))

    if len(mensaje) > 1000:
        flash('El mensaje no puede superar los 1000 caracteres.', 'warning')
        return redirect(url_for('main.inicio'))

    solicitud = SolicitudAyuda(usuario_id=current_user.id, mensaje=mensaje)
    db.session.add(solicitud)
    db.session.commit()

    flash('Tu mensaje fue enviado. Un psicólogo o administrador lo atenderá pronto.', 'success')
    return redirect(url_for('main.inicio'))


@ayuda_bp.route('/<int:solicitud_id>/marcar-leida', methods=['POST'])
@login_required
@solo_orientador
def marcar_leida(solicitud_id):
    """Marca una solicitud de ayuda como leída por el orientador/admin."""
    solicitud = SolicitudAyuda.query.get_or_404(solicitud_id)
    if not solicitud.leida:
        solicitud.marcar_leida(current_user.id)
        db.session.commit()
        flash('Solicitud marcada como leída.', 'success')
    return redirect(url_for('alertas.listado'))
