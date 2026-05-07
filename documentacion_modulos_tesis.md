# Implementación de los módulos principales del sistema MENTIS CURA

## Introducción

El presente apartado documenta la implementación técnica de los módulos centrales del sistema de monitoreo psicológico MENTIS CURA, desarrollado como prototipo académico para el seguimiento del bienestar emocional de estudiantes en un contexto de educación militar. El sistema fue construido sobre una arquitectura de tres capas —presentación, lógica de negocio y datos— siguiendo el patrón arquitectónico Modelo-Vista-Controlador (MVC). La capa de presentación está compuesta por plantillas HTML generadas dinámicamente mediante el motor de plantillas Jinja2, estilizadas con el framework Bootstrap 5. La capa de controladores está implementada mediante Blueprints de Flask, el microframework web basado en Python que estructura las rutas HTTP del sistema. La capa de servicios concentra la lógica de negocio en clases especializadas independientes de las rutas, y la capa de datos se gestiona mediante SQLAlchemy, el mapeador objeto-relacional (ORM) que abstrae las operaciones sobre la base de datos PostgreSQL. La separación explícita entre estas capas no solo favoreció la organización del código durante el desarrollo, sino que también facilita la extensión y el mantenimiento del sistema en iteraciones futuras del prototipo.

---

## Módulo 1 — Autenticación e inicio de sesión

### Propósito y posición en el sistema

El módulo de autenticación constituye el punto de entrada obligatorio para todos los actores del sistema, independientemente de su rol. Ninguna ruta del sistema MENTIS CURA es accesible sin que el usuario haya iniciado sesión previamente; este principio de acceso controlado garantiza que la información de salud mental de los discentes permanezca protegida en todo momento. El módulo cumple dos funciones fundamentales: verificar la identidad del usuario que intenta acceder y, una vez confirmada dicha identidad, redirigirlo al panel correspondiente según su rol asignado en la base de datos.

### Organización del Blueprint de autenticación

En Flask, un Blueprint es un mecanismo de organización modular que agrupa un conjunto de rutas, plantillas y recursos relacionados bajo un mismo espacio de nombres. El módulo de autenticación se implementó en el archivo `app/routes/auth.py`, donde se declara el Blueprint `auth_bp` y se definen las cuatro rutas del módulo: `/login`, `/logout`, `/registro` y `/registro-exitoso`. A continuación se muestra la declaración del Blueprint y las rutas principales:

```python
# Crear el Blueprint de autenticación
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Si ya está autenticado, redirigir al inicio
    if current_user.is_authenticated:
        return redirect(url_for('main.inicio'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Por favor ingrese usuario y contraseña.', 'warning')
            return render_template('auth/login.html')

        usuario, error = AuthService.autenticar(username, password)

        if error:
            flash(error, 'danger')
            return render_template('auth/login.html')

        login_user(usuario, remember=True)
        flash(f'Bienvenido, {usuario.nombre}', 'success')

        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)

        if usuario.puede_ver_alertas():
            return redirect(url_for('alertas.listado'))
        return redirect(url_for('main.inicio'))

    return render_template('auth/login.html')
```

Este fragmento ilustra el flujo completo de la ruta de inicio de sesión. La ruta acepta tanto peticiones GET, para mostrar el formulario, como peticiones POST, para procesar las credenciales enviadas. Antes de cualquier validación, el sistema verifica si el usuario ya tiene una sesión activa, en cuyo caso lo redirige al inicio sin necesidad de volver a autenticarse.

### Flujo de autenticación y delegación al servicio

La lógica de verificación de credenciales fue separada de la ruta y encapsulada en `AuthService`, una clase de servicio ubicada en `app/services/auth_service.py`. Esta separación responde al principio de responsabilidad única: la ruta se ocupa únicamente del manejo HTTP (recibir datos del formulario, mostrar mensajes flash y redirigir), mientras que el servicio concentra la lógica de negocio. El método `autenticar` realiza tres verificaciones en secuencia: primero confirma que el nombre de usuario exista en la base de datos, luego verifica que la cuenta esté activa y finalmente compara la contraseña proporcionada con la almacenada. En caso de éxito, actualiza la fecha de último acceso del usuario antes de retornar el objeto de usuario:

