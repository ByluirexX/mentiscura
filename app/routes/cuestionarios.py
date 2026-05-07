"""
================================================================================
MENTIS CURA - Rutas de Cuestionarios
================================================================================
Archivo: routes/cuestionarios.py
Descripcion: Define las rutas para la aplicacion de cuestionarios PHQ-2 y PHQ-9.
             Permite a los discentes ver y responder los cuestionarios.

Rutas disponibles:
    - /cuestionarios/: Lista de cuestionarios disponibles
    - /cuestionarios/<codigo>: Ver y responder un cuestionario
    - /cuestionarios/<codigo>/enviar: Procesar respuestas enviadas

Flujo de uso:
    1. El discente ve la lista de cuestionarios (/cuestionarios/)
    2. Selecciona uno para responder (/cuestionarios/PHQ-9)
    3. Responde todas las preguntas y envia
    4. El sistema procesa las respuestas (/cuestionarios/PHQ-9/enviar)
    5. Se muestra el resultado (/evaluaciones/resultado/X)

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

# Modelos y servicios del proyecto
from app.models.cuestionario import Cuestionario
from app.services.evaluacion_service import EvaluacionService
from app.config import Config


# =============================================================================
# CREAR BLUEPRINT
# =============================================================================
# Blueprint 'cuestionarios' con prefijo de URL /cuestionarios
cuestionarios_bp = Blueprint('cuestionarios', __name__)


# =============================================================================
# RUTA: LISTADO DE CUESTIONARIOS
# =============================================================================
@cuestionarios_bp.route('/')
@login_required
def listado():
    """
    Lista todos los cuestionarios disponibles.

    Muestra los cuestionarios activos que el usuario puede responder.
    Cada cuestionario incluye su nombre, descripcion y puntaje maximo.

    Retorna:
        Pagina HTML con la lista de cuestionarios
    """
    # Obtener solo cuestionarios activos
    cuestionarios = Cuestionario.query.filter_by(activo=True).all()

    return render_template('cuestionarios/listado.html',
                           cuestionarios=cuestionarios)


# =============================================================================
# RUTA: VER CUESTIONARIO PARA RESPONDER
# =============================================================================
@cuestionarios_bp.route('/<string:codigo>')
@login_required
def ver(codigo):
    """
    Muestra un cuestionario para que el usuario lo responda.

    Presenta todas las preguntas del cuestionario con sus opciones
    de respuesta. El usuario selecciona una opcion por pregunta.

    Parametros de URL:
        codigo (str): Codigo del cuestionario (ej: 'PHQ-2', 'PHQ-9')

    Flujo:
        1. Busca el cuestionario por codigo
        2. Si no existe o no esta activo, redirige con mensaje
        3. Obtiene las preguntas ordenadas
        4. Muestra el formulario de respuesta

    Retorna:
        Pagina HTML con el formulario del cuestionario
        O redireccion al listado si no existe
    """
    # Buscar el cuestionario por codigo (debe estar activo)
    cuestionario = Cuestionario.query.filter_by(
        codigo=codigo,
        activo=True
    ).first()

    # Si no existe, mostrar mensaje y volver al listado
    if not cuestionario:
        flash('Cuestionario no encontrado.', 'warning')
        return redirect(url_for('cuestionarios.listado'))

    # Obtener las preguntas ordenadas por numero
    preguntas = cuestionario.obtener_preguntas_ordenadas()

    # Template especifico para ASSIST
    if cuestionario.codigo == 'ASSIST':
        sustancias_info = {
            'tabaco': {'nombre': 'Tabaco', 'ejemplos': 'Cigarrillos, tabaco de mascar, puros, etc.'},
            'alcohol': {'nombre': 'Alcohol', 'ejemplos': 'Cerveza, vino, licores, etc.'},
            'cannabis': {'nombre': 'Cannabis', 'ejemplos': 'Marihuana, mota, hachís, etc.'},
            'cocaina': {'nombre': 'Cocaína', 'ejemplos': 'Coca, crack, etc.'},
            'anfetaminas': {'nombre': 'Anfetaminas', 'ejemplos': 'Speed, éxtasis, metanfetaminas, etc.'},
            'inhalantes': {'nombre': 'Inhalantes', 'ejemplos': 'Pegamento, gasolina, solventes, etc.'},
            'tranquilizantes': {'nombre': 'Tranquilizantes', 'ejemplos': 'Valium, Rivotril, benzodiazepinas, etc.'},
            'alucinogenos': {'nombre': 'Alucinógenos', 'ejemplos': 'LSD, hongos, peyote, ketamina, etc.'},
            'opiaceos': {'nombre': 'Opiáceos', 'ejemplos': 'Heroína, morfina, codeína, tramadol, etc.'}
        }
        preguntas_q1 = [p for p in preguntas if p.grupo_pregunta == 'Q1']
        preguntas_por_sustancia = {}
        for sustancia in Config.ASSIST_SUSTANCIAS:
            preguntas_por_sustancia[sustancia] = [
                p for p in preguntas if p.sustancia == sustancia and p.grupo_pregunta not in ('Q1', 'Q8')
            ]
        pregunta_q8 = next((p for p in preguntas if p.grupo_pregunta == 'Q8'), None)

        return render_template('cuestionarios/responder_assist.html',
                               cuestionario=cuestionario,
                               preguntas_q1=preguntas_q1,
                               preguntas_por_sustancia=preguntas_por_sustancia,
                               pregunta_q8=pregunta_q8,
                               sustancias_info=sustancias_info,
                               sustancias=Config.ASSIST_SUSTANCIAS)

    # Mostrar el formulario para responder
    return render_template('cuestionarios/responder.html',
                           cuestionario=cuestionario,
                           preguntas=preguntas)


# =============================================================================
# RUTA: ENVIAR RESPUESTAS
# =============================================================================
@cuestionarios_bp.route('/<string:codigo>/enviar', methods=['POST'])
@login_required
def enviar(codigo):
    """
    Procesa las respuestas enviadas de un cuestionario.

    Este es el endpoint que recibe el formulario cuando el usuario
    hace clic en "Enviar". Realiza las siguientes acciones:

    1. Valida que el cuestionario exista
    2. Recopila todas las respuestas del formulario
    3. Valida que todas las preguntas tengan respuesta
    4. Procesa la evaluacion (calcula puntaje, clasifica riesgo)
    5. Redirige a la pagina de resultados

    Parametros de URL:
        codigo (str): Codigo del cuestionario

    Datos del formulario:
        pregunta_X: Valor seleccionado para cada pregunta (0-3)

    Retorna:
        Exito: Redireccion a la pagina de resultado
        Error: Redireccion al cuestionario con mensaje de error
    """
    # -------------------------------------------------------------------------
    # Verificar que el cuestionario existe
    # -------------------------------------------------------------------------
    cuestionario = Cuestionario.query.filter_by(
        codigo=codigo,
        activo=True
    ).first()

    if not cuestionario:
        flash('Cuestionario no encontrado.', 'danger')
        return redirect(url_for('cuestionarios.listado'))

    # -------------------------------------------------------------------------
    # Recopilar respuestas del formulario
    # -------------------------------------------------------------------------
    respuestas = {}  # Diccionario {pregunta_id: valor}
    preguntas = cuestionario.obtener_preguntas_ordenadas()

    if cuestionario.codigo == 'ASSIST':
        # ASSIST: Recopilar respuestas con logica condicional
        # Primero obtener Q1 para saber que sustancias fueron usadas
        sustancias_usadas = set()
        for pregunta in preguntas:
            if pregunta.grupo_pregunta == 'Q1':
                campo = f'pregunta_{pregunta.id}'
                valor = request.form.get(campo)
                if valor is None:
                    flash('Por favor responda todas las preguntas de la sección inicial.', 'warning')
                    return redirect(url_for('cuestionarios.ver', codigo=codigo))
                try:
                    respuestas[pregunta.id] = int(valor)
                    if int(valor) > 0:
                        sustancias_usadas.add(pregunta.sustancia)
                except ValueError:
                    flash('Error en los datos enviados.', 'danger')
                    return redirect(url_for('cuestionarios.ver', codigo=codigo))

        # Q2-Q7: Solo requeridas para sustancias usadas
        for pregunta in preguntas:
            if pregunta.grupo_pregunta in ('Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7'):
                campo = f'pregunta_{pregunta.id}'
                valor = request.form.get(campo)
                if pregunta.sustancia in sustancias_usadas:
                    if valor is None:
                        flash(f'Por favor responda todas las preguntas para {pregunta.sustancia}.', 'warning')
                        return redirect(url_for('cuestionarios.ver', codigo=codigo))
                    try:
                        respuestas[pregunta.id] = int(valor)
                    except ValueError:
                        flash('Error en los datos enviados.', 'danger')
                        return redirect(url_for('cuestionarios.ver', codigo=codigo))
                else:
                    # Sustancia no usada: valor 0
                    respuestas[pregunta.id] = 0

        # Q8: Siempre obligatoria
        for pregunta in preguntas:
            if pregunta.grupo_pregunta == 'Q8':
                campo = f'pregunta_{pregunta.id}'
                valor = request.form.get(campo)
                if valor is None:
                    flash('Por favor responda la pregunta sobre uso por vía inyectada.', 'warning')
                    return redirect(url_for('cuestionarios.ver', codigo=codigo))
                try:
                    respuestas[pregunta.id] = int(valor)
                except ValueError:
                    flash('Error en los datos enviados.', 'danger')
                    return redirect(url_for('cuestionarios.ver', codigo=codigo))
    else:
        for pregunta in preguntas:
            # El nombre del campo en el formulario es "pregunta_X"
            campo = f'pregunta_{pregunta.id}'
            valor = request.form.get(campo)

            # Verificar que la pregunta tenga respuesta
            if valor is None:
                flash(f'Por favor responda todas las preguntas.', 'warning')
                return redirect(url_for('cuestionarios.ver', codigo=codigo))

            # Convertir el valor a entero
            try:
                respuestas[pregunta.id] = int(valor)
            except ValueError:
                flash('Error en los datos enviados.', 'danger')
                return redirect(url_for('cuestionarios.ver', codigo=codigo))

    # -------------------------------------------------------------------------
    # Validar las respuestas
    # -------------------------------------------------------------------------
    es_valido, error = EvaluacionService.validar_respuestas(
        cuestionario.id,
        respuestas
    )

    if not es_valido:
        flash(error, 'danger')
        return redirect(url_for('cuestionarios.ver', codigo=codigo))

    # -------------------------------------------------------------------------
    # Procesar la evaluacion
    # -------------------------------------------------------------------------
    try:
        # Crear la evaluacion con el servicio
        evaluacion = EvaluacionService.procesar_evaluacion(
            usuario_id=current_user.id,
            cuestionario_id=cuestionario.id,
            respuestas_dict=respuestas
        )

        # Mostrar mensaje de exito
        flash('Evaluación registrada correctamente.', 'success')

        # Redirigir a la pagina de resultados
        return redirect(url_for('evaluaciones.resultado',
                                evaluacion_id=evaluacion.id))

    except Exception as e:
        # Si hay error, mostrar mensaje y volver al cuestionario
        flash(f'Error al procesar la evaluación: {str(e)}', 'danger')
        return redirect(url_for('cuestionarios.ver', codigo=codigo))
