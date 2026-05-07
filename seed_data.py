#!/usr/bin/env python3
"""
================================================================================
MENTIS CURA - Script de Datos Iniciales
================================================================================
Archivo: seed_data.py
Descripcion: Script para poblar la base de datos con datos iniciales de prueba.
             Crea roles, usuarios, cuestionarios, preguntas y evaluaciones
             de ejemplo necesarios para que el sistema funcione.

Uso:
    python seed_data.py

Este script crea:
    1. ROLES (3):
       - administrador: Acceso total al sistema
       - orientador: Gestion de alertas y evaluaciones
       - discente: Responde cuestionarios

    2. USUARIOS DE PRUEBA:
       - 1 administrador (admin / admin123)
       - 2 orientadores (psicologo / psico123, psicologia / psico123)
       - 5 discentes (A20001-E20005 / disc123)

    3. CUESTIONARIOS:
       - PHQ-2: Cuestionario de tamizaje rapido (2 preguntas)
       - PHQ-9: Cuestionario completo (9 preguntas)
       - ASSIST: Evaluacion de consumo de sustancias (variable por sustancia)

    4. EVALUACIONES DE DEMOSTRACION:
       - Ejemplos con diferentes niveles de riesgo
       - Incluye casos con y sin alerta critica (P9 PHQ-9 e inyeccion ASSIST)

NOTA: Los discentes inician sesion usando su MATRICULA como username.
      Por ejemplo: A20001 / disc123

Autor: Luis Enrique Diaz Romero
Fecha: 2026
================================================================================
"""

# =============================================================================
# IMPORTACIONES
# =============================================================================
import os
import sys
from datetime import datetime, timedelta  # Para fechas de evaluaciones
import random  # Para generar datos aleatorios

# Agregar el directorio raiz al path de Python
# Esto permite importar modulos del proyecto correctamente
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar la aplicacion Flask y la base de datos
from app import create_app, db

# Importar todos los modelos necesarios
from app.models import (
    Usuario, Rol, Cuestionario, Pregunta, OpcionRespuesta,
    Evaluacion, Respuesta, Alerta, PuntajeSustancia
)


# =============================================================================
# FUNCION: CREAR ROLES
# =============================================================================
def crear_roles():
    """
    Crea los tres roles del sistema.

    Los roles definen que acciones puede realizar cada tipo de usuario:
    - administrador: Acceso total (usuarios, auditoria, configuracion)
    - orientador: Acceso a alertas, evaluaciones y busqueda de discentes
    - discente: Solo puede responder cuestionarios y ver su historial
    """
    print("Creando roles...")

    # Datos de los roles a crear
    roles_data = [
        {'nombre': 'administrador', 'descripcion': 'Acceso total al sistema'},
        {'nombre': 'orientador', 'descripcion': 'Gestión de alertas y evaluaciones'},
        {'nombre': 'discente', 'descripcion': 'Responde cuestionarios'}
    ]

    # Crear cada rol si no existe
    for rol_data in roles_data:
        # Verificar si el rol ya existe
        if not Rol.query.filter_by(nombre=rol_data['nombre']).first():
            rol = Rol(**rol_data)  # Crear instancia del rol
            db.session.add(rol)    # Agregar a la sesion

    # Guardar todos los roles en la base de datos
    db.session.commit()
    print(f"  ✓ {len(roles_data)} roles creados")


# =============================================================================
# FUNCION: CREAR USUARIOS DE PRUEBA
# =============================================================================
def crear_usuarios():
    """
    Crea usuarios de prueba para cada rol.

    Usuarios creados:
    - admin / admin123 (Administrador)
    - psicologo / psico123 (Orientador)
    - psicologia / psico123 (Orientador)
    - A20001 / disc123 (Discente - usar matricula como usuario)

    """
    print("Creando usuarios...")

    # Obtener los roles (ya deben existir)
    rol_admin = Rol.query.filter_by(nombre='administrador').first()
    rol_orientador = Rol.query.filter_by(nombre='orientador').first()
    rol_discente = Rol.query.filter_by(nombre='discente').first()

    # -------------------------------------------------------------------------
    # Lista de usuarios a crear
    # -------------------------------------------------------------------------
    usuarios_data = [
        # ---- ADMINISTRADOR ----
        {
            'username': 'admin',
            'password': 'admin123',
            'nombre': 'Administrador',
            'apellido_paterno': 'Sistema',
            'apellido_materno': None,
            'rol': rol_admin,
            'matricula': None
        },
        # ---- ORIENTADORES ----
        {
            'username': 'psicologo',
            'password': 'psico123',
            'nombre': 'María',
            'apellido_paterno': 'González',
            'apellido_materno': 'Pérez',
            'rol': rol_orientador,
            'matricula': None
        },
        {
            'username': 'psicologia',
            'password': 'psico123',
            'nombre': 'Carlos',
            'apellido_paterno': 'Rodríguez',
            'apellido_materno': 'Luna',
            'rol': rol_orientador,
            'matricula': None
        },
        # ---- DISCENTES ----
        # Nota: Los discentes usan su matricula como username
        {
            'username': 'A20001',  # La matricula es el username
            'password': 'disc123',
            'nombre': 'Juan Carlos',
            'apellido_paterno': 'Pérez',
            'apellido_materno': 'Martínez',
            'rol': rol_discente,
            'matricula': 'A20001',
            'edad': 20,
            'anio_cursa': 2,
            'carrera': 'ing_computacion',
            'compania': 'primera'
        },
        {
            'username': 'B20002',
            'password': 'disc123',
            'nombre': 'Ana Sofía',
            'apellido_paterno': 'López',
            'apellido_materno': 'García',
            'rol': rol_discente,
            'matricula': 'B20002',
            'edad': 19,
            'anio_cursa': 1,
            'carrera': 'tronco_comun',
            'compania': 'segunda'
        },
        {
            'username': 'C20003',
            'password': 'disc123',
            'nombre': 'Pedro',
            'apellido_paterno': 'Sánchez',
            'apellido_materno': 'Ruiz',
            'rol': rol_discente,
            'matricula': 'C20003',
            'edad': 21,
            'anio_cursa': 3,
            'carrera': 'ing_industrial',
            'compania': 'tercera'
        },
        {
            'username': 'D20004',
            'password': 'disc123',
            'nombre': 'Laura',
            'apellido_paterno': 'Hernández',
            'apellido_materno': 'Díaz',
            'rol': rol_discente,
            'matricula': 'D20004',
            'edad': 22,
            'anio_cursa': 4,
            'carrera': 'ing_comunicaciones',
            'compania': 'cuarta'
        },
        {
            'username': 'E20005',
            'password': 'disc123',
            'nombre': 'Miguel Ángel',
            'apellido_paterno': 'Torres',
            'apellido_materno': 'Vargas',
            'rol': rol_discente,
            'matricula': 'E20005',
            'edad': 23,
            'anio_cursa': 5,
            'carrera': 'ing_construccion',
            'compania': 'oficiales'
        }
    ]

    # -------------------------------------------------------------------------
    # Crear cada usuario si no existe
    # -------------------------------------------------------------------------
    for u_data in usuarios_data:
        # Verificar si el usuario ya existe
        if not Usuario.query.filter_by(username=u_data['username']).first():
            # Crear instancia del usuario
            usuario = Usuario(
                username=u_data['username'],
                nombre=u_data['nombre'],
                apellido_paterno=u_data['apellido_paterno'],
                apellido_materno=u_data.get('apellido_materno'),
                rol_id=u_data['rol'].id,
                matricula=u_data.get('matricula'),
                edad=u_data.get('edad'),
                anio_cursa=u_data.get('anio_cursa'),
                carrera=u_data.get('carrera'),
                compania=u_data.get('compania'),
                activo=True
            )
            # Establecer la contraseña (se guarda como hash)
            usuario.set_password(u_data['password'])
            db.session.add(usuario)

    # Guardar todos los usuarios
    db.session.commit()
    print(f"  ✓ {len(usuarios_data)} usuarios creados")


