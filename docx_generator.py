import os
from datetime import datetime
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

def generate_contract(client, amount=480):
    """
    Генерация договора на основе шаблона
    """
    template_path = os.path.join(os.path.dirname(__file__), 'contract_template.docx')
    
    # Если шаблона нет, создаём простой договор на лету
    if not os.path.exists(template_path):
        return generate_simple_contract(client, amount)
    
    # Загружаем шаблон
    doc = Document(template_path)
    
    # Форматируем даты
    current_date = datetime.now().strftime('%d.%m.%Y')
    start_date = client.contract_start.strftime('%d.%m.%Y')
    end_date = client.contract_end.strftime('%d.%m.%Y')
    
    # Данные для подстановки
    replacements = {
        '{contract_number}': str(client.contract_number),
        '{personal_account}': str(client.personal_account),
        '{full_name}': client.full_name,
        '{microdistrict}': client.microdistrict,
        '{house}': client.house,
        '{apartment}': client.apartment,
        '{phone}': client.phone,
        '{start_date}': start_date,
        '{end_date}': end_date,
        '{current_date}': current_date,
        '{amount}': str(amount),
        '{amount_text}': number_to_text(amount),
        '{city}': 'Нефтеюганск',
        '{year}': str(datetime.now().year)
    }
    
    # Заменяем текст во всех параграфах
    for paragraph in doc.paragraphs:
        for key, value in replacements.items():
            if key in paragraph.text:
                paragraph.text = paragraph.text.replace(key, value)
    
    # Заменяем текст в таблицах
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for key, value in replacements.items():
                    if key in cell.text:
                        cell.text = cell.text.replace(key, value)
    
    # Сохраняем договор
    contracts_dir = os.path.join(os.path.dirname(__file__), 'contracts')
    if not os.path.exists(contracts_dir):
        os.makedirs(contracts_dir)
    
    filename = f"Договор_{client.contract_number}_{client.personal_account}_{client.full_name.replace(' ', '_')}.docx"
    filepath = os.path.join(contracts_dir, filename)
    
    doc.save(filepath)
    
    return filepath, filename