```python
@staticmethod
def autenticar(username, password):
    usuario = Usuario.query.filter_by(username=username).first()

    if not usuario:
        return None, 'Usuario no encontrado'

    if not usuario.activo:
        return None, 'Cuenta desactivada. Contacte al administrador.'

    if not usuario.check_password(password):
        return None, 'Contraseña incorrecta'

    usuario.ultimo_acceso = datetime.utcnow()
    db.session.commit()

    return usuario, None
```

### Redirección diferenciada por rol

Una vez autenticado el usuario, el sistema evalúa su rol para decidir a qué sección redirigirlo. Los usuarios con rol de orientador o administrador son enviados directamente al listado de alertas, que representa el panel operativo de mayor relevancia para su función. Los discentes, en cambio, son redirigidos al panel de inicio donde se muestran los cuestionarios disponibles. Esta lógica se implementa mediante el método `puede_ver_alertas()` definido en el modelo `Usuario`, que retorna `True` únicamente para los roles `administrador` y `orientador`.

[FIGURA 1 — Captura de pantalla: pantalla de inicio de sesión]

[FIGURA 2 — Captura de pantalla: redirección al panel según rol]

### Control de acceso basado en roles (RBAC)

El sistema implementa un esquema de control de acceso basado en roles mediante decoradores personalizados definidos en `app/utils/decorators.py`. Los decoradores son funciones de orden superior que envuelven las funciones de ruta para añadir verificaciones de permisos antes de ejecutar la lógica de la vista. El sistema dispone de tres decoradores: `rol_requerido`, de propósito general; `solo_orientador`, para rutas accesibles únicamente por orientadores y administradores; y `solo_admin`, para rutas exclusivas del administrador del sistema.

```python
def solo_orientador(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Debe iniciar sesión para acceder.', 'warning')
            return redirect(url_for('auth.login'))

        if not current_user.puede_ver_alertas():
            flash('Acceso restringido a personal autorizado.', 'danger')
            return redirect(url_for('main.inicio'))

        return f(*args, **kwargs)
    return decorated_function
```

El uso de `functools.wraps` es relevante desde el punto de vista técnico, ya que preserva los metadatos de la función original (nombre, docstring, firma), lo cual es necesario para que Flask pueda registrar correctamente las rutas decoradas en su sistema interno de mapeo de URLs. La protección contra accesos no autorizados se resuelve mediante redirección al panel de inicio con un mensaje de error de tipo `danger`, en lugar de retornar un código HTTP 403, decisión que se tomó para ofrecer una experiencia de usuario más informativa en el contexto del prototipo.

### Gestión segura de contraseñas y sesiones

Las contraseñas de los usuarios se almacenan en el campo `password_hash` de la tabla `usuarios`. En la implementación actual del prototipo, el método `set_password` almacena la contraseña directamente en dicho campo y el método `check_password` realiza una comparación directa, decisión que simplifica el desarrollo inicial del prototipo y que deberá ser sustituida en versiones posteriores por el algoritmo de derivación de clave PBKDF2-SHA256 proporcionado por la biblioteca Werkzeug, el cual aplica una función de hash criptográfico con sal aleatoria para garantizar la seguridad de las contraseñas incluso ante un eventual compromiso de la base de datos.

La gestión de sesiones se configura en `app/config.py` mediante la directiva `PERMANENT_SESSION_LIFETIME = timedelta(hours=2)`, lo que establece una expiración de sesión de dos horas de inactividad. Adicionalmente, la cookie de sesión se configura con el atributo `HttpOnly = True`, lo que impide que scripts JavaScript del lado del cliente puedan leer su contenido, mitigando ataques de tipo Cross-Site Scripting (XSS). La protección contra ataques de falsificación de solicitudes entre sitios (CSRF) se implementa mediante la extensión Flask-WTF, que genera y valida un token único en cada formulario del sistema; el formulario de inicio de sesión incluye el campo oculto `csrf_token` con este propósito.

[CÓDIGO 1 — Fragmento ilustrativo: configuración de cookies de sesión en config.py]

---

## Módulo 2 — Registro del discente

### Propósito y diseño del autoregistro

El módulo de registro fue diseñado para que los discentes puedan crear su cuenta de forma autónoma, sin requerir intervención del administrador del sistema. Esta decisión de diseño responde a la naturaleza del contexto de uso: el sistema debe ser accesible para un número variable de estudiantes sin generar una carga operativa significativa en el personal administrativo. El autoregistro implica que el propio discente introduce sus datos académicos y personales, los cuales son validados por el servidor antes de crear la cuenta.

### Estructura del formulario y campos requeridos