# =============================================================================
# FUNCION: CREAR CUESTIONARIO PHQ-2
# =============================================================================
def crear_cuestionario_phq2():
    """
    Crea el cuestionario PHQ-2.

    El PHQ-2 es un instrumento de tamizaje rapido con solo 2 preguntas.
    Se usa como filtro inicial para detectar posibles indicadores de riesgo.

    Interpretacion:
    - Puntaje < 3: Sin indicador de riesgo
    - Puntaje >= 3: Indicador positivo (sugiere aplicar PHQ-9)

    Puntaje maximo: 6 (2 preguntas x 3 puntos)
    """
    print("Creando cuestionario PHQ-2...")

    # Verificar si ya existe
    if Cuestionario.query.filter_by(codigo='PHQ-2').first():
        print("  - PHQ-2 ya existe, omitiendo...")
        return

    # Crear el cuestionario
    phq2 = Cuestionario(
        codigo='PHQ-2',
        nombre='Cuestionario de Salud del Paciente (PHQ-2)',
        descripcion='Instrumento de tamizaje breve para detectar síntomas depresivos. '
                    'Evalúa la frecuencia de anhedonia y estado de ánimo deprimido.',
        instrucciones='Durante las ÚLTIMAS 2 SEMANAS, ¿con qué frecuencia le han molestado '
                      'los siguientes problemas?',
        puntaje_minimo=0,
        puntaje_maximo=6,  # 2 preguntas x 3 puntos maximo cada una
        activo=True
    )
    db.session.add(phq2)
    db.session.flush()  # Obtener el ID sin hacer commit

    # -------------------------------------------------------------------------
    # Preguntas del PHQ-2
    # -------------------------------------------------------------------------
    preguntas_phq2 = [
        'Tener poco interés o placer en hacer las cosas',
        'Sentirse desanimado/a, deprimido/a, o sin esperanza'
    ]

    # Opciones de respuesta (escala Likert de 4 puntos)
    opciones = [
        ('Nunca', 0),
        ('Varios días', 1),
        ('Más de la mitad de los días', 2),
        ('Casi todos los días', 3)
    ]

    # Crear cada pregunta con sus opciones
    for i, texto in enumerate(preguntas_phq2, 1):
        # Crear la pregunta
        pregunta = Pregunta(
            cuestionario_id=phq2.id,
            orden=i,        # Numero de pregunta (1, 2)
            texto=texto,
            es_critica=False  # PHQ-2 no tiene preguntas criticas
        )
        db.session.add(pregunta)
        db.session.flush()

        # Crear las 4 opciones de respuesta para esta pregunta
        for texto_opcion, valor in opciones:
            opcion = OpcionRespuesta(
                pregunta_id=pregunta.id,
                texto=texto_opcion,
                valor=valor
            )
            db.session.add(opcion)

    db.session.commit()
    print("  ✓ PHQ-2 creado con 2 preguntas")


# =============================================================================
# FUNCION: CREAR CUESTIONARIO PHQ-9
# =============================================================================
def crear_cuestionario_phq9():
    """
    Crea el cuestionario PHQ-9.

    El PHQ-9 es un instrumento estandarizado con 9 preguntas que evalua
    la severidad de sintomas depresivos. Esta basado en los criterios
    diagnosticos del DSM.

    IMPORTANTE: La pregunta 9 evalua ideacion suicida. Cualquier
    respuesta >= 1 en esta pregunta genera una ALERTA CRITICA automatica.

    Clasificacion por puntaje:
    - 0-4: Minimo o ninguno
    - 5-9: Leve
    - 10-14: Moderado
    - 15-19: Moderadamente severo
    - 20-27: Severo

    Puntaje maximo: 27 (9 preguntas x 3 puntos)
    """
    print("Creando cuestionario PHQ-9...")

    # Verificar si ya existe
    if Cuestionario.query.filter_by(codigo='PHQ-9').first():
        print("  - PHQ-9 ya existe, omitiendo...")
        return

    # Crear el cuestionario
    phq9 = Cuestionario(
        codigo='PHQ-9',
        nombre='Cuestionario de Salud del Paciente (PHQ-9)',
        descripcion='Instrumento estandarizado para evaluar la severidad de síntomas depresivos. '
                    'Incluye 9 ítems basados en criterios del DSM.',
        instrucciones='Durante las ÚLTIMAS 2 SEMANAS, ¿con qué frecuencia le han molestado '
                      'los siguientes problemas? Seleccione la opción que mejor describa '
                      'su experiencia.',
        puntaje_minimo=0,
        puntaje_maximo=27,  # 9 preguntas x 3 puntos maximo
        activo=True
    )
    db.session.add(phq9)
    db.session.flush()

    # -------------------------------------------------------------------------
    # Preguntas del PHQ-9
    # -------------------------------------------------------------------------
    # Cada tupla contiene: (texto, es_critica)
    # La pregunta 9 es critica porque evalua ideacion suicida
    preguntas_phq9 = [
        ('Tener poco interés o placer en hacer las cosas', False),
        ('Sentirse desanimado/a, deprimido/a, o sin esperanza', False),
        ('Tener dificultad para dormir o permanecer dormido/a, o dormir demasiado', False),
        ('Sentirse cansado/a o tener poca energía', False),
        ('Tener poco apetito o comer en exceso', False),
        ('Sentirse mal consigo mismo/a, sentir que es un fracaso o que se ha fallado '
         'a sí mismo/a o a su familia', False),
        ('Tener dificultad para concentrarse en cosas tales como leer el periódico '
         'o ver televisión', False),
        ('Moverse o hablar tan despacio que otras personas lo han notado, o lo contrario, '
         'estar tan agitado/a o inquieto/a que se mueve mucho más de lo normal', False),
        # PREGUNTA 9: CRITICA - Ideacion suicida
        ('Tener pensamientos de que estaría mejor muerto/a o de hacerse daño de alguna manera', True)
    ]

    # Opciones de respuesta (igual que PHQ-2)
    opciones = [
        ('Nunca', 0),
        ('Varios días', 1),
        ('Más de la mitad de los días', 2),
        ('Casi todos los días', 3)
    ]

    # Crear cada pregunta con sus opciones
    for i, (texto, es_critica) in enumerate(preguntas_phq9, 1):
        pregunta = Pregunta(
            cuestionario_id=phq9.id,
            orden=i,
            texto=texto,
            es_critica=es_critica  # Solo la pregunta 9 es critica
        )
        db.session.add(pregunta)
        db.session.flush()

        # Crear las opciones de respuesta
        for texto_opcion, valor in opciones:
            opcion = OpcionRespuesta(
                pregunta_id=pregunta.id,
                texto=texto_opcion,
                valor=valor
            )
            db.session.add(opcion)

    db.session.commit()
    print("  ✓ PHQ-9 creado con 9 preguntas")


