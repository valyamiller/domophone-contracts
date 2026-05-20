import pkgutil
import sys

# Патч для совместимости Flask с Python 3.14
if not hasattr(pkgutil, 'get_loader'):
    pkgutil.get_loader = pkgutil.find_loader

# Теперь запускаем приложение
from app import app

if __name__ == '__main__':
    print("=" * 50)
    print("Запуск приложения учёта договоров")
    print("=" * 50)
    app.run(debug=True, host='127.0.0.1', port=5000)