El formulario de registro, accesible desde la ruta `/registro`, solicita los siguientes campos: nombre(s), apellido paterno, apellido materno (opcional), matrícula, edad, año académico que cursa, carrera y compañía a la que pertenece, contraseña y su confirmación. Los campos de carrera y compañía se presentan como listas desplegables cuyos valores válidos están definidos como constantes de clase en el modelo `Usuario`:

```python
CARRERAS = [
    ('tronco_comun', 'Tronco Común'),
    ('ing_computacion', 'Ingeniería en Computación e Informática'),
    ('ing_industrial', 'Ingeniería Industrial'),
    ('ing_comunicaciones', 'Ingeniería en Comunicaciones y Electrónica'),
    ('ing_construccion', 'Ingeniería en Construcción')
]

COMPANIAS = [
    ('primera', 'Primera Cía.'),
    ('segunda', 'Segunda Cía.'),
    ('tercera', 'Tercera Cía.'),
    ('cuarta', 'Cuarta Cía.'),
    ('oficiales', 'Cía. Oficiales')
]
```

Esta estructura permite que el formulario se construya dinámicamente en la plantilla a partir de las constantes del modelo, garantizando que los valores enviados por el usuario coincidan exactamente con los valores definidos en el servidor.

### Validación mediante expresión regular

La matrícula es el campo más crítico del formulario, ya que opera simultáneamente como identificador único del discente en la base de datos y como nombre de usuario para iniciar sesión. El sistema valida que la matrícula cumpla el formato institucional mediante la expresión regular `r'^[A-Z]\d+$'`, que exige que el valor comience con exactamente una letra mayúscula seguida de uno o más dígitos numéricos. La validación se realiza en el servidor mediante el módulo `re` de Python:

```python
elif not re.match(r'^[A-Z]\d+$', matricula):
    errores.append('La matrícula debe ser una letra seguida de números (ej: A12345).')
```

Adicionalmente, el sistema convierte automáticamente la matrícula introducida a mayúsculas antes de validarla (`matricula = request.form.get('matricula', '').strip().upper()`), evitando rechazos por diferencia de capitalización. La validación de unicidad se realiza mediante una consulta a la base de datos que verifica que no exista ya un usuario con la misma matrícula, previniendo duplicidades antes de intentar insertar el registro.

### Proceso de creación de la cuenta

Una vez superadas todas las validaciones, el controlador construye un objeto `Usuario` con los datos del formulario, asigna el rol de discente consultándolo desde la base de datos y establece la contraseña. La matrícula se utiliza directamente como valor del campo `username`, de modo que el discente utiliza su matrícula para iniciar sesión:

```python
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
    rol_id=rol_discente.id,
    activo=True
)
usuario.set_password(password)
db.session.add(usuario)
db.session.commit()
```

La operación de escritura está envuelta en un bloque `try/except` que, ante cualquier excepción inesperada, ejecuta un `db.session.rollback()` para deshacer cualquier cambio parcial y evitar dejar la base de datos en un estado inconsistente. En caso de error, el usuario recibe un mensaje de advertencia y se le presenta nuevamente el formulario.

[FIGURA 3 — Captura de pantalla: formulario de registro]

[FIGURA 4 — Captura de pantalla: mensaje de validación de matrícula]

### Modelo de datos del Usuario

El modelo `Usuario` hereda de `UserMixin`, la clase base proporcionada por Flask-Login que implementa los métodos requeridos por el sistema de sesiones (`is_authenticated`, `is_active`, `get_id`), y de `db.Model`, la clase base de SQLAlchemy. La estructura del modelo refleja la naturaleza dual de los usuarios del sistema —personal institucional y discentes— mediante columnas opcionales que solo aplican a los discentes (matrícula, edad, año académico, carrera y compañía). La relación con el modelo `Rol` se establece mediante una clave foránea `rol_id` y una relación SQLAlchemy que permite acceder al objeto `Rol` directamente desde cualquier instancia de `Usuario` mediante el atributo `usuario.rol`.

[CÓDIGO 2 — Fragmento ilustrativo: definición completa del modelo Usuario con sus atributos y relaciones]

---

## Módulo 3 — Aplicación de cuestionarios psicométricos

### Propósito del módulo y presentación al discente

