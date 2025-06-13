import database as db
import os
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import re # Импортируем модуль re для регулярных выражений

# Определяем текущую директорию
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

def create_overlay(org_name, start_date, end_date, executor_full_name, pm_full_name):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    # Путь к TTF-шрифту
    font_path = os.path.join(CURRENT_DIR, 'fonts', 'DejaVuSansCondensed.ttf')

    # Регистрируем шрифт (один раз за сессию)
    pdfmetrics.registerFont(TTFont('DejaVu', font_path))

    c.setFont("DejaVu", 16)
    c.drawCentredString(297, 680, "Отчет по результатам мониторинга информационной безопасности")
    c.setFont("DejaVu", 12)
    c.drawCentredString(297, 650, org_name)
    c.drawCentredString(297, 630, f"За период с {start_date} по {end_date} года")
    c.setFont("DejaVu", 12)
    c.drawString(60, 120, f"Исполнил: {executor_full_name}")
    c.drawString(60, 100, f"Руководитель проекта: {pm_full_name}")
    c.save()
    buffer.seek(0)
    return buffer

def create_section1_overlay(executor_position, executor_full_name_no_position, contract_number, contract_date):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    font_path = os.path.join(CURRENT_DIR, 'fonts', 'DejaVuSansCondensed.ttf')
    pdfmetrics.registerFont(TTFont('DejaVu', font_path))
    
    c.setFont("DejaVu", 12)
    
    # Изменение окончания для слова "специалист" на "специалистом" с помощью регулярных выражений
    # Ищем слово "специалист" (регистронезависимо) и заменяем его на "специалистом"
    processed_executor_position = re.sub(r'специалист', 'специалистом', executor_position, flags=re.IGNORECASE)

    # Текст для второй страницы, как на скриншоте
    text_lines = [
        f"Мной, {processed_executor_position} ООО «РВ ГРУПП»,",
        f"{executor_full_name_no_position}, в соответствии с договором",
        f"{contract_number} от {contract_date} осуществлен анализ результатов работы",
        "системы мониторинга за отчетный период.",
        "",
        "Основными целями мониторинга за отчетный период являлись:",
        "",
        "1. Выявление угроз утечки информации по техническим каналам заказчика.",
        "2. Выявление фактов и признаков несанкционированного доступа к информации",
        "   заказчика связанных с действиями нарушителей имеющих доступ к информационным",
        "   системам.",
        "3. Выявление фактов и признаков несанкционированного доступа к информации",
        "   заказчика связанных с реализацией протоколов сетевого взаимодействия реализуемые",
        "   внутри распределённой сети.",
        "4. Выявление фактов и признаков несанкционированного доступа к информации",
        "   заказчика связанных с угрозами внедрения вредоносного программного обеспечения.",
        "5. Выявление фактов и признаков несанкционированного доступа к информации",
        "   заказчика связанных с угрозами виртуальной среды.",
        "6. Выявление угроз связанных с недекларированными возможностями используемого",
        "   программного обеспечения."
    ]

    y_position = 780 # Начальная позиция по Y
    for line in text_lines:
        c.drawString(60, y_position, line)
        y_position -= 14 # Межстрочный интервал

    c.save()
    buffer.seek(0)
    return buffer

def generate_pdf_from_data(org_id, start_date, end_date, executor_id, project_manager_id, report_filename, contract_id):
    org_name = db.get_organization_by_id(org_id)
    executor_full_name_for_main_page = db.get_executor_by_id(executor_id, include_position=False)
    executor_position_for_section1 = db.get_executor_position_by_id(executor_id)
    pm_full_name = db.get_project_manager_by_id(project_manager_id)
    contract_data = db.get_contract_by_id(contract_id)
    contract_number = contract_data[0] if contract_data else "Н/Д"
    contract_date = contract_data[1] if contract_data else "Н/Д"

    # Главная страница
    main_template_path = os.path.join(CURRENT_DIR, 'templates', 'main_pdf_template.pdf')
    overlay_buffer = create_overlay(org_name, start_date, end_date, executor_full_name_for_main_page, pm_full_name)
    overlay_pdf = PdfReader(overlay_buffer)
    main_template_pdf = PdfReader(main_template_path)
    writer = PdfWriter()
    main_template_page = main_template_pdf.pages[0]
    overlay_page = overlay_pdf.pages[0]
    main_template_page.merge_page(overlay_page)
    writer.add_page(main_template_page)

    # Раздел №1 (вторая страница)
    section1_template_path = os.path.join(CURRENT_DIR, 'templates', 'pdf_template.pdf')
    section1_overlay_buffer = create_section1_overlay(executor_position_for_section1, executor_full_name_for_main_page, contract_number, contract_date)
    section1_overlay_pdf = PdfReader(section1_overlay_buffer)
    section1_template_pdf = PdfReader(section1_template_path)
    section1_template_page = section1_template_pdf.pages[0]
    section1_overlay_page = section1_overlay_pdf.pages[0]
    section1_template_page.merge_page(section1_overlay_page)
    writer.add_page(section1_template_page)

    output_buffer = BytesIO()
    writer.write(output_buffer)
    output_buffer.seek(0)
    pdf_output = output_buffer.read()
    return pdf_output