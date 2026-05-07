# Documento Técnico para Tesis

## Mentis Cura - Sistema de Monitoreo Psicológico en el Sistema Educativo Militar

---

## 1. Decisiones de Arquitectura

### 1.1 Patrón Arquitectónico: Arquitectura por Capas

Se implementó una **arquitectura de tres capas** que separa responsabilidades y facilita el mantenimiento:

```
┌─────────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                      │
│  (Templates Jinja2 + Bootstrap + Routes/Blueprints Flask)   │
├─────────────────────────────────────────────────────────────┤
│                    CAPA DE SERVICIOS                         │
│  (AuthService, EvaluacionService, AlertaService, etc.)      │
├─────────────────────────────────────────────────────────────┤
│                    CAPA DE DATOS                             │
│  (Modelos SQLAlchemy: Usuario, Evaluacion, Alerta, etc.)    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Base de Datos  │
                    │  (PostgreSQL)   │
                    └─────────────────┘
```

**Justificación:**
- **Separación de responsabilidades**: Cada capa tiene una función específica, lo que reduce el acoplamiento.
- **Facilidad de pruebas**: Los servicios pueden probarse independientemente de la interfaz.
- **Escalabilidad**: Permite migrar componentes sin afectar otras capas.
- **Mantenibilidad**: Los cambios en la lógica de negocio se aíslan en la capa de servicios.

### 1.2 Patrón MVC Adaptado

Flask implementa un patrón Model-View-Controller adaptado:
- **Model**: Clases SQLAlchemy en `/app/models/`
- **View**: Templates Jinja2 en `/app/templates/`
- **Controller**: Blueprints en `/app/routes/`

### 1.3 Organización Modular con Blueprints

Los controladores se organizan en **Blueprints** de Flask:

| Blueprint      | Prefijo URL      | Responsabilidad                              |
|----------------|------------------|----------------------------------------------|
| auth           | /                | Autenticación (login/logout/registro)        |
| main           | /                | Dashboard principal                          |
| cuestionarios  | /cuestionarios   | Aplicación de PHQ-2, PHQ-9 y ASSIST          |
| evaluaciones   | /evaluaciones    | Visualización de resultados                  |
| alertas        | /alertas         | Gestión de alertas (orientadores)            |
| admin          | /admin           | Administración del sistema                   |
| reportes       | /reportes        | Generación de reportes PDF                   |
| materiales     | /materiales      | Gestión de materiales de apoyo               |

---

## 2. Justificación Tecnológica

### 2.1 Backend: Python + Flask

**¿Por qué Python?**
- Sintaxis clara y legible, ideal para proyectos académicos
- Amplia documentación y comunidad activa
- Bibliotecas maduras para seguridad y ORM
- Curva de aprendizaje accesible

**¿Por qué Flask sobre Django?**
- **Microframework**: Permite control granular sobre componentes
- **Flexibilidad**: No impone estructura rígida, adaptable a necesidades específicas
- **Ligereza**: Menor overhead para prototipos
- **Transparencia**: El funcionamiento interno es más visible para fines académicos

### 2.2 Base de Datos: PostgreSQL

**¿Por qué PostgreSQL?**
- Sistema de gestión de base de datos robusto y confiable
- Soporte completo para transacciones ACID
- Escalable para entornos de producción
- Herramientas gráficas disponibles (pgAdmin4)
- Compatible con SQLAlchemy ORM

**Configuración de conexión:**
```python
SQLALCHEMY_DATABASE_URI = 'postgresql://psico_user:psico123@localhost:5432/psico_monitor'
```

### 2.3 ORM: SQLAlchemy

**Ventajas:**
- Mapeo objeto-relacional transparente
- Prevención de SQL injection por diseño
- Consultas expresivas en Python
- Soporte para múltiples motores de BD
- Migraciones de esquema facilitadas

### 2.4 Frontend: Jinja2 + Bootstrap