El módulo de cuestionarios gestiona la presentación, validación y envío de los instrumentos psicométricos disponibles en el sistema. Al acceder a la ruta `/cuestionarios/`, el discente visualiza el listado de todos los cuestionarios activos almacenados en la base de datos. Esta consulta es dinámica: el sistema recupera únicamente los cuestionarios cuyo campo `activo` tiene valor verdadero, lo que permite activar o desactivar instrumentos sin modificar el código. El Blueprint `cuestionarios_bp`, definido en `app/routes/cuestionarios.py`, gestiona tres rutas: el listado, la visualización del formulario para responder y el procesamiento de las respuestas enviadas.

[FIGURA 5 — Captura de pantalla: listado de cuestionarios disponibles]

### Presentación del cuestionario y sus ítems

Al seleccionar un cuestionario, el sistema recupera el objeto `Cuestionario` de la base de datos filtrando por su código (por ejemplo, `PHQ-9`) y verifica que esté activo. A continuación, obtiene las preguntas asociadas ordenadas por su número de orden y las pasa al motor de plantillas para renderizar el formulario completo. Todos los ítems de un cuestionario se presentan simultáneamente en la misma página, no de forma individual, lo que permite al discente revisar y modificar sus respuestas antes de enviarlas. Cada ítem se muestra con sus opciones de respuesta en formato de botones de radio, identificados en el formulario con el nombre `pregunta_{id}`.

Para el cuestionario ASSIST, que tiene una estructura condicional y un número variable de ítems activos según las sustancias reportadas, se utiliza una plantilla específica (`responder_assist.html`) con lógica de presentación adaptada a su flujo particular.

[FIGURA 6 — Captura de pantalla: pantalla de respuesta de un cuestionario]

### Lógica adaptativa del PHQ-2

El PHQ-2 actúa como instrumento de tamizaje de primer nivel. Al obtenerse un puntaje igual o superior a 3 en este cuestionario, el resultado clínico indica la posible presencia de síntomas depresivos y recomienda la aplicación del PHQ-9 para una evaluación más detallada. Esta lógica adaptativa se implementa en la plantilla de resultados, donde el sistema evalúa el puntaje total y el código del cuestionario para mostrar el mensaje de recomendación correspondiente:

```python
# En la plantilla resultado.html (Jinja2)
{% if evaluacion.cuestionario.codigo == 'PHQ-2' %}
    {% if evaluacion.puntaje_total >= 3 %}
    <p class="mb-0">
        Un puntaje de 3 o más en el PHQ-2 sugiere la posible presencia de
        síntomas depresivos. Se recomienda completar el cuestionario PHQ-9
        para una evaluación más detallada.
    </p>
    {% endif %}
{% endif %}
```

Este umbral también está configurado como constante en `app/config.py` mediante `PHQ2_UMBRAL_RIESGO = 3`, siguiendo el criterio clínico establecido por los autores del instrumento. La recomendación de continuar con el PHQ-9 se presenta directamente al discente en la pantalla de resultados, quien puede navegar al listado de cuestionarios y aplicarlo voluntariamente.

### Validación de respuestas

El controlador valida que todas las preguntas hayan sido respondidas antes de procesar la evaluación. Si el usuario intenta enviar el formulario con algún ítem sin responder, el sistema detecta la ausencia del campo correspondiente en los datos POST y redirige al discente al formulario con un mensaje de advertencia. Esta validación ocurre tanto en la ruta de envío como en el `EvaluacionService` mediante el método `validar_respuestas`, que verifica que los identificadores de las preguntas respondidas coincidan exactamente con el conjunto de preguntas del cuestionario y que los valores enviados correspondan a opciones válidas definidas en la base de datos.

### El EvaluacionService: cálculo y clasificación

Una vez validadas las respuestas, el controlador delega el procesamiento completo al `EvaluacionService`, encapsulado en `app/services/evaluacion_service.py`. Este servicio implementa el método principal `procesar_evaluacion`, que ejecuta los siguientes pasos: calcula el puntaje total sumando los valores de todas las respuestas, detecta si alguna pregunta crítica fue respondida con un valor positivo, clasifica el nivel de riesgo según los rangos predefinidos para el instrumento aplicado, persiste la evaluación y las respuestas individuales en la base de datos y, finalmente, delega la generación de alertas al `AlertaService`.

