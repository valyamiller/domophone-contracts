from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import os
from backup import create_backup, restore_backup, get_backups_list, delete_backup

print("=== ЗАПУСК ПРИЛОЖЕНИЯ ===")

app = Flask(__name__)

# Настройки
app.config['SECRET_KEY'] = 'your-secret-key-change-this-production'
app.config['DEBUG'] = False

# Подключение к PostgreSQL (данные сохраняются между деплоями)
DB_HOST = '192.168.0.5'
DB_PORT = '5432'
DB_USER = 'gen_user'
DB_PASS = 'Miller1994'
DB_NAME = 'default_db'

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

print(f"✅ Подключено к PostgreSQL: {DB_HOST}:{DB_PORT}/{DB_NAME}")

# Импорты
from models import db, Client, PaymentHistory, User
from auth import init_auth, setup_routes, role_required
from reports import ReportGenerator

print("=== МОДЕЛИ ИМПОРТИРОВАНЫ ===")

# Инициализация
db.init_app(app)
init_auth(app)

print("=== ИНИЦИАЛИЗАЦИЯ ВЫПОЛНЕНА ===")

# Создание таблиц и администратора
with app.app_context():
    db.create_all()
    if User.query.count() == 0:
        admin = User()
        admin.username = 'admin'
        admin.full_name = 'Администратор'
        admin.role = 'admin'
        admin.is_active = True
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Администратор создан: admin / admin123")
    print("=== БАЗА ДАННЫХ ГОТОВА ===")

setup_routes(app)

print("=== МАРШРУТЫ НАСТРОЕНЫ ===")

@app.route('/admin/backup')
@login_required
@role_required('admin')
def admin_backup():
    """Страница управления бэкапами"""
    backups = get_backups_list()
    return render_template('backup.html', backups=backups, datetime=datetime)

@app.route('/admin/backup/create')
@login_required
@role_required('admin')
def create_backup_route():
    """Создание нового бэкапа"""
    backup_info, error = create_backup()
    
    if error:
        flash(f'❌ Ошибка создания бэкапа: {error}', 'danger')
    else:
        size_mb = backup_info['size'] / 1024 / 1024
        flash(f'✅ Бэкап создан: {backup_info["timestamp"]} (размер: {size_mb:.2f} MB)', 'success')
    
    return redirect(url_for('admin_backup'))

@app.route('/admin/backup/restore/<filename>')
@login_required
@role_required('admin')
def restore_backup_route(filename):
    """Восстановление из бэкапа"""
    success, message = restore_backup(filename)
    
    if success:
        flash(f'✅ {message}', 'success')
        flash('⚠️ Страница будет перезагружена. Войдите заново.', 'warning')
    else:
        flash(f'❌ Ошибка восстановления: {message}', 'danger')
    
    return redirect(url_for('admin_backup'))

@app.route('/admin/backup/delete/<filename>')
@login_required
@role_required('admin')
def delete_backup_route(filename):
    """Удаление файла бэкапа"""
    success, message = delete_backup(filename)
    
    if success:
        flash(f'✅ {message}', 'success')
    else:
        flash(f'❌ {message}', 'danger')
    
    return redirect(url_for('admin_backup'))

# Health check
@app.route('/health')
def health():
    return "OK", 200

@app.route('/')
@login_required
def index():
    search_query = request.args.get('search', '').strip()
    
    if search_query:
        clients = Client.query.filter(
            (Client.personal_account.contains(search_query)) |
            (Client.full_name.contains(search_query)) |
            (Client.microdistrict.contains(search_query)) |
            (Client.house.contains(search_query)) |
            (Client.apartment.contains(search_query)) |
            (Client.phone.contains(search_query))
        )
    else:
        clients = Client.query
    
    if not current_user.can_view_all_contracts():
        clients = clients.filter_by(created_by=current_user.id)
    
    clients = clients.order_by(Client.contract_end).all()
    
    return render_template('index.html', clients=clients, datetime=datetime, search_query=search_query)

@app.route('/add_client', methods=['GET', 'POST'])
@login_required
@role_required('manager')
def add_client():
    if request.method == 'POST':
        full_name = request.form['full_name']
        microdistrict = request.form['microdistrict']
        house = request.form['house']
        apartment = request.form['apartment']
        phone = request.form['phone']
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        
        tube_installed = request.form.get('tube_installed') == 'true'
        
        client = Client()
        client.contract_number = Client.generate_contract_number()
        client.personal_account = Client.generate_personal_account()
        client.full_name = full_name
        client.microdistrict = microdistrict
        client.house = house
        client.apartment = apartment
        client.phone = phone
        client.contract_start = start_date
        client.contract_end = client.calculate_end_date(start_date)
        client.last_payment_date = start_date
        client.is_active = True
        client.created_by = current_user.id
        client.tube_installed = tube_installed
        if tube_installed:
            client.tube_install_date = start_date
        
        db.session.add(client)
        db.session.commit()
        
        amount = request.form.get('amount', 480, type=float)
        if amount > 0:
            history = PaymentHistory(
                client_id=client.id,
                payment_date=start_date,
                payment_amount=amount,
                period_from=start_date,
                period_to=client.contract_end,
                created_by=current_user.id,
                tube_installed=tube_installed
            )
            db.session.add(history)
            db.session.commit()
        
        flash(f'Клиент {full_name} успешно добавлен. Договор №{client.contract_number}, ЛС: {client.personal_account}', 'success')
        return redirect(url_for('index'))
    
    return render_template('add_client.html')

