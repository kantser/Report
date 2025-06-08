import streamlit as st
import pandas as pd
import database as db
from fpdf import FPDF
from io import BytesIO
import os

def generate_pdf_from_data(org_id, start_date, end_date, executor_id, project_manager_id, report_filename):
    org_name = db.get_organization_by_id(org_id)
    executor_full_name = db.get_executor_by_id(executor_id)
    pm_full_name = db.get_project_manager_by_id(project_manager_id)

    current_dir = os.path.dirname(__file__)
    font_path_regular = os.path.join(current_dir, 'fonts', 'DejaVuSansCondensed.ttf')
    font_path_bold = os.path.join(current_dir, 'fonts', 'DejaVuSansCondensed-Bold.ttf')

    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('DejaVuSansCondensed', '', font_path_regular, uni=True)
    pdf.add_font('DejaVuSansCondensed', 'B', font_path_bold, uni=True)
    pdf.set_font('DejaVuSansCondensed', '', 12)

    # Верхний правый угол
    pdf.set_xy(150, 10)
    pdf.cell(0, 10, 'Конфиденциально', 0, 1, 'R')
    pdf.set_xy(150, 15)
    pdf.cell(0, 10, 'Экз №____', 0, 1, 'R')
    pdf.ln(30)
    
    pdf.set_font('DejaVuSansCondensed', 'B', 16)
    pdf.multi_cell(0, 10, 'Отчет по результатам мониторинга информационной безопасности', 0, 'C')
    pdf.ln(10)

    pdf.set_font('DejaVuSansCondensed', '', 12)
    pdf.multi_cell(0, 10, f'{org_name}', 0, 'C')
    pdf.multi_cell(0, 10, f'За период с {start_date} по {end_date} года', 0, 'C')
    pdf.ln(140)
    
    pdf.set_x(20)
    pdf.cell(0, 10, f'Исполнил: {executor_full_name}', 0, 1, 'L')
    pdf.set_x(20)
    pdf.cell(0, 10, f'Руководитель проекта: {pm_full_name}', 0, 1, 'L')


    pdf_output = pdf.output(dest='S').encode('latin1')
    
    return pdf_output 