```python
@classmethod
def procesar_evaluacion(cls, usuario_id, cuestionario_id, respuestas_dict):
    cuestionario = Cuestionario.query.get(cuestionario_id)
    if not cuestionario:
        raise ValueError('Cuestionario no encontrado')

    if cuestionario.codigo == 'ASSIST':
        return cls._procesar_assist(usuario_id, cuestionario, respuestas_dict)

    puntaje_total = sum(respuestas_dict.values())

    alerta_critica = False
    puntaje_critica = 0
    for pregunta_id, valor in respuestas_dict.items():
        pregunta = Pregunta.query.get(pregunta_id)
        if pregunta and pregunta.es_critica and valor >= 1:
            alerta_critica = True
            puntaje_critica = valor

    nivel_riesgo = cls._clasificar_riesgo(cuestionario.codigo, puntaje_total)

    evaluacion = Evaluacion(
        usuario_id=usuario_id,
        cuestionario_id=cuestionario_id,
        puntaje_total=puntaje_total,
        nivel_riesgo=nivel_riesgo,
        alerta_pregunta_critica=alerta_critica,
        puntaje_pregunta_critica=puntaje_critica,
        fecha_evaluacion=datetime.utcnow()
    )
    db.session.add(evaluacion)
    db.session.flush()

    for pregunta_id, valor in respuestas_dict.items():
        respuesta = Respuesta(
            evaluacion_id=evaluacion.id,
            pregunta_id=pregunta_id,
            valor=valor
        )
        db.session.add(respuesta)

    db.session.commit()
    AlertaService.evaluar_y_generar_alertas(evaluacion)

    return evaluacion
```

La clasificación de riesgo se realiza en el método `_clasificar_riesgo`, que aplica los rangos correspondientes a cada instrumento. Para el PHQ-9, los rangos están definidos como una constante de clase:

```python
CLASIFICACION_PHQ9 = {
    'minimo':          (0, 4),
    'leve':            (5, 9),
    'moderado':        (10, 14),
    'moderado_severo': (15, 19),
    'severo':          (20, 27)
}
```

Para los instrumentos IDERE e IDARE, la clasificación opera sobre un rango de puntaje de 20 a 80 (20 ítems en escala 1-4), mientras que los cuestionarios ADNM-8 y ADNM-20 aplican un esquema binario de clasificación (por debajo o por encima del punto de corte clínico establecido).

[FIGURA 7 — Captura de pantalla: resultado de la evaluación]

### Modelos de datos involucrados

Los datos de los instrumentos se organizan en tres modelos relacionados. El modelo `Cuestionario` almacena los metadatos del instrumento: código, nombre, descripción, instrucciones y puntaje máximo. El modelo `Pregunta` representa cada ítem del cuestionario, con campos adicionales para el cuestionario ASSIST: `sustancia` y `grupo_pregunta`, que permiten organizar los ítems según la sustancia evaluada y el grupo de preguntas al que pertenecen. El modelo `OpcionRespuesta` almacena las opciones de respuesta de cada ítem, incluyendo su texto y valor numérico. Esta estructura de tres niveles permite que el sistema soporte instrumentos con diferentes escalas de respuesta sin modificar el código de procesamiento.

[CÓDIGO 3 — Fragmento ilustrativo: definición de los modelos Cuestionario, Pregunta y OpcionRespuesta]

---

## Módulo 4 — Almacenamiento de resultados

### Propósito de la persistencia centralizada

El módulo de almacenamiento de resultados constituye la base del monitoreo longitudinal del sistema. La persistencia de todas las evaluaciones en una base de datos relacional permite registrar la evolución del estado de bienestar de cada discente a lo largo del tiempo, comparar resultados entre diferentes momentos y generar reportes agregados para el personal de orientación. Sin este módulo, el sistema se reduciría a una herramienta de evaluación puntual sin capacidad de seguimiento.

### Modelos de datos: Evaluación y Respuesta

El modelo `Evaluacion` registra los datos agregados de cada aplicación de cuestionario. Sus atributos principales son: `usuario_id`, que referencia al discente evaluado; `cuestionario_id`, que identifica el instrumento aplicado; `puntaje_total`, la suma de los valores de todas las respuestas; `nivel_riesgo`, la clasificación resultante según los rangos del instrumento; `alerta_pregunta_critica`, un indicador booleano que señala si alguna pregunta crítica fue respondida con un valor positivo; `puntaje_pregunta_critica`, el valor específico de dicha respuesta; y `fecha_evaluacion`, el sello de tiempo de la evaluación.