# =============================================================================
# FUNCION: CREAR EVALUACIONES DE DEMOSTRACION
# =============================================================================
def crear_evaluaciones_demo():
    """
    Crea evaluaciones de demostracion para probar el sistema.

    Esto permite que los orientadores vean como se ven las alertas
    y evaluaciones sin necesidad de que los discentes respondan
    cuestionarios reales.

    Las evaluaciones incluyen diferentes escenarios:
    - Riesgo minimo (sin alerta)
    - Riesgo leve (alerta baja)
    - Riesgo moderado (alerta media)
    - Riesgo severo con P9 positiva (alerta critica)
    """
    print("Creando evaluaciones de demostración...")

    # Obtener los cuestionarios
    phq9 = Cuestionario.query.filter_by(codigo='PHQ-9').first()
    phq2 = Cuestionario.query.filter_by(codigo='PHQ-2').first()

    if not phq9 or not phq2:
        print("  ! Cuestionarios no encontrados, omitiendo evaluaciones...")
        return

    # Obtener todos los discentes
    discentes = Usuario.query.join(Rol).filter(Rol.nombre == 'discente').all()

    evaluaciones_creadas = 0

    # -------------------------------------------------------------------------
    # Escenarios de evaluacion
    # -------------------------------------------------------------------------
    # Cada escenario es: (indice_discente, codigo_cuestionario, respuestas, dias_atras)
    escenarios = [
        # Discente 0: Dos evaluaciones (minimo y leve)
        (0, 'PHQ-9', [0, 0, 1, 1, 0, 0, 0, 0, 0], 30),  # Puntaje 2: Minimo
        (0, 'PHQ-9', [1, 1, 1, 1, 0, 0, 1, 0, 0], 15),  # Puntaje 5: Leve

        # Discente 1: Moderado y PHQ-2 alto
        (1, 'PHQ-9', [2, 2, 2, 2, 1, 1, 1, 1, 0], 20),  # Puntaje 12: Moderado
        (1, 'PHQ-2', [2, 2], 10),  # Puntaje 4: Indicador positivo

        # Discente 2: Moderado-Severo CON P9 positiva (genera alerta critica)
        (2, 'PHQ-9', [3, 3, 2, 2, 2, 2, 2, 1, 1], 5),   # P9=1: Alerta critica

        # Discente 3: Leve y PHQ-2 bajo
        (3, 'PHQ-9', [1, 0, 1, 1, 0, 0, 0, 0, 0], 25),  # Puntaje 3: Minimo
        (3, 'PHQ-2', [1, 1], 12),  # Puntaje 2: Sin indicador

        # Discente 4: Moderado
        (4, 'PHQ-9', [2, 2, 1, 2, 1, 1, 1, 0, 0], 8),   # Puntaje 10: Moderado
    ]

    # -------------------------------------------------------------------------
    # Crear cada evaluacion
    # -------------------------------------------------------------------------
    for idx, codigo, respuestas, dias in escenarios:
        # Verificar que el indice sea valido
        if idx >= len(discentes):
            continue

        usuario = discentes[idx]
        cuestionario = phq9 if codigo == 'PHQ-9' else phq2
        preguntas = cuestionario.obtener_preguntas_ordenadas()

        # Verificar que el numero de respuestas coincida
        if len(respuestas) != len(preguntas):
            continue

        # Calcular puntaje total
        puntaje_total = sum(respuestas)

        # ---------------------------------------------------------------------
        # Clasificar nivel de riesgo segun puntaje
        # ---------------------------------------------------------------------
        if codigo == 'PHQ-2':
            # PHQ-2: >= 3 indica riesgo
            nivel_riesgo = 'moderado' if puntaje_total >= 3 else 'minimo'
        else:
            # PHQ-9: Clasificacion en 5 niveles
            if puntaje_total <= 4:
                nivel_riesgo = 'minimo'
            elif puntaje_total <= 9:
                nivel_riesgo = 'leve'
            elif puntaje_total <= 14:
                nivel_riesgo = 'moderado'
            elif puntaje_total <= 19:
                nivel_riesgo = 'moderado_severo'
            else:
                nivel_riesgo = 'severo'

        # ---------------------------------------------------------------------
        # Detectar pregunta critica (P9 del PHQ-9)
        # ---------------------------------------------------------------------
        alerta_critica = False
        puntaje_critica = 0
        if codigo == 'PHQ-9' and len(respuestas) == 9:
            puntaje_critica = respuestas[8]  # Indice 8 = pregunta 9
            alerta_critica = puntaje_critica >= 1

        # ---------------------------------------------------------------------
        # Crear la evaluacion
        # ---------------------------------------------------------------------
        evaluacion = Evaluacion(
            usuario_id=usuario.id,
            cuestionario_id=cuestionario.id,
            puntaje_total=puntaje_total,
            nivel_riesgo=nivel_riesgo,
            alerta_pregunta_critica=alerta_critica,
            puntaje_pregunta_critica=puntaje_critica,
            # Fecha en el pasado segun dias especificados
            fecha_evaluacion=datetime.utcnow() - timedelta(days=dias)
        )
        db.session.add(evaluacion)
        db.session.flush()

        # ---------------------------------------------------------------------
        # Crear las respuestas individuales
        # ---------------------------------------------------------------------
        for pregunta, valor in zip(preguntas, respuestas):
            respuesta = Respuesta(
                evaluacion_id=evaluacion.id,
                pregunta_id=pregunta.id,
                valor=valor
            )
            db.session.add(respuesta)

        # ---------------------------------------------------------------------
        # Crear alerta si corresponde
        # ---------------------------------------------------------------------
        if alerta_critica:
            # Alerta critica por P9 positiva
            alerta = Alerta(
                usuario_id=usuario.id,
                evaluacion_id=evaluacion.id,
                tipo='pregunta_critica',
                prioridad='critica',
                mensaje=f'ATENCIÓN PRIORITARIA: El discente ha indicado un valor de '
                        f'{puntaje_critica} en la pregunta sobre pensamientos de hacerse daño.',
                estado='pendiente'
            )
            db.session.add(alerta)
        elif nivel_riesgo in ['moderado', 'moderado_severo', 'severo']:
            # Alerta por nivel de riesgo elevado
            prioridad = 'media' if nivel_riesgo == 'moderado' else 'alta'
            alerta = Alerta(
                usuario_id=usuario.id,
                evaluacion_id=evaluacion.id,
                tipo='puntaje_riesgo',
                prioridad=prioridad,
                mensaje=f'Evaluación {codigo} completada con nivel de riesgo '
                        f'{nivel_riesgo.replace("_", " ")} (puntaje: {puntaje_total}).',
                estado='pendiente'
            )
            db.session.add(alerta)

        evaluaciones_creadas += 1

    db.session.commit()
    print(f"  ✓ {evaluaciones_creadas} evaluaciones de demostración creadas")


