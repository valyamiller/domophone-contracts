#!/usr/bin/env python
import sys
import os

# Отключаем предупреждения
import warnings
warnings.filterwarnings('ignore')

# Устанавливаем переменные окружения для обхода проблем Flask
os.environ['FLASK_DEBUG'] = '0'

# Простой HTTP сервер для демонстрации
print("=" * 60)
print("ПРОБЛЕМА СОВМЕСТИМОСТИ")
print("=" * 60)
print("Ваша версия Python 3.14 несовместима с текущими версиями Flask.")
print()
print("РЕШЕНИЕ:")
print("1. Установите Python 3.11 или 3.12")
print("   Скачайте: https://www.python.org/downloads/release/python-3110/")
print()
print("2. ИЛИ используйте онлайн-версию на Replit или Glitch")
print()
print("3. ИЛИ установите более старую версию Flask, совместимую с Python 3.14")
print("   Выполните команду:")
print("   pip install flask==2.0.3 flask-sqlalchemy==2.5.1")
print("=" * 60)

# Пытаемся запустить с альтернативным подходом
try:
    print("\nПытаемся запустить с альтернативным методом...")
    
    # Используем импорт через importlib
    import importlib.util
    
    # Создаём простой WSGI сервер
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import json
    
    class SimpleHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = '''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Учёт договоров домофонных трубок</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                    .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
                    .error { background: #fee; border-left: 4px solid #f00; padding: 15px; margin: 20px 0; }
                    .solution { background: #e8f4fd; border-left: 4px solid #3498db; padding: 15px; margin: 20px 0; }
                    code { background: #eee; padding: 2px 6px; border-radius: 3px; }
                    button { background: #3498db; color: white; border: none; padding: 10px 20px; cursor: pointer; border-radius: 5px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Учёт договоров домофонных трубок</h1>
                    
                    <div class="error">
                        <h3>Ошибка совместимости</h3>
                        <p>Ваша версия Python 3.14 несовместима с текущей версией Flask.</p>
                    </div>
                    
                    <div class="solution">
                        <h3>Быстрое решение:</h3>
                        <p>Установите Python 3.11 или 3.12:</p>
                        <ol>
                            <li>Скачайте Python 3.11 с <a href="https://www.python.org/downloads/release/python-3110/">официального сайта</a></li>
                            <li>Установите его (обязательно отметьте "Add Python to PATH")</li>
                            <li>Переустановите зависимости: <code>pip install -r requirements.txt</code></li>
                            <li>Запустите приложение: <code>python app.py</code></li>
                        </ol>
                    </div>
                    
                    <div class="solution">
                        <h3>Альтернативное решение (попробуйте прямо сейчас):</h3>
                        <p>Установите старую версию Flask, совместимую с Python 3.14:</p>
                        <code>pip uninstall flask flask-sqlalchemy werkzeug -y</code><br>
                        <code>pip install flask==2.0.3 flask-sqlalchemy==2.5.1 werkzeug==2.0.3 python-dateutil</code>
                        <br><br>
                        <button onclick="location.reload()">Проверить после установки</button>
                    </div>
                    
                    <div class="solution">
                        <h3>Использовать онлайн-сервисы:</h3>
                        <p>Вы можете запустить это приложение на:</p>
                        <ul>
                            <li><a href="https://replit.com">Replit</a> - бесплатно</li>
                            <li><a href="https://glitch.com">Glitch</a> - бесплатно</li>
                            <li><a href="https://pythonanywhere.com">PythonAnywhere</a></li>
                        </ul>
                    </div>
                </div>
            </body>
            </html>
            '''
            
            self.wfile.write(html.encode())
    
    def run_server():
        port = 5000
        server_address = ('', port)
        httpd = HTTPServer(server_address, SimpleHandler)
        print(f"\nСервер запущен на http://localhost:{port}")
        print("Нажмите Ctrl+C для остановки")
        httpd.serve_forever()
    
    run_server()
    
except Exception as e:
    print(f"Ошибка: {e}")
    
print("\nНажмите Enter для выхода...")
input()