```python
class Evaluacion(db.Model):
    __tablename__ = 'evaluaciones'

    id                     = db.Column(db.Integer, primary_key=True)
    usuario_id             = db.Column(db.Integer, db.ForeignKey('usuarios.id'),
                                       nullable=False, index=True)
    cuestionario_id        = db.Column(db.Integer, db.ForeignKey('cuestionarios.id'),
                                       nullable=False)
    puntaje_total          = db.Column(db.Integer, nullable=False)
    nivel_riesgo           = db.Column(db.String(30), nullable=False)
    alerta_pregunta_critica = db.Column(db.Boolean, default=False)
    puntaje_pregunta_critica = db.Column(db.Integer, default=0)
    observaciones          = db.Column(db.Text)
    fecha_evaluacion       = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    created_at             = db.Column(db.DateTime, default=datetime.utcnow)

    respuestas         = db.relationship('Respuesta', backref='evaluacion',
                                         lazy='dynamic', cascade='all, delete-orphan')
    alertas            = db.relationship('Alerta', backref='evaluacion', lazy='dynamic')
    puntajes_sustancia = db.relationship('PuntajeSustancia', backref='evaluacion',
                                          lazy='dynamic', cascade='all, delete-orphan')
```

El modelo `Respuesta` almacena el valor individual de cada ítem respondido, vinculado a la evaluación y a la pregunta correspondiente. La relación entre `Evaluacion` y `Respuesta` es de uno a muchos, y se configura con `cascade='all, delete-orphan'`, lo que garantiza que si una evaluación es eliminada, todas sus respuestas asociadas se eliminan en cascada, manteniendo la integridad referencial de la base de datos.

### El patrón ORM y la prevención de inyección SQL

SQLAlchemy implementa el patrón de mapeo objeto-relacional, que abstrae las operaciones de base de datos detrás de métodos Python sobre objetos. Esto significa que ninguna consulta o escritura en el sistema MENTIS CURA involucra la construcción manual de cadenas SQL, lo que elimina structuralmente la posibilidad de ataques de inyección SQL. Las consultas parametrizadas son generadas automáticamente por SQLAlchemy, y los valores de los parámetros nunca se concatenan directamente en el texto de la consulta. La recuperación del historial de evaluaciones de un usuario ilustra este principio:

```python
@classmethod
def obtener_historial_usuario(cls, usuario_id, limite=10):
    return Evaluacion.query.filter_by(usuario_id=usuario_id)\
        .order_by(Evaluacion.fecha_evaluacion.desc())\
        .limit(limite)\
        .all()
```

Esta consulta, generada internamente por SQLAlchemy como una sentencia SQL parametrizada con el valor de `usuario_id` como parámetro vinculado, garantiza que el valor del identificador nunca sea interpretado como código SQL.

### Integridad transaccional

El sistema garantiza la atomicidad de las operaciones de escritura mediante el uso del patrón de transacción de SQLAlchemy. El método `procesar_evaluacion` utiliza `db.session.flush()` para obtener el identificador de la nueva evaluación sin confirmar aún la transacción, lo que permite crear los objetos `Respuesta` vinculados con el `evaluacion_id` correcto. La confirmación final de todos los cambios se realiza con una única llamada a `db.session.commit()` al final del proceso, asegurando que el registro de la evaluación y el de todas sus respuestas individuales se persistan de forma atómica: o se persisten todos juntos o no se persiste ninguno.

[FIGURA 8 — Captura de pantalla: historial de evaluaciones del discente]

[FIGURA 9 — Captura de pantalla: historial de un discente visto por el orientador]

### La entidad PuntajeSustancia para el ASSIST

El cuestionario ASSIST evalúa nueve sustancias de forma independiente, calculando un puntaje SSIS (Specific Substance Involvement Score) para cada una. Este nivel de detalle no puede representarse en el campo `puntaje_total` del modelo `Evaluacion`, que solo almacena un único valor numérico. Para resolver esta limitación, se diseñó el modelo `PuntajeSustancia`, que almacena el puntaje y el nivel de riesgo para cada sustancia reportada como consumida en una evaluación ASSIST particular. Este diseño permite que la pantalla de resultados del ASSIST muestre una tabla desglosada por sustancia, con su puntaje individual y clasificación de riesgo correspondiente, lo que proporciona información clínicamente más precisa al orientador.

[CÓDIGO 4 — Fragmento ilustrativo: método _procesar_assist del EvaluacionService con creación de PuntajeSustancia]

---

## Módulo 5 — Generación y gestión de alertas

### Propósito del sistema de alertas

