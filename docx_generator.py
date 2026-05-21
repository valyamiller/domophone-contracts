# pyright: reportMissingImports=false
# ruff: noqa

import os
from datetime import datetime
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

def generate_contract(client, amount=480):
    """Генерация договора из шаблона Word"""
    
    template_path = os.path.join(os.path.dirname(__file__), 'contract_template.docx')
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Файл шаблона не найден: {template_path}")
    
    doc = Document(template_path)
    
    current_date = datetime.now().strftime('%d.%m.%Y')
    start_date = client.contract_start.strftime('%d.%m.%Y')
    end_date = client.contract_end.strftime('%d.%m.%Y')
    
    # Полный адрес
    full_address = f"{client.microdistrict}-{client.house}-{client.apartment}"
    
    # Формируем пункт о монтаже только если трубка установлена
    installation_clause = ""
    if client.tube_installed:
        installation_clause = "3.2. Плата за монтаж абонентского устройства (АУ) составляет с одной квартиры, 3000 (три тысячи) рублей 00 коп."
    
    # Все замены
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
        '{installation_clause}': installation_clause,
        '{full_address}': full_address,  # Добавляем полный адрес
    }
    
    # Определяем базовый стиль из существующего текста
    base_style = None
    base_font_name = 'Times New Roman'
    base_font_size = Pt(14)
    
    # Ищем образец стиля
    for paragraph in doc.paragraphs:
        if 'Договор' in paragraph.text or '1.1.' in paragraph.text:
            base_style = paragraph.style
            if paragraph.runs:
                base_font_name = paragraph.runs[0].font.name or 'Times New Roman'
                base_font_size = paragraph.runs[0].font.size or Pt(14)
            break
    
    # Заменяем текст во всех параграфах
    for paragraph in doc.paragraphs:
        text_changed = False
        for key, value in replacements.items():
            if key in paragraph.text:
                paragraph.text = paragraph.text.replace(key, value)
                text_changed = True
        
        # Применяем единый стиль ко всем параграфам
        if base_style:
            paragraph.style = base_style
        
        # Применяем шрифт ко всем runs
        for run in paragraph.runs:
            run.font.name = base_font_name
            run.font.size = base_font_size
    
    # Заменяем текст в таблицах
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for key, value in replacements.items():
                        if key in paragraph.text:
                            paragraph.text = paragraph.text.replace(key, value)
                    
                    # Применяем стиль и шрифт
                    if base_style:
                        paragraph.style = base_style
                    for run in paragraph.runs:
                        run.font.name = base_font_name
                        run.font.size = base_font_size
    
    # Сохраняем договор
    contracts_dir = os.path.join(os.path.dirname(__file__), 'contracts')
    if not os.path.exists(contracts_dir):
        os.makedirs(contracts_dir)
    
    filename = f"Договор_{client.contract_number}_{client.personal_account}.docx"
    filepath = os.path.join(contracts_dir, filename)
    
    doc.save(filepath)
    
    return filepath, filename