# =============================================================================
# FUNCION: CREAR CUESTIONARIO ASSIST
# =============================================================================
def crear_cuestionario_assist():
    """
    Crea el cuestionario ASSIST (Alcohol, Smoking and Substance Involvement
    Screening Test) de la OMS v3.1.

    El ASSIST evalua 9 sustancias de forma independiente con flujo condicional.
    Total: 64 preguntas (9 Q1 + 54 Q2-Q7 + 1 Q8)

    Estructura:
    - Q1: Uso alguna vez (9 preguntas, una por sustancia)
    - Q2-Q7: Preguntas detalladas por sustancia (54 preguntas)
    - Q8: Uso por via inyectada (1 pregunta)
    """
    print("Creando cuestionario ASSIST...")

    if Cuestionario.query.filter_by(codigo='ASSIST').first():
        print("  - ASSIST ya existe, omitiendo...")
        return

    assist = Cuestionario(
        codigo='ASSIST',
        nombre='Prueba de Detección de Consumo de Alcohol, Tabaco y Sustancias (ASSIST)',
        descripcion='Instrumento de tamizaje de la OMS para detectar el nivel de riesgo '
                    'asociado al consumo de diversas sustancias. Evalúa 9 sustancias de '
                    'forma independiente.',
        instrucciones='Las siguientes preguntas se refieren a su experiencia con el consumo '
                      'de alcohol, tabaco y otras sustancias a lo largo de su vida y en los '
                      'últimos tres meses. Responda con honestidad; sus respuestas son '
                      'confidenciales y serán utilizadas únicamente para brindarle mejor atención.',
        puntaje_minimo=0,
        puntaje_maximo=351,
        activo=True
    )
    db.session.add(assist)
    db.session.flush()

    # Sustancias evaluadas
    sustancias = [
        'tabaco', 'alcohol', 'cannabis', 'cocaina', 'anfetaminas',
        'inhalantes', 'tranquilizantes', 'alucinogenos', 'opiaceos'
    ]

    sustancias_textos = {
        'tabaco': 'tabaco (cigarrillos, tabaco de mascar, puros, etc.)',
        'alcohol': 'bebidas alcohólicas (cerveza, vino, licores, etc.)',
        'cannabis': 'cannabis (marihuana, mota, hachís, etc.)',
        'cocaina': 'cocaína (coca, crack, etc.)',
        'anfetaminas': 'estimulantes de tipo anfetamina (speed, éxtasis, metanfetaminas, etc.)',
        'inhalantes': 'inhalantes (pegamento, gasolina, solventes, etc.)',
        'tranquilizantes': 'tranquilizantes o pastillas para dormir (Valium, Rivotril, benzodiazepinas, etc.)',
        'alucinogenos': 'alucinógenos (LSD, hongos, peyote, ketamina, etc.)',
        'opiaceos': 'opiáceos (heroína, morfina, codeína, tramadol, etc.)'
    }

    # Opciones para Q1
    opciones_q1 = [('No', 0), ('Sí', 1)]

    # Opciones para Q2-Q5
    opciones_q2_q5 = [
        ('Nunca', 0),
        ('Una o dos veces', 2),
        ('Mensualmente', 3),
        ('Semanalmente', 4),
        ('Diariamente o casi diariamente', 6)
    ]

    # Opciones para Q6-Q7
    opciones_q6_q7 = [
        ('No, nunca', 0),
        ('Sí, pero no en los últimos 3 meses', 3),
        ('Sí, en los últimos 3 meses', 6)
    ]

    # Textos de Q2-Q7
    textos_preguntas = {
        'Q2': 'En los últimos 3 meses, ¿con qué frecuencia ha consumido {sustancia}?',
        'Q3': 'En los últimos 3 meses, ¿con qué frecuencia ha tenido un fuerte deseo o '
              'ansias de consumir {sustancia}?',
        'Q4': 'En los últimos 3 meses, ¿con qué frecuencia le ha causado problemas de salud, '
              'sociales, legales o económicos el consumo de {sustancia}?',
        'Q5': 'En los últimos 3 meses, ¿con qué frecuencia dejó de hacer lo que se esperaba '
              'de usted habitualmente por el consumo de {sustancia}?',
        'Q6': '¿Un amigo, familiar o alguien más alguna vez ha mostrado preocupación por su '
              'consumo de {sustancia}?',
        'Q7': '¿Ha intentado alguna vez reducir o eliminar el consumo de {sustancia} sin lograrlo?'
    }

    orden = 1

    # -------------------------------------------------------------------------
    # Q1: Uso alguna vez en la vida (9 preguntas)
    # -------------------------------------------------------------------------
    for sustancia in sustancias:
        pregunta = Pregunta(
            cuestionario_id=assist.id,
            orden=orden,
            texto=f'¿Ha consumido alguna vez {sustancias_textos[sustancia]}?',
            es_critica=False,
            sustancia=sustancia,
            grupo_pregunta='Q1'
        )
        db.session.add(pregunta)
        db.session.flush()

        for texto_op, valor in opciones_q1:
            db.session.add(OpcionRespuesta(
                pregunta_id=pregunta.id, texto=texto_op, valor=valor
            ))
        orden += 1

    # -------------------------------------------------------------------------
    # Q2-Q7: Preguntas detalladas por sustancia (54 preguntas)
    # -------------------------------------------------------------------------
    for sustancia in sustancias:
        for grupo in ['Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7']:
            texto = textos_preguntas[grupo].format(sustancia=sustancias_textos[sustancia])
            pregunta = Pregunta(
                cuestionario_id=assist.id,
                orden=orden,
                texto=texto,
                es_critica=False,
                sustancia=sustancia,
                grupo_pregunta=grupo
            )
            db.session.add(pregunta)
            db.session.flush()

            opciones = opciones_q2_q5 if grupo in ('Q2', 'Q3', 'Q4', 'Q5') else opciones_q6_q7
            for texto_op, valor in opciones:
                db.session.add(OpcionRespuesta(
                    pregunta_id=pregunta.id, texto=texto_op, valor=valor
                ))
            orden += 1

    # -------------------------------------------------------------------------
    # Q8: Uso por via inyectada (1 pregunta)
    # -------------------------------------------------------------------------
    opciones_q8 = [
        ('No, nunca', 0),
        ('Sí, pero no en los últimos 3 meses', 1),
        ('Sí, en los últimos 3 meses', 2)
    ]

    pregunta_q8 = Pregunta(
        cuestionario_id=assist.id,
        orden=orden,
        texto='¿Ha consumido alguna vez alguna droga por vía inyectada (inyecciones no recetadas)?',
        es_critica=True,
        sustancia=None,
        grupo_pregunta='Q8'
    )
    db.session.add(pregunta_q8)
    db.session.flush()

    for texto_op, valor in opciones_q8:
        db.session.add(OpcionRespuesta(
            pregunta_id=pregunta_q8.id, texto=texto_op, valor=valor
        ))

    db.session.commit()
    print(f"  ✓ ASSIST creado con {orden} preguntas (9 Q1 + 54 Q2-Q7 + 1 Q8)")