El sistema de alertas es el componente de mayor impacto institucional del sistema MENTIS CURA. Su función es notificar automáticamente al personal de orientación cuando una evaluación revela indicadores que requieren atención profesional, eliminando la dependencia de una revisión manual periódica de todos los resultados. La generación automática de alertas garantiza que ningún caso de riesgo quede sin ser identificado, independientemente del volumen de evaluaciones procesadas.

### El AlertaService y las dos condiciones de activación

La lógica de generación de alertas está encapsulada en `AlertaService`, definido en `app/services/alerta_service.py`. El método principal `evaluar_y_generar_alertas` recibe el objeto `Evaluacion` recién creado y evalúa dos condiciones de forma independiente. La primera condición verifica si la evaluación contiene una respuesta positiva en alguna pregunta marcada como crítica (como la pregunta 9 del PHQ-9, que evalúa ideación suicida), en cuyo caso genera una alerta de prioridad `crítica` que requiere atención inmediata. La segunda condición verifica si el nivel de riesgo de la evaluación es igual o superior a `leve`, en cuyo caso genera una alerta de prioridad correspondiente al nivel de riesgo. Ambas condiciones son mutuamente excluyentes en la práctica: si se activa la primera, no se genera la alerta por nivel de riesgo, evitando duplicidades:

```python
@classmethod
def evaluar_y_generar_alertas(cls, evaluacion):
    alertas_generadas = []

    if evaluacion.cuestionario.codigo == 'ASSIST':
        return cls._evaluar_alertas_assist(evaluacion)

    # CONDICIÓN 1: Pregunta crítica (ideación suicida)
    if evaluacion.alerta_pregunta_critica:
        alerta = cls._crear_alerta(
            evaluacion=evaluacion,
            tipo='pregunta_critica',
            prioridad='critica',
            mensaje=cls._generar_mensaje_critico(evaluacion)
        )
        alertas_generadas.append(alerta)

    # CONDICIÓN 2: Nivel de riesgo igual o superior a leve
    prioridad = cls.PRIORIDAD_POR_RIESGO.get(evaluacion.nivel_riesgo)
    if prioridad and not evaluacion.alerta_pregunta_critica:
        alerta = cls._crear_alerta(
            evaluacion=evaluacion,
            tipo='puntaje_riesgo',
            prioridad=prioridad,
            mensaje=cls._generar_mensaje_riesgo(evaluacion)
        )
        alertas_generadas.append(alerta)

    return alertas_generadas
```

### Los cuatro niveles de prioridad

El sistema establece cuatro niveles de prioridad para las alertas, definidos como valores del campo `prioridad` en el modelo `Alerta`. La prioridad `baja` corresponde a evaluaciones con nivel de riesgo `leve` y representa casos que requieren seguimiento rutinario. La prioridad `media` se asigna a niveles de riesgo `moderado` e indica que se requiere atención pronta. La prioridad `alta` se asigna a niveles `moderado_severo`, `severo` y `alto` (para ASSIST), e indica atención prioritaria. La prioridad `crítica` se reserva exclusivamente para respuestas positivas en la pregunta 9 del PHQ-9 y para uso de sustancias por vía inyectada reportado en el ASSIST, e indica la necesidad de atención inmediata. La asignación de prioridad por nivel de riesgo está centralizada en el diccionario `PRIORIDAD_POR_RIESGO`:

```python
PRIORIDAD_POR_RIESGO = {
    'minimo':           None,
    'bajo':             None,
    'leve':             'baja',
    'riesgo':           'media',
    'moderado':         'media',
    'perjudicial':      'alta',
    'moderado_severo':  'alta',
    'alto':             'alta',
    'posible_dependencia': 'alta',
    'severo':           'alta'
}
```

### El modelo de datos Alerta

El modelo `Alerta` registra toda la información relevante de cada evento de alerta generado por el sistema. Además de los campos de clasificación (`tipo`, `prioridad`, `mensaje`), el modelo implementa los campos necesarios para rastrear el ciclo de vida completo de la alerta: `estado`, que registra la fase actual; `atendida_por_id`, que referencia al orientador que intervino; `fecha_atencion`, el sello de tiempo de la intervención; y `notas_atencion`, el campo de texto libre donde el orientador documenta las acciones tomadas. El campo `updated_at` se actualiza automáticamente con cada modificación del registro, proveyendo una bitácora de auditoría básica de los cambios de estado.

### Ciclo de vida de una alerta y gestión por el orientador

