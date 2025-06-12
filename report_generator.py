import database as db
import os
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

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

def generate_pdf_from_data(org_id, start_date, end_date, executor_id, project_manager_id, report_filename):
    org_name = db.get_organization_by_id(org_id)
    executor_full_name = db.get_executor_by_id(executor_id)
    pm_full_name = db.get_project_manager_by_id(project_manager_id)

    # Путь к шаблону PDF
    template_path = os.path.join(CURRENT_DIR, 'templates', 'main_pdf_template.pdf')

    # Генерируем наложение с текстом
    overlay_buffer = create_overlay(org_name, start_date, end_date, executor_full_name, pm_full_name)
    overlay_pdf = PdfReader(overlay_buffer)
    template_pdf = PdfReader(template_path)
    writer = PdfWriter()

    template_page = template_pdf.pages[0]
    overlay_page = overlay_pdf.pages[0]
    template_page.merge_page(overlay_page)
    writer.add_page(template_page)

    output_buffer = BytesIO()
    writer.write(output_buffer)
    output_buffer.seek(0)
    pdf_output = output_buffer.read()
    return pdf_output