**Plantillas Jinja2:**
- Integración nativa con Flask
- Herencia de plantillas (DRY)
- Escape automático de HTML (seguridad XSS)
- Sintaxis intuitiva

**Bootstrap 5:**
- Framework CSS responsive
- Componentes prediseñados
- Consistencia visual
- Documentación extensa

---

## 3. Modelo de Datos

### 3.1 Diagrama Entidad-Relación

```
┌─────────────┐       ┌───────────────────────────┐       ┌──────────────┐
│    Rol      │       │         Usuario           │       │ Cuestionario │
├─────────────┤       ├───────────────────────────┤       ├──────────────┤
│ id (PK)     │──────<│ id (PK)                   │       │ id (PK)      │
│ nombre      │       │ username                  │       │ codigo       │
│ descripcion │       │ email                     │       │ nombre       │
└─────────────┘       │ password_hash             │       │ descripcion  │
                      │ nombre                    │       │ puntaje_max  │
                      │ apellido_paterno          │       └──────┬───────┘
                      │ apellido_materno          │              │
                      │ matricula (único)         │              │
                      │ edad                      │       ┌──────▼───────┐
                      │ anio_cursa (1-6)          │       │   Pregunta   │
                      │ carrera                   │       ├──────────────┤
                      │ compania                  │       │ id (PK)      │
                      │ rol_id (FK)               │       │ cuest_id(FK) │
                      │ activo                    │       │ orden        │
                      └───────────┬───────────────┘       │ texto        │
                                  │                       │ es_critica   │
                                  │                       └──────┬───────┘
                                  │                              │
                      ┌───────────▼───────────┐           ┌──────▼───────┐
                      │     Evaluacion        │           │   Opcion     │
                      ├───────────────────────┤           │  Respuesta   │
                      │ id (PK)               │           ├──────────────┤
                      │ usuario_id (FK)       │           │ id (PK)      │
                      │ cuestionario_id (FK)  │           │ pregunta_id  │
                      │ puntaje_total         │           │ texto        │
                      │ nivel_riesgo          │           │ valor (0-3)  │
                      │ alerta_pregunta_crit. │           └──────────────┘
                      │ puntaje_preg_critica  │
                      │ fecha_evaluacion      │
                      └───────────┬───────────┘
                                  │
              ┌───────────────────┴───────────────┐
              │                                   │
      ┌───────▼───────┐                   ┌───────▼───────┐
      │   Respuesta   │                   │    Alerta     │
      ├───────────────┤                   ├───────────────┤
      │ id (PK)       │                   │ id (PK)       │
      │ eval_id (FK)  │                   │ usuario_id    │
      │ pregunta_id   │                   │ eval_id (FK)  │
      │ valor         │                   │ tipo          │
      └───────────────┘                   │ prioridad     │
                                          │ mensaje       │
                                          │ estado        │
                                          │ atendida_por  │
                                          │ notas_atencion│
                                          └───────────────┘

```

### 3.2 Descripción de Entidades

| Entidad         | Propósito                                              |
|-----------------|--------------------------------------------------------|
| Rol             | Define permisos: administrador, orientador, discente   |
| Usuario         | Credenciales, datos personales y académicos            |
| Cuestionario      | Definición de PHQ-2, PHQ-9 y ASSIST                      |
| Pregunta          | Ítems individuales de cada cuestionario                  |
| OpcionRespuesta   | Opciones de respuesta para cada pregunta                 |
| Evaluacion        | Registro de aplicación con puntaje y clasificación       |
| Respuesta         | Valor seleccionado por pregunta                          |
| PuntajeSustancia  | SSIS calculado por sustancia (solo ASSIST)               |
| Alerta            | Notificación generada por reglas de riesgo               |
| Material          | Documentos de apoyo gestionados por orientadores         |

### 3.3 Campos del Usuario (Discente)

