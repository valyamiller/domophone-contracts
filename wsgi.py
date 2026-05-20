#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Импортируем приложение
try:
    from app import app
    print("✓ Flask app imported successfully")
except Exception as e:
    print(f"✗ Failed to import app: {e}")
    raise

# Gunicorn ожидает переменную 'application'
application = app

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=8000)