Las alertas transitan a través de tres estados en su ciclo de vida. El estado inicial `pendiente` indica que la alerta ha sido generada pero aún no ha sido atendida. El estado `en_revision` señala que un orientador ha tomado conocimiento de la alerta y está trabajando activamente en el caso. El estado `atendida` indica que el caso fue cerrado y documentado. Esta progresión se implementa en el modelo mediante los métodos `marcar_en_revision` y `marcar_atendida`:

```python
def marcar_en_revision(self, usuario_id):
    self.estado = 'en_revision'
    self.atendida_por_id = usuario_id
    self.updated_at = datetime.utcnow()

def marcar_atendida(self, usuario_id, notas=''):
    self.estado = 'atendida'
    self.atendida_por_id = usuario_id
    self.fecha_atencion = datetime.utcnow()
    self.notas_atencion = notas
    self.updated_at = datetime.utcnow()
```

El panel de alertas del orientador, accesible desde `/alertas/`, presenta el listado de alertas ordenado por prioridad de mayor a menor urgencia, utilizando una expresión `CASE` de SQLAlchemy para definir el orden personalizado. El orientador puede filtrar el listado por estado y prioridad mediante parámetros de URL, y puede acceder al detalle de cada alerta para consultar la información del discente, el resultado de la evaluación que la originó y el historial de atenciones anteriores. Las acciones de cambio de estado se ejecutan mediante solicitudes POST a las rutas `/alertas/<id>/en-revision` y `/alertas/<id>/atender`, protegidas con el decorador `@solo_orientador` para garantizar que únicamente el personal autorizado pueda modificar el estado de las alertas.

[FIGURA 10 — Captura de pantalla: panel de alertas del orientador]

[FIGURA 11 — Captura de pantalla: detalle de una alerta con opciones de gestión]

[FIGURA 12 — Captura de pantalla: registro de notas de seguimiento]

---

## Consideraciones generales de implementación

La implementación del sistema MENTIS CURA estuvo guiada por un conjunto de decisiones técnicas que favorecen la organización, la seguridad y la extensibilidad del código. La adopción del patrón de Application Factory de Flask, que centraliza la inicialización de la aplicación en la función `create_app`, permitió separar la configuración del sistema de su instanciación, facilitando la creación de instancias con diferentes configuraciones para entornos de desarrollo, pruebas y producción. La organización de las rutas en Blueprints temáticos —`auth_bp`, `cuestionarios_bp`, `evaluaciones_bp`, `alertas_bp`, `admin_bp`, `reportes_bp` y `materiales_bp`— siguió el principio de separación de responsabilidades y evitó la concentración de toda la lógica de ruteo en un único archivo, un problema frecuente en aplicaciones Flask de mediana complejidad.

La introducción de una capa de servicios —`AuthService`, `EvaluacionService` y `AlertaService`— como intermediarios entre los controladores y los modelos de datos fue una decisión arquitectónica de especial relevancia. Esta capa garantiza que la lógica de negocio no quede acoplada a la capa de presentación ni sea duplicada entre diferentes rutas que comparten la misma operación. En particular, el hecho de que tanto la ruta de envío de cuestionarios como el script de inicialización de datos de prueba utilicen el mismo `EvaluacionService` para procesar evaluaciones asegura que la lógica de clasificación de riesgo y generación de alertas sea consistente en todos los contextos de uso.

El uso de SQLAlchemy como capa de abstracción sobre la base de datos PostgreSQL no solo simplificó las operaciones de lectura y escritura mediante el modelo ORM, sino que también aportó protección estructural contra ataques de inyección SQL al gestionar automáticamente la parametrización de consultas. La gestión de transacciones mediante `db.session` garantizó la atomicidad de las operaciones críticas, como el registro conjunto de una evaluación y todas sus respuestas individuales. El sistema de migraciones implícito de SQLAlchemy, mediante `db.create_all()`, facilitó la inicialización de la base de datos durante el desarrollo del prototipo, aunque en un entorno de producción deberá ser sustituido por una herramienta de migraciones explícitas como Alembic para gestionar los cambios de esquema de forma controlada.

En conjunto, estas decisiones técnicas posicionan a MENTIS CURA como un prototipo que no solo cumple con los requisitos funcionales identificados durante el análisis, sino que también establece una base arquitectónica sólida sobre la cual podrán desarrollarse las funcionalidades previstas para versiones futuras del sistema, incluyendo la implementación de notificaciones en tiempo real, la integración con sistemas institucionales de registro académico y el fortalecimiento de los mecanismos de cifrado de datos sensibles.