| Campo            | Tipo        | Descripción                                    |
|------------------|-------------|------------------------------------------------|
| matricula        | String(50)  | Identificador único (ej: A12345)               |
| nombre           | String(100) | Nombre(s) del discente                         |
| apellido_paterno | String(100) | Apellido paterno                               |
| apellido_materno | String(100) | Apellido materno (opcional)                    |
| edad             | Integer     | Edad del discente (16-50)                      |
| anio_cursa       | Integer     | Año académico (1-6)                            |
| carrera          | String(100) | Carrera que cursa                              |
| compania         | String(50)  | Compañía a la que pertenece                    |

**Opciones de Carrera:**
- Tronco Común
- Ingeniería en Computación e Informática
- Ingeniería Industrial
- Ingeniería en Comunicaciones y Electrónica
- Ingeniería en Construcción

**Opciones de Compañía:**
- Primera Cía.
- Segunda Cía.
- Tercera Cía.
- Cuarta Cía.
- Cía. Oficiales

---

## 4. Flujo de Datos

### 4.1 Flujo de Registro de Discentes

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Discente   │     │   Sistema    │     │    Base de   │
│              │     │              │     │    Datos     │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       │  1. Accede a       │                    │
       │     /registro      │                    │
       │───────────────────>│                    │
       │                    │                    │
       │  2. Muestra form   │                    │
       │<───────────────────│                    │
       │                    │                    │
       │  3. Envía datos    │                    │
       │   (matrícula,      │                    │
       │    nombre, etc.)   │                    │
       │───────────────────>│                    │
       │                    │  4. Valida datos   │
       │                    │     y matrícula    │
       │                    │───────────────────>│
       │                    │<───────────────────│
       │                    │                    │
       │                    │  5. Crea usuario   │
       │                    │     con hash       │
       │                    │───────────────────>│
       │                    │                    │
       │  6. Redirige a     │                    │
       │     registro-      │                    │
       │     exitoso        │                    │
       │<───────────────────│                    │
       │                    │                    │
```

### 4.2 Flujo de Aplicación de Cuestionario

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Discente   │     │   Sistema    │     │    Base de   │
│              │     │              │     │    Datos     │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       │  1. Selecciona     │                    │
       │     cuestionario   │                    │
       │───────────────────>│                    │
       │                    │  2. Obtiene        │
       │                    │     preguntas      │
       │                    │───────────────────>│
       │                    │<───────────────────│
       │  3. Muestra        │                    │
       │     formulario     │                    │
       │<───────────────────│                    │
       │                    │                    │
       │  4. Envía          │                    │
       │     respuestas     │                    │
       │───────────────────>│                    │
       │                    │  5. Valida         │
       │                    │  6. Calcula puntaje│
       │                    │  7. Clasifica riesgo
       │                    │  8. Detecta P9     │
       │                    │                    │
       │                    │  9. Guarda         │
       │                    │     evaluación     │
       │                    │───────────────────>│
       │                    │                    │
       │                    │  10. Genera alerta │
       │                    │      (si aplica)   │
       │                    │───────────────────>│
       │                    │                    │
       │  11. Muestra       │                    │
       │      resultado     │                    │
       │<───────────────────│                    │
       │                    │                    │
```

### 4.3 Flujo de Generación de Alertas

```python
# Reglas implementadas en AlertaService

REGLA 1: Pregunta Crítica (P9 del PHQ-9)
    SI respuesta_P9 >= 1:
        GENERAR alerta prioridad="CRÍTICA"
        tipo="pregunta_critica"

REGLA 2: Nivel de Riesgo por Puntaje
    SI nivel_riesgo == "leve":
        GENERAR alerta prioridad="baja"
    SI nivel_riesgo == "moderado":
        GENERAR alerta prioridad="media"
    SI nivel_riesgo in ["moderado_severo", "severo"]:
        GENERAR alerta prioridad="alta"
```

---

## 5. Módulo de Registro de Discentes

### 5.1 Funcionalidad

El sistema permite el auto-registro de discentes desde la pantalla de login, sin necesidad de intervención administrativa.

### 5.2 Campos del Formulario de Registro

