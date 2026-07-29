"""
Scorpion Elite - API Endpoint para Scheduler
============================================
Este archivo expone un endpoint que puede ser llamado por un cron job externo
para ejecutar el scheduler automáticamente.
"""

import os
import sys

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar y ejecutar el scheduler
try:
    from scheduler import run_scheduler
    result = run_scheduler()
    print(f"✅ Scheduler completado: {result}")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
