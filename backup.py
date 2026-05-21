# pyright: reportMissingModuleSource=false
# ruff: noqa

import os
import subprocess
from datetime import datetime

DB_HOST = '192.168.0.5'
DB_PORT = '5432'
DB_USER = 'gen_user'
DB_PASS = 'Miller1994'
DB_NAME = 'default_db'

def create_backup():
    """Создание резервной копии базы данных"""
    try:
        backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'backup_{timestamp}.sql')
        
        cmd = f'PGPASSWORD={DB_PASS} pg_dump -h {DB_HOST} -p {DB_PORT} -U {DB_USER} -d {DB_NAME} > {backup_file}'
        subprocess.run(cmd, shell=True, executable='/bin/bash', check=True)
        
        backup_info = {
            'file': backup_file,
            'timestamp': timestamp,
            'size': os.path.getsize(backup_file),
            'filename': f'backup_{timestamp}.sql'
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
        
        cmd = f'PGPASSWORD={DB_PASS} psql -h {DB_HOST} -p {DB_PORT} -U {DB_USER} -d {DB_NAME} < {backup_file}'
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

def get_backup_file_path(backup_filename):
    """Получение пути к файлу бэкапа для скачивания"""
    backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
    backup_file = os.path.join(backup_dir, backup_filename)
    
    if os.path.exists(backup_file):
        return backup_file
    return None