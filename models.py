from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask_login import UserMixin
import random
import hashlib
import secrets

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    password_salt = db.Column(db.String(64), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='manager')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_login = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password):
        self.password_salt = secrets.token_hex(16)
        hash_obj = hashlib.sha256()
        hash_obj.update((password + self.password_salt).encode('utf-8'))
        self.password_hash = hash_obj.hexdigest()
    
    def check_password(self, password):
        if not self.password_hash or not self.password_salt:
            return False
        hash_obj = hashlib.sha256()
        hash_obj.update((password + self.password_salt).encode('utf-8'))
        return hash_obj.hexdigest() == self.password_hash
    
    def has_role(self, role_name):
        if self.role == 'admin':
            return True
        if role_name == 'viewer':
            return True
        if role_name == 'manager' and self.role in ['manager', 'senior']:
            return True
        if role_name == 'senior' and self.role == 'senior':
            return True
        if role_name == self.role:
            return True
        return False
    
    def can_edit_contract(self, contract):
        if self.role == 'admin':
            return True
        if self.role == 'senior':
            return True
        if self.role == 'manager' and contract.created_by == self.id:
            return True
        return False
    
    def can_view_all_contracts(self):
        return self.role in ['admin', 'senior']
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%d.%m.%Y %H:%M') if self.created_at else '',
            'last_login': self.last_login.strftime('%d.%m.%Y %H:%M') if self.last_login else 'Никогда'
        }

class Client(db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    contract_number = db.Column(db.Integer, unique=True, nullable=False)
    personal_account = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    microdistrict = db.Column(db.String(100), nullable=False)
    house = db.Column(db.String(20), nullable=False)
    apartment = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    contract_start = db.Column(db.Date, nullable=False)
    contract_end = db.Column(db.Date, nullable=False)
    last_payment_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)
    
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_contracts')
    updater = db.relationship('User', foreign_keys=[updated_by], backref='updated_contracts')
    
    @property
    def full_address(self):
        return f"{self.microdistrict}-{self.house}-{self.apartment}"
    
    @staticmethod
    def generate_personal_account():
        """Генерация уникального лицевого счёта"""
        while True:
            account = '1' + ''.join([str(random.randint(0, 9)) for _ in range(9)])
            if not Client.query.filter_by(personal_account=account).first():
                return account
    
    @staticmethod
    def generate_contract_number():
        """Генерация следующего номера договора"""
        last_client = Client.query.order_by(Client.contract_number.desc()).first()
        if last_client and last_client.contract_number:
            return last_client.contract_number + 1
        return 1
    
    def calculate_end_date(self, start_date):
        return start_date + relativedelta(months=12)
    
    def renew_contract(self, new_payment_date):
        if new_payment_date > self.contract_end:
            self.contract_start = new_payment_date
            self.contract_end = self.calculate_end_date(new_payment_date)
            self.last_payment_date = new_payment_date
        elif new_payment_date <= self.contract_end:
            new_end = self.calculate_end_date(self.contract_end)
            self.contract_end = new_end
            self.last_payment_date = new_payment_date
        self.is_active = True
    
    def days_until_expiry(self):
        if not self.is_active:
            return None
        delta = self.contract_end - datetime.now().date()
        return delta.days
    
    def to_dict(self):
        return {
            'id': self.id,
            'contract_number': self.contract_number,
            'personal_account': self.personal_account,
            'full_name': self.full_name,
            'full_address': self.full_address,
            'microdistrict': self.microdistrict,
            'house': self.house,
            'apartment': self.apartment,
            'phone': self.phone,
            'contract_start': self.contract_start.strftime('%d.%m.%Y'),
            'contract_end': self.contract_end.strftime('%d.%m.%Y'),
            'days_left': self.days_until_expiry(),
            'creator_name': self.creator.full_name if self.creator else 'Неизвестно',
            'created_at': self.created_at.strftime('%d.%m.%Y %H:%M') if self.created_at else ''
        }

class PaymentHistory(db.Model):
    __tablename__ = 'payment_history'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    payment_amount = db.Column(db.Float, default=0)
    period_from = db.Column(db.Date, nullable=False)
    period_to = db.Column(db.Date, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    client = db.relationship('Client', backref=db.backref('payments', lazy=True))
    creator = db.relationship('User', backref='payments')