# =============================================================================
# FUNCION: CREAR EVALUACIONES DEMO ASSIST
# =============================================================================
def crear_evaluaciones_demo_assist():
    """
    Crea evaluaciones de demostracion para ASSIST con escenarios variados.
    """
    print("Creando evaluaciones ASSIST de demostración...")

    assist = Cuestionario.query.filter_by(codigo='ASSIST').first()
    if not assist:
        print("  ! ASSIST no encontrado, omitiendo...")
        return

    from app.models.usuario import Rol
    discentes = Usuario.query.join(Rol).filter(Rol.nombre == 'discente').all()
    if len(discentes) < 2:
        print("  ! Insuficientes discentes, omitiendo...")
        return

    preguntas = assist.obtener_preguntas_ordenadas()
    preguntas_map = {p.id: p for p in preguntas}

    # Escenario 1: Discente 3 - Alcohol moderado, tabaco bajo
    usuario = discentes[3] if len(discentes) > 3 else discentes[0]
    respuestas_vals = {}

    # Q1: Si para tabaco y alcohol, No para el resto
    for p in preguntas:
        if p.grupo_pregunta == 'Q1':
            if p.sustancia in ('tabaco', 'alcohol'):
                respuestas_vals[p.id] = 1
            else:
                respuestas_vals[p.id] = 0

    # Q2-Q7 para tabaco (bajo: SSIS=3)
    for p in preguntas:
        if p.sustancia == 'tabaco' and p.grupo_pregunta in ('Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7'):
            if p.grupo_pregunta == 'Q2':
                respuestas_vals[p.id] = 3  # Mensualmente
            else:
                respuestas_vals[p.id] = 0
        elif p.sustancia == 'alcohol' and p.grupo_pregunta in ('Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7'):
            if p.grupo_pregunta == 'Q2':
                respuestas_vals[p.id] = 4  # Semanalmente
            elif p.grupo_pregunta == 'Q3':
                respuestas_vals[p.id] = 3  # Mensualmente
            elif p.grupo_pregunta == 'Q6':
                respuestas_vals[p.id] = 6  # Si, ultimos 3 meses
            else:
                respuestas_vals[p.id] = 0
        elif p.sustancia not in ('tabaco', 'alcohol') and p.grupo_pregunta in ('Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7'):
            respuestas_vals[p.id] = 0

    # Q8: No
    for p in preguntas:
        if p.grupo_pregunta == 'Q8':
            respuestas_vals[p.id] = 0

    # Calcular SSIS
    ssis_tabaco = sum(respuestas_vals[p.id] for p in preguntas
                      if p.sustancia == 'tabaco' and p.grupo_pregunta in ('Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7'))
    ssis_alcohol = sum(respuestas_vals[p.id] for p in preguntas
                       if p.sustancia == 'alcohol' and p.grupo_pregunta in ('Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7'))

    # Clasificar riesgo
    nivel_tabaco = 'bajo' if ssis_tabaco <= 3 else ('moderado' if ssis_tabaco <= 26 else 'alto')
    nivel_alcohol = 'bajo' if ssis_alcohol <= 10 else ('moderado' if ssis_alcohol <= 26 else 'alto')

    # Nivel global
    jerarquia = {'bajo': 0, 'moderado': 1, 'alto': 2}
    nivel_global = 'moderado' if jerarquia.get(nivel_alcohol, 0) > jerarquia.get(nivel_tabaco, 0) else nivel_tabaco
    if jerarquia.get(nivel_alcohol, 0) > jerarquia.get(nivel_global, 0):
        nivel_global = nivel_alcohol

    evaluacion = Evaluacion(
        usuario_id=usuario.id,
        cuestionario_id=assist.id,
        puntaje_total=ssis_tabaco + ssis_alcohol,
        nivel_riesgo=nivel_global,
        alerta_pregunta_critica=False,
        puntaje_pregunta_critica=0,
        fecha_evaluacion=datetime.utcnow() - timedelta(days=7)
    )
    db.session.add(evaluacion)
    db.session.flush()

    for pid, val in respuestas_vals.items():
        db.session.add(Respuesta(evaluacion_id=evaluacion.id, pregunta_id=pid, valor=val))

    # Puntajes por sustancia
    if ssis_tabaco > 0 or nivel_tabaco != 'bajo':
        db.session.add(PuntajeSustancia(
            evaluacion_id=evaluacion.id, sustancia='tabaco',
            puntaje=ssis_tabaco, nivel_riesgo=nivel_tabaco
        ))
    db.session.add(PuntajeSustancia(
        evaluacion_id=evaluacion.id, sustancia='alcohol',
        puntaje=ssis_alcohol, nivel_riesgo=nivel_alcohol
    ))

    # Alerta si aplica
    if nivel_global == 'moderado':
        db.session.add(Alerta(
            usuario_id=usuario.id, evaluacion_id=evaluacion.id,
            tipo='puntaje_riesgo', prioridad='media',
            mensaje=f'Evaluación ASSIST completada con riesgo MODERADO en: Alcohol. '
                    f'Se sugiere intervención breve según protocolo.',
            estado='pendiente'
        ))

    db.session.commit()
    print("  ✓ 1 evaluación ASSIST de demostración creada")


# =============================================================================
# FUNCION: CREAR CUESTIONARIO IDERE-E (ESTADO)
# =============================================================================
def crear_cuestionario_idere_e():
    """
    Crea el cuestionario IDERE-E (Inventario de Depresion Estado-Rasgo, subescala Estado).

    Evalua como se siente el estudiante AHORA MISMO.
    20 items en escala 1-4 (Nada, Algo, Bastante, Mucho).

    Items directos (D): mayor respuesta = mas depresion.
    Items inversos (I): mayor respuesta = menos depresion (valor invertido en BD).

    Puntaje total: 20-80.
    Clasificacion:
    - 20-24: Bajo (sin indicador significativo)
    - 25-36: Moderado (indicador leve-moderado)
    - 37-80: Alto (indicador severo)
    """
    print("Creando cuestionario IDERE-E...")

    if Cuestionario.query.filter_by(codigo='IDERE-E').first():
        print("  - IDERE-E ya existe, omitiendo...")
        return

    idere_e = Cuestionario(
        codigo='IDERE-E',
        nombre='Inventario de Depresión Estado (IDERE-E)',
        descripcion='Subescala Estado del Inventario de Depresión Estado-Rasgo (IDERE). '
                    'Evalúa síntomas depresivos en el momento actual de la evaluación.',
        instrucciones='A continuación encontrará una serie de frases que describen cómo '
                      'se puede sentir una persona. Lea cada frase e indique cómo se siente '
                      'AHORA MISMO, en este momento. No hay respuestas buenas ni malas. '
                      'Responda con sinceridad.',
        puntaje_minimo=20,
        puntaje_maximo=80,
        activo=True
    )
    db.session.add(idere_e)
    db.session.flush()

    # -------------------------------------------------------------------------
    # Items del IDERE-E
    # Cada tupla: (texto, es_directo)
    # Directo (True): Nada=1, Algo=2, Bastante=3, Mucho=4
    # Inverso (False): Nada=4, Algo=3, Bastante=2, Mucho=1
    # -------------------------------------------------------------------------
    items_idere_e = [
        ('Me siento animado/a',                                           False),  # I
        ('Me siento triste',                                              True),   # D
        ('Me siento satisfecho/a conmigo mismo/a',                        False),  # I
        ('Me siento cansado/a sin razón aparente',                        True),   # D
        ('Me siento tranquilo/a',                                         False),  # I
        ('Me siento deprimido/a',                                         True),   # D
        ('Me siento con ganas de hacer cosas',                            False),  # I
        ('Tengo ganas de llorar',                                         True),   # D
        ('Me siento contento/a',                                          False),  # I
        ('Me siento apático/a (sin interés por nada)',                    True),   # D
        ('Me siento esperanzado/a respecto al futuro',                    False),  # I
        ('Me siento sin valor (inútil)',                                   True),   # D
        ('Me siento seguro/a de mí mismo/a',                              False),  # I
        ('Me siento desesperanzado/a',                                    True),   # D
        ('Me siento alegre',                                              False),  # I
        ('Me siento abatido/a',                                           True),   # D
        ('Me siento relajado/a',                                          False),  # I
        ('Me cuesta disfrutar las cosas que normalmente me gustan',       True),   # D
        ('Me siento optimista',                                           False),  # I
        ('Me siento sin energía',                                         True),   # D
    ]

    opciones_directas = [('Nada', 1), ('Algo', 2), ('Bastante', 3), ('Mucho', 4)]
    opciones_inversas = [('Nada', 4), ('Algo', 3), ('Bastante', 2), ('Mucho', 1)]

    for i, (texto, es_directo) in enumerate(items_idere_e, 1):
        pregunta = Pregunta(
            cuestionario_id=idere_e.id,
            orden=i,
            texto=texto,
            es_critica=False
        )
        db.session.add(pregunta)
        db.session.flush()

        opciones = opciones_directas if es_directo else opciones_inversas
        for texto_opcion, valor in opciones:
            db.session.add(OpcionRespuesta(
                pregunta_id=pregunta.id,
                texto=texto_opcion,
                valor=valor
            ))

    db.session.commit()
    print("  ✓ IDERE-E creado con 20 ítems")


