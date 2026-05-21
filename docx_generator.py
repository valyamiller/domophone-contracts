# pyright: reportMissingImports=false
# ruff: noqa

import os
from datetime import datetime
from docx import Document

def generate_contract(client, amount=480):
    """Генерация договора из шаблона Word"""
    
    template_path = os.path.join(os.path.dirname(__file__), 'contract_template.docx')
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Файл шаблона не найден: {template_path}")
    
    doc = Document(template_path)
    
    current_date = datetime.now().strftime('%d.%m.%Y')
    start_date = client.contract_start.strftime('%d.%m.%Y')
    end_date = client.contract_end.strftime('%d.%m.%Y')
    
    full_address = f"{client.microdistrict}-{client.house}-{client.apartment}"
    
    # Текст для пункта монтажа
    tube_clause = "3.2. Плата за монтаж абонентского устройства (АУ) составляет с одной квартиры, 3000 (три тысячи) рублей 00 коп."
    
    # Замены
    replacements = {
        '{microdistrict}': client.microdistrict,
        '{house}': client.house,
        '{apartment}': client.apartment,
        '{full_name}': client.full_name,
        '{phone}': client.phone,
        '{current_date}': current_date,
        '{start_date}': start_date,
        '{end_date}': end_date,
        '{amount}': str(amount),
        '{amount_text}': 'четыреста восемьдесят',
        '{personal_account}': client.personal_account,
        '{contract_number}': str(client.contract_number),
        '{full_address}': full_address,
    }
    
    # Заменяем текст во всех параграфах
    for paragraph in doc.paragraphs:
        # Сначала заменяем {installation_clause} на нужный текст
        if '{installation_clause}' in paragraph.text:
            if client.tube_installed:
                paragraph.text = paragraph.text.replace('{installation_clause}', tube_clause)
                # Меняем нумерацию последующих пунктов
                for p in doc.paragraphs:
                    if '3.3.' in p.text:
                        p.text = p.text.replace('3.3.', '3.4.')
                    elif '3.4.' in p.text:
                        p.text = p.text.replace('3.4.', '3.5.')
            else:
                # Удаляем пустую строку
                paragraph.text = paragraph.text.replace('{installation_clause}', '')
                for p in doc.paragraphs:
                    if '3.3.' in p.text:
                        p.text = p.text.replace('3.3.', '3.2.')
                    elif '3.4.' in p.text:
                        p.text = p.text.replace('3.4.', '3.3.')
        
        # Остальные замены
        for key, value in replacements.items():
            if key in paragraph.text:
                paragraph.text = paragraph.text.replace(key, value)
    
    # Заменяем текст в таблицах
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for key, value in replacements.items():
                        if key in paragraph.text:
                            paragraph.text = paragraph.text.replace(key, value)
    
    contracts_dir = os.path.join(os.path.dirname(__file__), 'contracts')
    if not os.path.exists(contracts_dir):
        os.makedirs(contracts_dir)
    
    filename = f"Договор_{client.contract_number}_{client.personal_account}.docx"
    filepath = os.path.join(contracts_dir, filename)
    
    doc.save(filepath)
    
    return filepath, filename