def generate_simple_contract(client, amount=480):
    """
    Создание простого договора если нет шаблона
    """
    from docx import Document
    from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    
    doc = Document()
    
    # Заголовок
    title = doc.add_heading('ДОГОВОР', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Номер договора
    doc.add_paragraph(f'№ {client.contract_number} / {client.personal_account}')
    doc.add_paragraph()
    
    # Дата
    current_date = datetime.now().strftime('%d.%m.%Y')
    doc.add_paragraph(f'г. Нефтеюганск                    {current_date}')
    doc.add_paragraph()
    
    # Стороны
    doc.add_paragraph('Общество с ограниченной ответственностью «Интерком», именуемое в дальнейшем «Исполнитель»,')
    doc.add_paragraph(f'и {client.full_name}, именуемый в дальнейшем «Заказчик», заключили настоящий договор о нижеследующем:')
    doc.add_paragraph()
    
    # Предмет договора
    doc.add_heading('1. ПРЕДМЕТ ДОГОВОРА', level=1)
    doc.add_paragraph(f'1.1. «Заказчик» поручает, а «Исполнитель» принимает на себя обслуживание ПЗУ по адресу:')
    doc.add_paragraph(f'мкр-н {client.microdistrict}, дом № {client.house}, кв. № {client.apartment}')
    doc.add_paragraph()
    
    # Срок действия
    doc.add_heading('2. СРОК ДЕЙСТВИЯ ДОГОВОРА', level=1)
    start_date = client.contract_start.strftime('%d.%m.%Y')
    end_date = client.contract_end.strftime('%d.%m.%Y')
    doc.add_paragraph(f'2.1. Договор на обслуживание системы ПЗУ заключается на срок с {start_date} по {end_date}')
    doc.add_paragraph('2.2. По истечении срока, с согласия обеих сторон, договор продлевается автоматически.')
    doc.add_paragraph()
    
    # Стоимость
    doc.add_heading('3. СТОИМОСТЬ И ПОРЯДОК РАСЧЕТОВ', level=1)
    doc.add_paragraph(f'3.1. Плата за обслуживание составляет {amount} ({number_to_text(amount)}) рублей в год.')
    doc.add_paragraph('3.2. Оплата производится авансом раз в год.')
    doc.add_paragraph()
    
    # Права и обязанности
    doc.add_heading('4. ПРАВА И ОБЯЗАННОСТИ СТОРОН', level=1)
    doc.add_paragraph('4.1. «Заказчик» обязуется оплатить услуги по обслуживанию ПЗУ авансом раз в год.')
    doc.add_paragraph('4.2. «Исполнитель» обязуется выполнять заявки по ремонту в течение 3-х дней.')
    doc.add_paragraph()
    
    # Адреса и реквизиты
    doc.add_heading('ЮРИДИЧЕСКИЕ АДРЕСА СТОРОН', level=1)
    doc.add_paragraph('Исполнитель:')
    doc.add_paragraph('ООО «Интерком»')
    doc.add_paragraph('628309, г. Нефтеюганск, ул. Мира, 2а, помещение 3, каб. 18')
    doc.add_paragraph('Тел.: (3463) 200-800')
    doc.add_paragraph('ИНН/КПП 8604045295/860401001')
    doc.add_paragraph()
    doc.add_paragraph('Заказчик:')
    doc.add_paragraph(f'{client.full_name}')
    doc.add_paragraph(f'Адрес: мкр-н {client.microdistrict}, дом {client.house}, кв. {client.apartment}')
    doc.add_paragraph(f'Телефон: {client.phone}')
    doc.add_paragraph()
    
    # Подписи
    doc.add_paragraph()
    doc.add_paragraph('От Исполнителя:                    От Заказчика:')
    doc.add_paragraph('__________________                 __________________')
    doc.add_paragraph('/ Шибаев М.А. /                    / _______________ /')
    
    # Сохраняем
    contracts_dir = os.path.join(os.path.dirname(__file__), 'contracts')
    if not os.path.exists(contracts_dir):
        os.makedirs(contracts_dir)
    
    filename = f"Договор_{client.contract_number}_{client.personal_account}_{client.full_name.replace(' ', '_')}.docx"
    filepath = os.path.join(contracts_dir, filename)
    
    doc.save(filepath)
    
    return filepath, filename

def number_to_text(n):
    """Преобразование числа в текст для суммы прописью"""
    if n == 0:
        return 'ноль'
    
    numbers_1_19 = [
        '', 'один', 'два', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять',
        'десять', 'одиннадцать', 'двенадцать', 'тринадцать', 'четырнадцать', 'пятнадцать',
        'шестнадцать', 'семнадцать', 'восемнадцать', 'девятнадцать'
    ]
    
    tens = [
        '', '', 'двадцать', 'тридцать', 'сорок', 'пятьдесят',
        'шестьдесят', 'семьдесят', 'восемьдесят', 'девяносто'
    ]
    
    hundreds = [
        '', 'сто', 'двести', 'триста', 'четыреста', 'пятьсот',
        'шестьсот', 'семьсот', 'восемьсот', 'девятьсот'
    ]
    
    if n < 20:
        return numbers_1_19[n]
    elif n < 100:
        return tens[n // 10] + (' ' + numbers_1_19[n % 10] if n % 10 != 0 else '')
    elif n < 1000:
        return hundreds[n // 100] + (' ' + number_to_text(n % 100) if n % 100 != 0 else '')
    else:
        thousands = n // 1000
        remainder = n % 1000
        thousand_text = number_to_text(thousands) + ' тысяч' + ('и' if 2 <= thousands % 10 <= 4 else '')
        if remainder:
            thousand_text += ' ' + number_to_text(remainder)
        return thousand_text