# =============================================================================
# FUNCION: CREAR CUESTIONARIO IDERE-R (RASGO)
# =============================================================================
def crear_cuestionario_idere_r():
    """
    Crea el cuestionario IDERE-R (Inventario de Depresion Estado-Rasgo, subescala Rasgo).

    Evalua como se siente el estudiante EN GENERAL (tendencia estable).
    20 items en escala 1-4 (Nunca, Algunas veces, Frecuentemente, Casi siempre).

    Items directos (D): mayor respuesta = mas depresion.
    Items inversos (I): mayor respuesta = menos depresion (valor invertido en BD).

    Puntaje total: 20-80.
    Clasificacion igual que IDERE-E.
    """
    print("Creando cuestionario IDERE-R...")

    if Cuestionario.query.filter_by(codigo='IDERE-R').first():
        print("  - IDERE-R ya existe, omitiendo...")
        return

    idere_r = Cuestionario(
        codigo='IDERE-R',
        nombre='Inventario de Depresión Rasgo (IDERE-R)',
        descripcion='Subescala Rasgo del Inventario de Depresión Estado-Rasgo (IDERE). '
                    'Evalúa la tendencia estable a experimentar síntomas depresivos.',
        instrucciones='A continuación encontrará una serie de frases que describen cómo '
                      'se puede sentir una persona. Lea cada frase e indique cómo se siente '
                      'EN GENERAL, es decir, cómo suele sentirse habitualmente. '
                      'No hay respuestas buenas ni malas. Responda con sinceridad.',
        puntaje_minimo=20,
        puntaje_maximo=80,
        activo=True
    )
    db.session.add(idere_r)
    db.session.flush()

    # -------------------------------------------------------------------------
    # Items del IDERE-R
    # Cada tupla: (texto, es_directo)
    # -------------------------------------------------------------------------
    items_idere_r = [
        ('En general, me siento bien',                                        False),  # I
        ('Me canso con facilidad',                                            True),   # D
        ('Me siento deprimido/a',                                             True),   # D
        ('Me gustaría ser tan feliz como los demás parecen ser',              True),   # D
        ('Soy una persona feliz',                                             False),  # I
        ('Me siento un fracaso',                                              True),   # D
        ('Soy una persona optimista',                                         False),  # I
        ('Siento que las dificultades se acumulan y no puedo superarlas',     True),   # D
        ('Me preocupo demasiado por cosas que en realidad no importan',       True),   # D
        ('Disfruto de las actividades que hago habitualmente',                False),  # I
        ('Me resulta difícil encontrarle sentido a las cosas',                True),   # D
        ('Me falta confianza en mí mismo/a',                                  True),   # D
        ('Me siento seguro/a de mí mismo/a',                                  False),  # I
        ('Evito enfrentar los problemas',                                     True),   # D
        ('Me siento melancólico/a con frecuencia',                            True),   # D
        ('Me siento satisfecho/a con mi vida',                                False),  # I
        ('Me siento vacío/a interiormente',                                   True),   # D
        ('Los desengaños me afectan mucho y no me los puedo quitar de encima', True),  # D
        ('Me siento emocionalmente estable',                                  False),  # I
        ('Me siento sin motivación para hacer las cosas',                     True),   # D
    ]

    opciones_directas = [('Nunca', 1), ('Algunas veces', 2), ('Frecuentemente', 3), ('Casi siempre', 4)]
    opciones_inversas = [('Nunca', 4), ('Algunas veces', 3), ('Frecuentemente', 2), ('Casi siempre', 1)]

    for i, (texto, es_directo) in enumerate(items_idere_r, 1):
        pregunta = Pregunta(
            cuestionario_id=idere_r.id,
            orden=i,
            texto=texto,
            es_critica=False
        )
        db.session.add(pregunta)
        db.session.flush()

        opciones = opciones_directas if es_directo else opciones_inversas
        for texto_opcion, valor in opciones:
            db.session.add(OpcionRespuesta(
                pregunta_id=pregunta.id,
                texto=texto_opcion,
                valor=valor
            ))

    db.session.commit()
    print("  ✓ IDERE-R creado con 20 ítems")


# =============================================================================
# FUNCION: CREAR CUESTIONARIO IDARE-E (ANSIEDAD ESTADO)
# =============================================================================
def crear_cuestionario_idare_e():
    """
    Crea el cuestionario IDARE-E (Inventario de Ansiedad Estado-Rasgo, subescala Estado).

    Evalua como se siente el estudiante AHORA MISMO en terminos de ansiedad.
    20 items en escala 1-4 (Nada, Algo, Bastante, Mucho).

    Items directos (D): mayor respuesta = mas ansiedad.
    Items inversos (I): mayor respuesta = menos ansiedad (valor invertido en BD).

    Puntaje total: 20-80.
    Clasificacion:
    - 20-30: Bajo (sin indicador significativo)
    - 31-44: Moderado (ansiedad moderada)
    - 45-80: Alto (ansiedad elevada)
    """
    print("Creando cuestionario IDARE-E...")

    if Cuestionario.query.filter_by(codigo='IDARE-E').first():
        print("  - IDARE-E ya existe, omitiendo...")
        return

    idare_e = Cuestionario(
        codigo='IDARE-E',
        nombre='Inventario de Ansiedad Estado (IDARE-E)',
        descripcion='Subescala Estado del Inventario de Ansiedad Estado-Rasgo (IDARE). '
                    'Evalúa el nivel de ansiedad experimentado en el momento actual.',
        instrucciones='A continuación encontrará una serie de frases que la gente usa para '
                      'describirse a sí misma. Lea cada frase e indique cómo se siente '
                      'AHORA MISMO, en este momento. No hay respuestas buenas ni malas. '
                      'Responda con sinceridad.',
        puntaje_minimo=20,
        puntaje_maximo=80,
        activo=True
    )
    db.session.add(idare_e)
    db.session.flush()

    # -------------------------------------------------------------------------
    # Items del IDARE-E
    # Cada tupla: (texto, es_directo)
    # Directo (True): Nada=1, Algo=2, Bastante=3, Mucho=4
    # Inverso (False): Nada=4, Algo=3, Bastante=2, Mucho=1
    # -------------------------------------------------------------------------
    items_idare_e = [
        ('Me siento calmado/a',                                            False),  # I
        ('Me siento seguro/a',                                             False),  # I
        ('Estoy tenso/a',                                                  True),   # D
        ('Estoy contrariado/a',                                            True),   # D
        ('Me siento cómodo/a (a gusto)',                                   False),  # I
        ('Me siento alterado/a',                                           True),   # D
        ('Estoy preocupado/a ahora por posibles desgracias futuras',       True),   # D
        ('Me siento descansado/a',                                         False),  # I
        ('Me siento angustiado/a',                                         True),   # D
        ('Me siento confortable',                                          False),  # I
        ('Tengo confianza en mí mismo/a',                                  False),  # I
        ('Me siento nervioso/a',                                           True),   # D
        ('Estoy desasosegado/a (inquieto/a)',                              True),   # D
        ('Me siento muy agobiado/a (como oprimido/a)',                     True),   # D
        ('Estoy relajado/a',                                               False),  # I
        ('Me siento satisfecho/a',                                         False),  # I
        ('Estoy preocupado/a',                                             True),   # D
        ('Me siento muy nervioso/a y agitado/a',                           True),   # D
        ('Me siento alegre',                                               False),  # I
        ('Me siento bien',                                                 False),  # I
    ]

    opciones_directas = [('Nada', 1), ('Algo', 2), ('Bastante', 3), ('Mucho', 4)]
    opciones_inversas = [('Nada', 4), ('Algo', 3), ('Bastante', 2), ('Mucho', 1)]

    for i, (texto, es_directo) in enumerate(items_idare_e, 1):
        pregunta = Pregunta(
            cuestionario_id=idare_e.id,
            orden=i,
            texto=texto,
            es_critica=False
        )
        db.session.add(pregunta)
        db.session.flush()

        opciones = opciones_directas if es_directo else opciones_inversas
        for texto_opcion, valor in opciones:
            db.session.add(OpcionRespuesta(
                pregunta_id=pregunta.id,
                texto=texto_opcion,
                valor=valor
            ))

    db.session.commit()
    print("  ✓ IDARE-E creado con 20 ítems")