| Campo              | Tipo       | Validación                              | Obligatorio |
|--------------------|------------|----------------------------------------|-------------|
| Nombre             | Texto      | Mínimo 2 caracteres                    | Sí          |
| Apellido Paterno   | Texto      | Mínimo 2 caracteres                    | Sí          |
| Apellido Materno   | Texto      | -                                      | No          |
| Matrícula          | Texto      | Formato: letra + números (ej: A12345)  | Sí          |
| Edad               | Número     | Entre 16 y 50 años                     | Sí          |
| Año que Cursa      | Selección  | 1° a 6° año                            | Sí          |
| Carrera            | Selección  | 5 opciones predefinidas                | Sí          |
| Compañía           | Selección  | 5 opciones predefinidas                | Sí          |
| Contraseña         | Password   | Mínimo 6 caracteres                    | Sí          |
| Confirmar Password | Password   | Debe coincidir                         | Sí          |

### 5.3 Validaciones Implementadas

1. **Formato de matrícula**: Expresión regular `^[A-Z]\d+$`
2. **Unicidad de matrícula**: Verificación contra base de datos
3. **Rango de edad**: 16-50 años
4. **Coincidencia de contraseñas**: Validación cliente y servidor
5. **Campos obligatorios**: Validación HTML5 y backend

### 5.4 Flujo Post-Registro

1. Usuario completa formulario
2. Sistema valida datos
3. Crea usuario con rol "discente"
4. Genera email automático: `{matricula}@mentiscura.local`
5. Redirige a página de "Registro Exitoso"
6. Muestra matrícula como usuario de acceso
7. Ofrece botón para ir a login

---

## 6. Consideraciones Éticas y de Confidencialidad

### 6.1 Principios Implementados

1. **Minimización de Datos**: Solo se recopilan datos estrictamente necesarios para el tamizaje.

2. **Control de Acceso**: Sistema RBAC (Role-Based Access Control) con tres niveles:
   - Discente: Solo accede a sus propias evaluaciones
   - Orientador: Accede a alertas y evaluaciones para seguimiento
   - Administrador: Gestión técnica del sistema

3. **Trazabilidad**: Bitácora de auditoría registra:
   - Todos los accesos al sistema
   - Consultas a evaluaciones de terceros
   - Atención de alertas
   - Modificaciones de usuarios

4. **No Diagnóstico**: El sistema explícitamente indica que:
   - NO realiza diagnósticos clínicos
   - Es una herramienta de tamizaje/screening
   - Los resultados requieren evaluación profesional

### 6.2 Medidas de Seguridad

| Medida                    | Implementación                        |
|---------------------------|---------------------------------------|
| Autenticación segura      | Hash PBKDF2-SHA256 para contraseñas   |
| Protección CSRF           | Tokens Flask-WTF en formularios       |
| Sesiones seguras          | Cookies HttpOnly, SameSite=Lax        |
| Prevención SQL Injection  | ORM SQLAlchemy con consultas seguras  |
| Prevención XSS            | Escape automático en Jinja2           |
| Expiración de sesión      | 2 horas de inactividad                |
| Validación de entrada     | Regex para matrícula, rangos numéricos|

### 6.3 Disclaimer Legal

El sistema incluye avisos claros en la interfaz:
> "Este sistema NO realiza diagnósticos clínicos. Solo tamizaje y alertamiento."

---

## 7. Reglas de Evaluación PHQ

### 7.1 PHQ-2 (Patient Health Questionnaire-2)

**Preguntas evaluadas:**
1. Poco interés o placer en hacer las cosas
2. Sentirse desanimado, deprimido o sin esperanza

**Escala de respuestas (últimas 2 semanas):**
- 0 = Nunca
- 1 = Varios días
- 2 = Más de la mitad de los días
- 3 = Casi todos los días

**Interpretación:**
| Puntaje | Interpretación                                    |
|---------|---------------------------------------------------|
| 0-2     | Sin indicador de riesgo depresivo                 |
| ≥3      | Indicador positivo - Se recomienda aplicar PHQ-9  |

