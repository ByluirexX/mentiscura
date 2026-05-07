from datetime import datetime
from app import db


class SolicitudAyuda(db.Model):
    __tablename__ = 'solicitudes_ayuda'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    mensaje = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    leida = db.Column(db.Boolean, default=False)
    leida_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    fecha_lectura = db.Column(db.DateTime, nullable=True)

    usuario = db.relationship('Usuario', foreign_keys=[usuario_id], backref='solicitudes_ayuda')
    leida_por = db.relationship('Usuario', foreign_keys=[leida_por_id])

    def marcar_leida(self, usuario_id):
        self.leida = True
        self.leida_por_id = usuario_id
        self.fecha_lectura = datetime.utcnow()

    def __repr__(self):
        return f'<SolicitudAyuda {self.id} - usuario {self.usuario_id}>'