# =============================================================================
# FUNCION: CREAR CUESTIONARIO IDARE-R (ANSIEDAD RASGO)
# =============================================================================
def crear_cuestionario_idare_r():
    """
    Crea el cuestionario IDARE-R (Inventario de Ansiedad Estado-Rasgo, subescala Rasgo).

    Evalua como se siente el estudiante EN GENERAL (tendencia estable a la ansiedad).
    20 items en escala 1-4 (Casi nunca, Algunas veces, Frecuentemente, Casi siempre).

    Items directos (D): mayor respuesta = mas ansiedad rasgo.
    Items inversos (I): mayor respuesta = menos ansiedad rasgo (valor invertido en BD).

    Puntaje total: 20-80.
    Clasificacion igual que IDARE-E.
    """
    print("Creando cuestionario IDARE-R...")

    if Cuestionario.query.filter_by(codigo='IDARE-R').first():
        print("  - IDARE-R ya existe, omitiendo...")
        return

    idare_r = Cuestionario(
        codigo='IDARE-R',
        nombre='Inventario de Ansiedad Rasgo (IDARE-R)',
        descripcion='Subescala Rasgo del Inventario de Ansiedad Estado-Rasgo (IDARE). '
                    'Evalúa la tendencia estable a percibir situaciones como amenazantes '
                    'y a responder con ansiedad.',
        instrucciones='A continuación encontrará una serie de frases que la gente usa para '
                      'describirse a sí misma. Lea cada frase e indique cómo se siente '
                      'EN GENERAL, es decir, cómo suele sentirse habitualmente. '
                      'No hay respuestas buenas ni malas. Responda con sinceridad.',
        puntaje_minimo=20,
        puntaje_maximo=80,
        activo=True
    )
    db.session.add(idare_r)
    db.session.flush()

    # -------------------------------------------------------------------------
    # Items del IDARE-R
    # Cada tupla: (texto, es_directo)
    # -------------------------------------------------------------------------
    items_idare_r = [
        ('Me siento bien',                                                         False),  # I
        ('Me canso rápidamente',                                                   True),   # D
        ('Siento ganas de llorar',                                                 True),   # D
        ('Me gustaría ser tan feliz como otros parecen serlo',                     True),   # D
        ('Pierdo oportunidades por no poder decidirme rápidamente',               True),   # D
        ('Me siento descansado/a',                                                 False),  # I
        ('Soy una persona tranquila, serena y sosegada',                          False),  # I
        ('Veo que las dificultades se amontonan y no puedo con ellas',            True),   # D
        ('Me preocupo demasiado por cosas sin importancia',                       True),   # D
        ('Soy feliz',                                                              False),  # I
        ('Suelo tomar las cosas demasiado en serio',                              True),   # D
        ('Me falta confianza en mí mismo/a',                                      True),   # D
        ('Me siento seguro/a',                                                     False),  # I
        ('No suelo afrontar las crisis o dificultades',                           True),   # D
        ('Me siento triste (melancólico/a)',                                       True),   # D
        ('Me siento satisfecho/a',                                                 False),  # I
        ('Me rondan y molestan pensamientos sin importancia',                      True),   # D
        ('Me afectan tanto los desengaños que no me los puedo quitar de la cabeza', True),  # D
        ('Soy una persona estable',                                                False),  # I
        ('Al pensar en mis preocupaciones actuales me pongo tenso/a y agitado/a', True),   # D
    ]

    opciones_directas = [('Casi nunca', 1), ('Algunas veces', 2), ('Frecuentemente', 3), ('Casi siempre', 4)]
    opciones_inversas = [('Casi nunca', 4), ('Algunas veces', 3), ('Frecuentemente', 2), ('Casi siempre', 1)]

    for i, (texto, es_directo) in enumerate(items_idare_r, 1):
        pregunta = Pregunta(
            cuestionario_id=idare_r.id,
            orden=i,
            texto=texto,
            es_critica=False
        )
        db.session.add(pregunta)
        db.session.flush()

        opciones = opciones_directas if es_directo else opciones_inversas
        for texto_opcion, valor in opciones:
            db.session.add(OpcionRespuesta(
                pregunta_id=pregunta.id,
                texto=texto_opcion,
                valor=valor
            ))

    db.session.commit()
    print("  ✓ IDARE-R creado con 20 ítems")


# =============================================================================
# FUNCION: CREAR CUESTIONARIO ADNM-8
# =============================================================================
def crear_cuestionario_adnm8():
    """
    Crea el cuestionario ADNM-8 (Adjustment Disorder - New Module, version corta).

    Instrumento de tamizaje rapido para detectar trastorno adaptativo.
    8 items en escala 1-4 (Nunca, Raramente, A veces, A menudo).
    Todos los items son directos (mayor puntaje = mayor sintomatologia).

    Subescalas:
    - Preocupacion: items 1-4 (pensamientos intrusivos sobre el estresor)
    - Falta de adaptacion: items 5-8 (dificultad para funcionar con normalidad)

    Puntaje total: 8-32.
    Clasificacion:
    - 8-19:  Bajo  (sin indicador significativo)
    - 20-32: Alto  (indicador positivo, sugiere aplicar ADNM-20)
    """
    print("Creando cuestionario ADNM-8...")

    if Cuestionario.query.filter_by(codigo='ADNM-8').first():
        print("  - ADNM-8 ya existe, omitiendo...")
        return

    adnm8 = Cuestionario(
        codigo='ADNM-8',
        nombre='Módulo de Trastorno Adaptativo - Versión Corta (ADNM-8)',
        descripcion='Instrumento de tamizaje breve para detectar síntomas de trastorno '
                    'adaptativo. Evalúa preocupación y falta de adaptación ante un '
                    'acontecimiento estresante.',
        instrucciones='Las siguientes preguntas se refieren a cómo ha reaccionado ante '
                      'un acontecimiento estresante reciente (p. ej., problemas familiares, '
                      'académicos, de salud, económicos, etc.). Indique con qué frecuencia '
                      'ha experimentado cada situación en las ÚLTIMAS 2 SEMANAS.',
        puntaje_minimo=8,
        puntaje_maximo=32,
        activo=True
    )
    db.session.add(adnm8)
    db.session.flush()

    # -------------------------------------------------------------------------
    # Items del ADNM-8 (todos directos: mayor puntaje = mayor sintoma)
    # Subescala Preocupacion (4 items)
    # -------------------------------------------------------------------------
    items_adnm8 = [
        # -- Preocupacion --
        'Tengo pensamientos recurrentes sobre el acontecimiento estresante',
        'Me resulta difícil dejar de pensar en el acontecimiento',
        'Me preocupo por el acontecimiento',
        'Me doy cuenta de que pienso en el acontecimiento incluso cuando no quiero',
        # -- Falta de adaptacion --
        'Me resulta difícil concentrarme en otras cosas',
        'Me siento incapaz de realizar mis actividades habituales',
        'Me resulta difícil disfrutar de las cosas',
        'Me siento sin esperanza respecto al futuro',
    ]

    opciones = [('Nunca', 1), ('Raramente', 2), ('A veces', 3), ('A menudo', 4)]

    for i, texto in enumerate(items_adnm8, 1):
        pregunta = Pregunta(
            cuestionario_id=adnm8.id,
            orden=i,
            texto=texto,
            es_critica=False
        )
        db.session.add(pregunta)
        db.session.flush()

        for texto_opcion, valor in opciones:
            db.session.add(OpcionRespuesta(
                pregunta_id=pregunta.id,
                texto=texto_opcion,
                valor=valor
            ))

    db.session.commit()
    print("  ✓ ADNM-8 creado con 8 ítems")


