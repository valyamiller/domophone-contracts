import os
from datetime import datetime

def generate_contract(client, amount=480):
    """Генерация договора в формате HTML"""
    
    current_date = datetime.now().strftime('%d.%m.%Y')
    start_date = client.contract_start.strftime('%d.%m.%Y')
    end_date = client.contract_end.strftime('%d.%m.%Y')
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Договор №{client.contract_number}</title>
        <style>
            body {{
                font-family: 'Times New Roman', Times, serif;
                margin: 50px;
                font-size: 14px;
                line-height: 1.4;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .title {{
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 5px;
            }}
            .subtitle {{
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 20px;
            }}
            .contract-number {{
                text-align: right;
                margin-bottom: 20px;
            }}
            .content {{
                margin-top: 20px;
            }}
            .signatures {{
                margin-top: 50px;
                display: flex;
                justify-content: space-between;
            }}
            .signature-block {{
                width: 45%;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            td, th {{
                border: 1px solid black;
                padding: 8px;
                vertical-align: top;
            }}
            .underline {{
                text-decoration: underline;
            }}
            .bold {{
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="contract-number">
            <strong>Договор № {client.contract_number} / {client.personal_account}</strong>
        </div>
        
        <div class="header">
            <div class="title">ДОГОВОР</div>
            <div class="subtitle">на монтаж и обслуживание системы переговорно-замкового устройства (ПЗУ)</div>
        </div>
        
        <p>г. Нефтеюганск                    {current_date}</p>
        
        <p><strong>Общество с ограниченной ответственностью «Интерком»</strong>, именуемое в дальнейшем «Исполнитель», в лице генерального директора Шибаева Михаила Анатольевича, действующего на основании Устава, с одной стороны, и <strong>{client.full_name}</strong>, именуемый в дальнейшем «Заказчик», с другой стороны, заключили настоящий договор о нижеследующем:</p>
        
        <h3>1. ПРЕДМЕТ ДОГОВОРА</h3>
        <p>1.1. «Заказчик» поручает, а «Исполнитель» принимает на себя обслуживание ПЗУ по адресу:</p>
        <p><strong>мкр-н {client.microdistrict}, дом № {client.house}, кв. № {client.apartment}</strong></p>
        <p>1.2. Обслуживание ПЗУ включает в себя поддержание работоспособности линии, замену вышедшего из строя оборудования, проведение профилактических осмотров, выполнение заявок.</p>
        
        <h3>2. СРОК ДЕЙСТВИЯ ДОГОВОРА</h3>
        <p>2.1. Договор на обслуживание системы ПЗУ заключается на срок с <strong>{start_date}</strong> по <strong>{end_date}</strong>.</p>
        <p>2.2. По истечении срока, с согласия обеих сторон, договор продлевается автоматически.</p>
        
        <h3>3. СТОИМОСТЬ И ПОРЯДОК РАСЧЕТОВ</h3>
        <p>3.1. Плата за обслуживание составляет <strong>{amount} (четыреста восемьдесят) рублей 00 коп в год</strong>.</p>
        <p>3.2. Оплата производится авансом раз в год.</p>
        
        <h3>4. ПРАВА И ОБЯЗАННОСТИ СТОРОН</h3>
        <p>4.1. «Заказчик» обязуется оплатить услуги по обслуживанию ПЗУ авансом раз в год.</p>
        <p>4.2. «Исполнитель» обязуется выполнять заявки по ремонту в течение 3-х дней.</p>
        
        <h3>5. АДРЕСА И РЕКВИЗИТЫ СТОРОН</h3>
        
        <table>
            <tr>
                <td width="50%"><strong>Исполнитель:</strong></td>
                <td width="50%"><strong>Заказчик:</strong></td>
            </tr>
            <tr>
                <td>ООО «Интерком»<br>
                628309, г. Нефтеюганск, ул. Мира, 2а<br>
                помещение 3, каб. 18<br>
                Тел.: (3463) 200-800<br>
                ИНН/КПП 8604045295/860401001<br>
                р/с 40702810602500118844<br>
                Банк: ООО "Банк Точка"<br>
                к/с 30101810745374525104<br>
                БИК 044525104</td>
                <td>{client.full_name}<br>
                Адрес: мкр-н {client.microdistrict}, дом {client.house}, кв. {client.apartment}<br>
                Телефон: {client.phone}<br>
                &nbsp;</td>
            </tr>
        </table>
        
        <div class="signatures">
            <div class="signature-block">
                От Исполнителя:<br><br>
                ______________ / Шибаев М.А. /
            </div>
            <div class="signature-block">
                От Заказчика:<br><br>
                ______________ / _______________ /
            </div>
        </div>
    </body>
    </html>
    """
    
    # Сохраняем HTML файл
    contracts_dir = os.path.join(os.path.dirname(__file__), 'contracts')
    if not os.path.exists(contracts_dir):
        os.makedirs(contracts_dir)
    
    filename = f"Договор_{client.contract_number}_{client.personal_account}_{client.full_name.replace(' ', '_')}.html"
    filepath = os.path.join(contracts_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return filepath, filename