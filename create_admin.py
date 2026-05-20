import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User

def create_admin():
    with app.app_context():
        # Проверяем, есть ли уже администратор
        admin = User.query.filter_by(role='admin').first()
        if admin:
            print(f"Администратор уже существует:")
            print(f"  Логин: {admin.username}")
            print(f"  ФИО: {admin.full_name}")
            print("  Если забыли пароль, удалите contracts.db и создайте заново")
            return
        
        print("=" * 50)
        print("Создание первого администратора")
        print("=" * 50)
        
        username = input("Введите имя пользователя (логин): ").strip()
        if not username:
            username = "admin"
            print(f"Использую логин по умолчанию: {username}")
        
        full_name = input("Введите ФИО: ").strip()
        if not full_name:
            full_name = "Администратор"
            print(f"Использую ФИО по умолчанию: {full_name}")
        
        password = input("Введите пароль: ").strip()
        if not password:
            password = "admin123"
            print(f"Использую пароль по умолчанию: {password}")
        
        admin = User()
        admin.username = username
        admin.full_name = full_name
        admin.role = 'admin'
        admin.is_active = True
        admin.set_password(password)
        
        db.session.add(admin)
        db.session.commit()
        
        print("=" * 50)
        print("Администратор успешно создан!")
        print(f"Логин: {username}")
        print(f"Пароль: {password}")
        print("=" * 50)
        print("Теперь запустите: python app.py")
        print("И перейдите на: http://127.0.0.1:5000")
        print("=" * 50)

if __name__ == '__main__':
    create_admin()