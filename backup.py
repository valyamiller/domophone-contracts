# pyright: reportMissingModuleSource=false
# ruff: noqa

import os
import psycopg2
from datetime import datetime

DB_HOST = '192.168.0.5'
DB_PORT = '5432'
DB_USER = 'gen_user'
DB_PASS = 'Miller1994'
DB_NAME = 'default_db'

def create_backup():
    """Создание резервной копии базы данных через Python"""
    try:
        backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'backup_{timestamp}.sql')
        
        # Подключаемся к базе
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            # Пишем заголовок
            f.write(f"-- Backup created at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"-- Database: {DB_NAME}\n\n")
            
            # Получаем список всех таблиц
            cur = conn.cursor()
            cur.execute("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)
            tables = cur.fetchall()
            
            # Для каждой таблицы создаём дамп
            for table in tables:
                table_name = table[0]
                print(f"Бэкап таблицы: {table_name}")
                
                # Получаем структуру таблицы
                cur.execute(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}'
                    ORDER BY ordinal_position
                """)
                columns = cur.fetchall()
                
                # Получаем данные
                cur.execute(f"SELECT * FROM {table_name}")
                rows = cur.fetchall()
                
                if rows:
                    # Пишем INSERT запросы
                    for row in rows:
                        values = []
                        for val in row:
                            if val is None:
                                values.append('NULL')
                            elif isinstance(val, str):
                                values.append(f"'{val.replace(chr(39), chr(39)+chr(39))}'")
                            elif isinstance(val, datetime):
                                values.append(f"'{val.strftime('%Y-%m-%d %H:%M:%S')}'")
                            else:
                                values.append(str(val))
                        
                        insert_sql = f"INSERT INTO {table_name} VALUES ({', '.join(values)});\n"
                        f.write(insert_sql)
                f.write("\n")
            
            cur.close()
        
        conn.close()
        
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
        
        # Подключаемся к базе
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        cur = conn.cursor()
        
        with open(backup_file, 'r', encoding='utf-8') as f:
            sql = f.read()
            # Выполняем SQL запросы из бэкапа
            cur.execute(sql)
        
        conn.commit()
        cur.close()
        conn.close()
        
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