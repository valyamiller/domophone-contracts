# pyright: reportMissingModuleSource=false
# ruff: noqa
import os
import subprocess
from datetime import datetime
import psycopg2

def get_db_connection():
    """Получение подключения к базе данных"""
    return psycopg2.connect(
        host='192.168.0.5',
        port='5432',
        user='gen_user',
        password='Miller1994',
        database='default_db'
    )

def create_backup():
    """Создание резервной копии базы данных"""
    try:
        # Создаём папку для бэкапов
        backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Имя файла с датой
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'backup_{timestamp}.sql')
        
        # Создаём дамп через pg_dump
        cmd = f'PGPASSWORD=Miller1994 pg_dump -h 192.168.0.5 -p 5432 -U gen_user -d default_db > {backup_file}'
        subprocess.run(cmd, shell=True, executable='/bin/bash', check=True)
        
        # Сохраняем информацию о бэкапе
        backup_info = {
            'file': backup_file,
            'timestamp': timestamp,
            'size': os.path.getsize(backup_file)
        }
        
        return backup_info, None
    except Exception as e:
        return None, str(e)

def restore_backup(backup_filename):
    """Восстановление базы данных из резервной копии"""
    try:
        backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
        backup_file = os.path.join(backup_dir, backup_filename)
        
        if not os.path.exists(backup_file):
            return False, "Файл бэкапа не найден"
        
        # Восстанавливаем через psql
        cmd = f'PGPASSWORD=Miller1994 psql -h 192.168.0.5 -p 5432 -U gen_user -d default_db < {backup_file}'
        subprocess.run(cmd, shell=True, executable='/bin/bash', check=True)
        
        return True, "База данных успешно восстановлена"
    except Exception as e:
        return False, str(e)

def get_backups_list():
    """Получение списка всех бэкапов"""
    backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
    if not os.path.exists(backup_dir):
        return []
    
    backups = []
    for file in os.listdir(backup_dir):
        if file.endswith('.sql'):
            filepath = os.path.join(backup_dir, file)
            stat = os.stat(filepath)
            backups.append({
                'filename': file,
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime).strftime('%d.%m.%Y %H:%M:%S')
            })
    
    # Сортируем по дате (новые сверху)
    backups.sort(key=lambda x: x['created'], reverse=True)
    return backups

def delete_backup(backup_filename):
    """Удаление файла бэкапа"""
    try:
        backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
        backup_file = os.path.join(backup_dir, backup_filename)
        
        if os.path.exists(backup_file):
            os.remove(backup_file)
            return True, "Бэкап удалён"
        return False, "Файл не найден"
    except Exception as e:
        return False, str(e)