@app.route('/contract/<int:client_id>')
@login_required
def view_contract(client_id):
    client = Client.query.get_or_404(client_id)
    
    if not current_user.can_view_all_contracts() and client.created_by != current_user.id:
        flash('У вас нет прав для просмотра этого договора', 'danger')
        return redirect(url_for('index'))
    
    return render_template('contract_preview.html', client=client, datetime=datetime)

@app.route('/contract/download/<int:client_id>')
@login_required
def download_contract(client_id):
    from docx_generator import generate_contract
    
    client = Client.query.get_or_404(client_id)
    
    if not current_user.can_view_all_contracts() and client.created_by != current_user.id:
        flash('У вас нет прав для скачивания этого договора', 'danger')
        return redirect(url_for('index'))
    
    try:
        amount = 480
        filepath, filename = generate_contract(client, amount)
        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        flash(f'Ошибка при генерации договора: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/renew_contract/<int:client_id>', methods=['GET', 'POST'])
@login_required
def renew_contract(client_id):
    client = Client.query.get_or_404(client_id)
    
    if not current_user.can_edit_contract(client):
        flash('У вас нет прав для редактирования этого договора', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        payment_date = datetime.strptime(request.form['payment_date'], '%Y-%m-%d').date()
        payment_amount = request.form.get('amount', 480, type=float)
        tube_installed = request.form.get('tube_installed') == 'true'
        
        old_end = client.contract_end
        
        if tube_installed:
            client.tube_installed = True
            client.tube_install_date = payment_date
        
        client.renew_contract(payment_date)
        client.updated_by = current_user.id
        db.session.commit()
        
        if payment_amount > 0:
            history = PaymentHistory(
                client_id=client.id,
                payment_date=payment_date,
                payment_amount=payment_amount,
                period_from=payment_date if payment_date > old_end else old_end,
                period_to=client.contract_end,
                created_by=current_user.id,
                tube_installed=tube_installed
            )
            db.session.add(history)
            db.session.commit()
        
        flash(f'Договор №{client.contract_number} для {client.full_name} успешно продлён', 'success')
        return redirect(url_for('index'))
    
    return render_template('edit_contract.html', client=client, datetime=datetime)

@app.route('/notifications')
@login_required
def notifications():
    clients_query = Client.query.filter_by(is_active=True)
    
    if not current_user.can_view_all_contracts():
        clients_query = clients_query.filter_by(created_by=current_user.id)
    
    clients = clients_query.all()
    
    notifications_30 = []
    notifications_14 = []
    notifications_7 = []
    expired = []
    
    for client in clients:
        days = client.days_until_expiry()
        if days is None:
            continue
        if days < 0:
            expired.append(client)
        elif days <= 7:
            notifications_7.append(client)
        elif days <= 14:
            notifications_14.append(client)
        elif days <= 30:
            notifications_30.append(client)
    
    return render_template('notifications.html', 
                         notifications_30=notifications_30,
                         notifications_14=notifications_14,
                         notifications_7=notifications_7,
                         expired=expired)

@app.route('/client_history/<int:client_id>')
@login_required
def client_history(client_id):
    client = Client.query.get_or_404(client_id)
    
    if not current_user.can_view_all_contracts() and client.created_by != current_user.id:
        flash('У вас нет прав для просмотра истории этого договора', 'danger')
        return redirect(url_for('index'))
    
    payments = PaymentHistory.query.filter_by(client_id=client_id).order_by(PaymentHistory.payment_date.desc()).all()
    return render_template('client_history.html', client=client, payments=payments)

@app.route('/search')
@login_required
def search():
    search_query = request.args.get('q', '').strip()
    search_field = request.args.get('field', 'all')
    
    if search_query:
        if search_field == 'account':
            clients_query = Client.query.filter(Client.personal_account.contains(search_query))
        elif search_field == 'name':
            clients_query = Client.query.filter(Client.full_name.contains(search_query))
        elif search_field == 'address':
            clients_query = Client.query.filter(
                (Client.microdistrict.contains(search_query)) |
                (Client.house.contains(search_query)) |
                (Client.apartment.contains(search_query))
            )
        elif search_field == 'phone':
            clients_query = Client.query.filter(Client.phone.contains(search_query))
        else:
            clients_query = Client.query.filter(
                (Client.personal_account.contains(search_query)) |
                (Client.full_name.contains(search_query)) |
                (Client.microdistrict.contains(search_query)) |
                (Client.house.contains(search_query)) |
                (Client.apartment.contains(search_query)) |
                (Client.phone.contains(search_query))
            )
        
        if not current_user.can_view_all_contracts():
            clients_query = clients_query.filter_by(created_by=current_user.id)
        
        clients = clients_query.all()
    else:
        clients = []
    
    return render_template('search.html', clients=clients, search_query=search_query, search_field=search_field)

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html', datetime=datetime)

@app.route('/reports/expiring')
@login_required
def reports_expiring():
    clients_query = Client.query.filter_by(is_active=True)
    
    if not current_user.can_view_all_contracts():
        clients_query = clients_query.filter_by(created_by=current_user.id)
    
    clients = [c for c in clients_query.all() if c.days_until_expiry() is not None and c.days_until_expiry() <= 30]
    
    output = ReportGenerator.generate_expiring_contracts_report(clients)
    
    filename = f"отчет_истекающие_договоры_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(output, as_attachment=True, download_name=filename)

@app.route('/reports/monthly')
@login_required
def reports_monthly():
    if not current_user.can_view_all_contracts():
        clients = Client.query.filter_by(created_by=current_user.id).all()
    else:
        clients = Client.query.all()
    
    output = ReportGenerator.generate_monthly_statistics(clients)
    
    filename = f"статистика_месячная_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(output, as_attachment=True, download_name=filename)

@app.route('/reports/export_all')
@login_required
def reports_export_all():
    if not current_user.can_view_all_contracts():
        clients = Client.query.filter_by(created_by=current_user.id).order_by(Client.contract_number).all()
    else:
        clients = Client.query.order_by(Client.contract_number).all()
    
    output = ReportGenerator.generate_clients_export(clients)
    
    filename = f"все_клиенты_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(output, as_attachment=True, download_name=filename)

@app.route('/reports/filtered')
@login_required
def reports_filtered():
    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status', 'all')
    
    clients_query = Client.query
    
    if search_query:
        clients_query = clients_query.filter(
            (Client.personal_account.contains(search_query)) |
            (Client.full_name.contains(search_query)) |
            (Client.microdistrict.contains(search_query)) |
            (Client.house.contains(search_query)) |
            (Client.apartment.contains(search_query)) |
            (Client.phone.contains(search_query))
        )
    
    if status_filter == 'active':
        clients_query = clients_query.filter(Client.is_active == True, Client.contract_end >= datetime.now().date())
    elif status_filter == 'expiring_30':
        clients_query = clients_query.filter(Client.contract_end <= datetime.now().date() + timedelta(days=30))
    elif status_filter == 'expiring_7':
        clients_query = clients_query.filter(Client.contract_end <= datetime.now().date() + timedelta(days=7))
    elif status_filter == 'expired':
        clients_query = clients_query.filter(Client.contract_end < datetime.now().date())
    
    if not current_user.can_view_all_contracts():
        clients_query = clients_query.filter_by(created_by=current_user.id)
    
    clients = clients_query.order_by(Client.contract_number).all()
    output = ReportGenerator.generate_clients_export(clients)
    
    filename = f"экспорт_клиентов_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(output, as_attachment=True, download_name=filename)

@app.route('/admin/backup/download/<filename>')
@login_required
@role_required('admin')
def download_backup_route(filename):
    """Скачивание файла бэкапа"""
    from backup import get_backup_file_path
    
    filepath = get_backup_file_path(filename)
    if filepath and os.path.exists(filepath):
        return send_file(filepath, as_attachment=True, download_name=filename)
    else:
        flash('❌ Файл бэкапа не найден', 'danger')
        return redirect(url_for('admin_backup'))
    
@app.route('/delete_client/<int:client_id>')
@login_required
@role_required('admin')
def delete_client(client_id):
    """Удаление клиента (только для администраторов)"""
    client = Client.query.get_or_404(client_id)
    
    client_name = client.full_name
    client_number = client.contract_number
    
    try:
        PaymentHistory.query.filter_by(client_id=client.id).delete()
        db.session.delete(client)
        db.session.commit()
        flash(f'✅ Клиент {client_name} (договор №{client_number}) удалён', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Ошибка при удалении: {str(e)}', 'danger')
    
    return redirect(url_for('index'))

print("=== ВСЕ МАРШРУТЫ ЗАРЕГИСТРИРОВАНЫ ===")

if __name__ == '__main__':
    print("=== ЗАПУСК СЕРВЕРА ===")
    app.run(debug=False, host='0.0.0.0', port=8000)