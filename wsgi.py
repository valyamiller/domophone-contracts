import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Импортируем приложение
from app import app as application

# Для совместимости с Gunicorn
app = application

if __name__ == "__main__":
    application.run()