### 7.2 PHQ-9 (Patient Health Questionnaire-9)

**Puntaje total: 0-27**

| Rango   | Clasificación        | Acción Sugerida                     |
|---------|----------------------|-------------------------------------|
| 0-4     | Mínimo o Ninguno     | Monitoreo rutinario                 |
| 5-9     | Leve                 | Vigilancia, apoyo de bienestar      |
| 10-14   | Moderado             | Evaluación profesional recomendada  |
| 15-19   | Moderadamente Severo | Intervención activa necesaria       |
| 20-27   | Severo               | Atención prioritaria inmediata      |

### 7.3 Pregunta 9 (Crítica)

> "Tener pensamientos de que estaría mejor muerto/a o de hacerse daño de alguna manera"

**Regla especial:** Cualquier respuesta ≥1 genera automáticamente una alerta de **prioridad CRÍTICA**, independientemente del puntaje total.

---

## 8. Búsqueda y Filtrado de Discentes

### 8.1 Funcionalidad para Orientadores

El módulo de "Listado de Discentes" permite a orientadores y administradores:

1. **Buscar por Matrícula**: Campo de texto con búsqueda en tiempo real
2. **Buscar por Nombre**: Búsqueda parcial en nombre completo
3. **Filtrar por Compañía**: Selector con las 5 compañías disponibles

### 8.2 Información Mostrada

| Campo           | Descripción                          |
|-----------------|--------------------------------------|
| Matrícula       | Identificador único del discente     |
| Nombre Completo | Nombre y apellidos                   |
| Edad            | Edad en años                         |
| Año             | Año académico que cursa (1°-6°)      |
| Carrera         | Nombre completo de la carrera        |
| Compañía        | Compañía a la que pertenece          |
| Estado          | Activo/Inactivo                      |

### 8.3 Acciones Disponibles

- **Ver Historial**: Acceso al historial completo de evaluaciones del discente
- **Filtrado combinado**: Matrícula + Nombre + Compañía simultáneamente

---

## 9. Conclusiones Técnicas

### Fortalezas del Prototipo

1. **Arquitectura escalable**: Diseño preparado para crecimiento
2. **Código mantenible**: Separación clara de responsabilidades
3. **Seguridad integrada**: Múltiples capas de protección
4. **Trazabilidad completa**: Auditoría de todas las acciones
5. **Auto-registro**: Discentes pueden registrarse sin intervención
6. **Búsqueda eficiente**: Filtrado por matrícula, nombre y compañía
7. **Base de datos robusta**: PostgreSQL para producción

### Limitaciones y Trabajo Futuro

1. **Autenticación**: Considerar integración con directorio institucional (LDAP)
2. **Notificaciones**: Implementar alertas por email/SMS
3. **Reportes**: Agregar exportación de estadísticas (PDF, Excel)
4. **Backup**: Automatizar respaldos de base de datos
5. **HTTPS**: Configurar certificado SSL para producción
6. **API REST**: Exponer endpoints para integración con otros sistemas

---

## 10. Glosario

| Término       | Definición                                                    |
|---------------|---------------------------------------------------------------|
| Discente      | Estudiante/cadete del sistema educativo militar               |
| Orientador    | Profesional de salud mental autorizado                        |
| PHQ-2         | Patient Health Questionnaire de 2 ítems                       |
| PHQ-9         | Patient Health Questionnaire de 9 ítems                       |
| Tamizaje      | Proceso de detección inicial de posibles casos                |
| P9            | Pregunta 9 del PHQ-9 (ideación suicida)                       |
| Alerta        | Notificación interna generada por reglas de riesgo            |
| Matrícula     | Identificador único del discente (formato: letra + números)   |
| RBAC          | Role-Based Access Control (Control de acceso basado en roles) |
| ORM           | Object-Relational Mapping (Mapeo objeto-relacional)           |

---

**Documento generado para fines de documentación de tesis.**

**Sistema**: Mentis Cura
**Versión**: 1.0.0
**Fecha**: 2026
