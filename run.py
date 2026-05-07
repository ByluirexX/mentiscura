#!/usr/bin/env python3
"""
================================================================================
MENTIS CURA - Script de Ejecucion
================================================================================
Archivo: run.py
Descripcion: Script principal para iniciar el servidor web de la aplicacion.
             Este es el punto de entrada del sistema.

Uso:
    python run.py

El servidor se iniciara en:
    http://127.0.0.1:5000

Notas:
    - 127.0.0.1 es "localhost" (tu propia computadora)
    - El puerto 5000 es el puerto por defecto de Flask
    - El modo debug permite ver cambios sin reiniciar el servidor

Autor: Luis Enrique Diaz Romero
Fecha: 2026
================================================================================
"""

# =============================================================================
# IMPORTACIONES
# =============================================================================
import os  # Para leer variables de entorno

# Importar la funcion factory que crea la aplicacion
from app import create_app


# =============================================================================
# CONFIGURACION DEL ENTORNO
# =============================================================================
# Leer el entorno desde variable de entorno FLASK_ENV
# Si no existe, usar 'development' por defecto
env = os.environ.get('FLASK_ENV', 'development')

# Crear la instancia de la aplicacion con la configuracion correspondiente
app = create_app(env)


# =============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# =============================================================================
# Este bloque solo se ejecuta cuando corres "python run.py" directamente
# No se ejecuta si el archivo es importado por otro modulo
if __name__ == '__main__':
    # -------------------------------------------------------------------------
    # Mostrar informacion de bienvenida en la consola
    # -------------------------------------------------------------------------
    print("\n" + "="*60)
    print("  Mentis Cura - Sistema de Monitoreo Psicológico")
    print("  Prototipo Académico v1.0")
    print("="*60)
    print(f"\n  Entorno: {env}")
    print("  URL: http://127.0.0.1:5000")

    # Mostrar usuarios de prueba para facilitar el acceso
    print("\n  Usuarios de prueba:")
    print("    - admin / admin123 (Administrador)")
    print("    - orientador / orient123 (Orientador)")
    print("    - A20001 / disc123 (Discente - usar matrícula)")
    print("\n" + "="*60 + "\n")

    # -------------------------------------------------------------------------
    # Iniciar el servidor web
    # -------------------------------------------------------------------------
    # Parametros:
    #   host: IP donde escuchar (127.0.0.1 = solo local)
    #   port: Puerto del servidor (5000 es el default de Flask)
    #   debug: True = recargar automatico y errores detallados
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0' if os.environ.get('PORT') else '127.0.0.1'
    app.run(
        host=host,
        port=port,
        debug=(env == 'development')
    )
