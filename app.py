from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import os

print("=== ЗАПУСК ПРИЛОЖЕНИЯ ===")

app = Flask(__name__)

# Настройки
app.config['SECRET_KEY'] = 'your-secret-key-change-this-production'
app.config['DEBUG'] = False

# Настройки базы данных - PostgreSQL (Timeweb)
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_USER = os.environ.get('DB_USER', '')
DB_PASS = os.environ.get('DB_PASS', '')
DB_NAME = os.environ.get('DB_NAME', 'domophone_db')

# Если нет переменных окружения - используем SQLite
if DB_USER and DB_PASS:
    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    print("=== ИСПОЛЬЗУЕТСЯ POSTGRESQL ===")
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'contracts.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    print("=== ИСПОЛЬЗУЕТСЯ SQLITE ===")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

print("=== НАСТРОЙКИ БД ЗАГРУЖЕНЫ ===")

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
                created_by=current_user.id
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
        
        old_end = client.contract_end
        
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
                created_by=current_user.id
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

print("=== ВСЕ МАРШРУТЫ ЗАРЕГИСТРИРОВАНЫ ===")

if __name__ == '__main__':
    print("=== ЗАПУСК СЕРВЕРА ===")
    app.run(debug=False, host='0.0.0.0', port=8000)