# =============================================================================
# FUNCION: CREAR CUESTIONARIO ADNM-20
# =============================================================================
def crear_cuestionario_adnm20():
    """
    Crea el cuestionario ADNM-20 (Adjustment Disorder - New Module, version completa).

    Evaluacion completa de trastorno adaptativo segun criterios CIE-11.
    20 items en escala 1-4 (Nunca, Raramente, A veces, A menudo).
    Todos los items son directos.

    Subescalas:
    - Preocupacion   (items  1-7): Pensamientos intrusivos sobre el estresor
    - Falta de adaptacion (items 8-14): Dificultad para funcionar con normalidad
    - Evitacion      (items 15-20): Conductas de evitacion del estresor

    Puntaje total: 20-80.
    Clasificacion:
    - 20-46: Bajo  (sin indicador significativo)
    - 47-80: Alto  (probable trastorno adaptativo)
    """
    print("Creando cuestionario ADNM-20...")

    if Cuestionario.query.filter_by(codigo='ADNM-20').first():
        print("  - ADNM-20 ya existe, omitiendo...")
        return

    adnm20 = Cuestionario(
        codigo='ADNM-20',
        nombre='Módulo de Trastorno Adaptativo - Versión Completa (ADNM-20)',
        descripcion='Instrumento completo para evaluar trastorno adaptativo según criterios '
                    'CIE-11. Evalúa preocupación, falta de adaptación y evitación ante un '
                    'acontecimiento estresante.',
        instrucciones='Las siguientes preguntas se refieren a cómo ha reaccionado ante '
                      'un acontecimiento estresante reciente (p. ej., problemas familiares, '
                      'académicos, de salud, económicos, etc.). Indique con qué frecuencia '
                      'ha experimentado cada situación en las ÚLTIMAS 2 SEMANAS.',
        puntaje_minimo=20,
        puntaje_maximo=80,
        activo=True
    )
    db.session.add(adnm20)
    db.session.flush()

    # -------------------------------------------------------------------------
    # Items del ADNM-20 (todos directos)
    # -------------------------------------------------------------------------
    items_adnm20 = [
        # -- Preocupacion (items 1-7) --
        'Tengo pensamientos recurrentes sobre el acontecimiento estresante',
        'Imágenes del acontecimiento vienen a mi mente involuntariamente',
        'Me resulta difícil dejar de pensar en el acontecimiento',
        'Ciertos aspectos del acontecimiento siguen perturbándome',
        'Me preocupo por el acontecimiento',
        'Me siento impactado/a por el acontecimiento',
        'Me doy cuenta de que pienso en el acontecimiento incluso cuando no quiero',
        # -- Falta de adaptacion (items 8-14) --
        'Me resulta difícil concentrarme en otras cosas',
        'Me siento incapaz de realizar mis actividades habituales',
        'Me resulta difícil disfrutar de las cosas',
        'Me siento irritable',
        'Me siento triste',
        'Me siento ansioso/a',
        'Me siento sin esperanza respecto al futuro',
        # -- Evitacion (items 15-20) --
        'Evito pensar en el acontecimiento',
        'Intento no hablar del acontecimiento con nadie',
        'Evito lugares o situaciones que me recuerdan al acontecimiento',
        'Intento alejar de mi mente los pensamientos sobre el acontecimiento',
        'Me resulta difícil afrontar directamente el acontecimiento',
        'Evito personas relacionadas con el acontecimiento',
    ]

    opciones = [('Nunca', 1), ('Raramente', 2), ('A veces', 3), ('A menudo', 4)]

    for i, texto in enumerate(items_adnm20, 1):
        pregunta = Pregunta(
            cuestionario_id=adnm20.id,
            orden=i,
            texto=texto,
            es_critica=False
        )
        db.session.add(pregunta)
        db.session.flush()

        for texto_opcion, valor in opciones:
            db.session.add(OpcionRespuesta(
                pregunta_id=pregunta.id,
                texto=texto_opcion,
                valor=valor
            ))

    db.session.commit()
    print("  ✓ ADNM-20 creado con 20 ítems")


# =============================================================================
# FUNCION PRINCIPAL
# =============================================================================
def main():
    """
    Funcion principal que ejecuta la inicializacion de la base de datos.

    Realiza los siguientes pasos:
    1. Crea la aplicacion Flask
    2. Crea las tablas de la base de datos
    3. Crea los roles del sistema
    4. Crea los usuarios de prueba
    5. Crea los cuestionarios PHQ-2, PHQ-9 y ASSIST
    6. Crea evaluaciones de demostracion

    Al finalizar, muestra las credenciales de acceso para pruebas.
    """
    # Mostrar encabezado
    print("\n" + "="*60)
    print("  Mentis Cura - Inicialización de Base de Datos")
    print("="*60 + "\n")

    # Crear la aplicacion Flask con configuracion de desarrollo
    app = create_app('development')

    # Ejecutar dentro del contexto de la aplicacion
    # (necesario para acceder a la base de datos)
    with app.app_context():
        # Crear estructura de tablas
        print("Creando estructura de base de datos...")
        db.create_all()
        print("  ✓ Tablas creadas\n")

        # Poblar con datos iniciales
        crear_roles()
        crear_usuarios()
        crear_cuestionario_phq2()
        crear_cuestionario_phq9()
        crear_cuestionario_assist()
        crear_cuestionario_idere_e()
        crear_cuestionario_idere_r()
        crear_cuestionario_idare_e()
        crear_cuestionario_idare_r()
        crear_cuestionario_adnm8()
        crear_cuestionario_adnm20()
        crear_evaluaciones_demo()
        crear_evaluaciones_demo_assist()

        # Mostrar resumen final
        print("\n" + "="*60)
        print("  ✓ Base de datos inicializada correctamente")
        print("="*60)
        print("\n  Usuarios de acceso:")
        print("  ─────────────────────────────────────────────")
        print("  Usuario      │ Contraseña │ Rol")
        print("  ─────────────────────────────────────────────")
        print("  admin        │ admin123   │ Administrador")
        print("  psicologo    │ psico123   │ Orientador")
        print("  psicologia   │ psico123   │ Orientador")
        print("  A20001       │ disc123    │ Discente (Matrícula)")
        print("  B20002       │ disc123    │ Discente (Matrícula)")
        print("  C20003       │ disc123    │ Discente (Matrícula)")
        print("  D20004       │ disc123    │ Discente (Matrícula)")
        print("  E20005       │ disc123    │ Discente (Matrícula)")
        print("  ─────────────────────────────────────────────")
        print("\n  Los discentes inician sesión con su matrícula.\n")


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================
# Este bloque solo se ejecuta si se corre directamente: python seed_data.py
if __name__ == '__main__':
    main()
