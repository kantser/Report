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
    processed_executor_position = re.sub(r'специалист', 'специалистом', executor_position, flags=re.IGNORECASE)

    # Текст для второй страницы, как на скриншоте
    text_lines = [
        f"Мной, {processed_executor_position} ООО «РВ ГРУПП»",
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

    c.showPage() # Добавляем новую страницу
    c.save()
    buffer.seek(0)
    return buffer

def _draw_table_headers(c, table_x, table_y, col_widths, header_row_height, headers):
    """
    Рисует заголовки таблицы.
    """
    c.setFont("DejaVu", 10)
    current_x = table_x
    for i, header in enumerate(headers):
        lines = header.split('\n')
        font_size = 10
        line_height = 12 # Высота строки для заголовков
        total_text_height = len(lines) * line_height
        y_cell_center = table_y - (header_row_height / 2)
        y_baseline_start = y_cell_center + (total_text_height / 2) - line_height

        for j, line in enumerate(lines):
            text_width = c.stringWidth(line, "DejaVu", font_size)
            x_offset = (col_widths[i] - text_width) / 2 # Центрируем текст по горизонтали
            c.drawString(current_x + x_offset, y_baseline_start - (j * line_height), line)
        
        current_x += col_widths[i]

    # Рисуем линии заголовков
    c.rect(table_x, table_y - header_row_height, sum(col_widths), header_row_height) # Общая рамка для заголовков
    current_x = table_x
    for i in range(len(col_widths)):
        if i > 0:
            c.line(current_x, table_y - header_row_height, current_x, table_y) # Вертикальные линии
        current_x += col_widths[i]

# Вспомогательная функция для переноса текста
def _get_wrapped_text_lines(canvas, text, font_name, font_size, max_width):
    if not text:
        return [''], 0

    text_str = str(text)
    canvas.setFont(font_name, font_size)

    lines = []
    current_line_words = []

    # Internal buffer to ensure text does not overflow
    internal_buffer = 15 # Add a small buffer to max_width for internal calculations
    effective_max_width = max_width - internal_buffer

    # Ensure effective_max_width is never negative or zero
    if effective_max_width <= 0:
        effective_max_width = 1 # Set to a minimal positive value to avoid division by zero or infinite loops

    words = text_str.split(' ')

    for word in words:
        word_width = canvas.stringWidth(word, font_name, font_size)

        if word_width > effective_max_width:
            if current_line_words:
                lines.append(" ".join(current_line_words))
                current_line_words = []
            
            temp_part = ""
            for char in word:
                if canvas.stringWidth(temp_part + char, font_name, font_size) <= effective_max_width:
                    temp_part += char
                else:
                    lines.append(temp_part)
                    temp_part = char
            if temp_part:
                lines.append(temp_part)
            
            continue 

        test_line_width = canvas.stringWidth(" ".join(current_line_words + [word]), font_name, font_size)

        if test_line_width <= effective_max_width:
            current_line_words.append(word)
        else:
            lines.append(" ".join(current_line_words))
            current_line_words = [word]

    if current_line_words:
        lines.append(" ".join(current_line_words))

    if not lines:
        lines.append('')

    line_height = 12 # Уменьшена высота строки для контента
    required_height = len(lines) * line_height

    return lines, required_height

def create_statistical_section_overlay(num_licenses, control_list_data, num_incidents_section1, num_blocked_resources,
                                       num_unidentified_carriers, num_info_messages, num_controlled_docs, num_time_violations):
    # print(f"DEBUG: control_list_data received: {control_list_data}")
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    font_path = os.path.join(CURRENT_DIR, 'fonts', 'DejaVuSansCondensed.ttf')
    pdfmetrics.registerFont(TTFont('DejaVu', font_path))
    
    c.setFont("DejaVu", 12)

    # Раздел I. Статистические сведения
    c.setFont("DejaVu", 16)
    c.drawCentredString(297, 780, "Раздел I. Статистические сведения")
    y_position = 750
    
    c.setFont("DejaVu", 12)
    c.drawString(60, y_position, f"— Количество задействованных лицензий - {num_licenses}")
    y_position -= 20

    c.drawString(60, y_position, "— Перечень лиц находящихся на контроле (должность, ФИО)")
    y_position -= 30

    # Параметры таблицы
    table_x = 60
    table_y = y_position # Начальная Y-позиция для таблицы
    # Скорректированная ширина столбцов: № п/п, Должность, ФИО, Наименование ПЭВМ, Период контроля
    col_widths = [30, 100, 120, 160, 110] 
    # row_height = 20 # Теперь высота строки будет динамической
    header_row_height = 40 # Увеличена высота строки для заголовков
    # Заголовки таблицы
    headers = ["№\nп/п", "Должность", "ФИО", "Наименование\nПЭВМ в ИС\nЗаказчика", "Период контроля"]
    
    # Пороги для переноса на новую страницу
    Y_THRESHOLD_FOR_ROWS = 60 # Порог для переноса строк таблицы
    Y_THRESHOLD_FOR_TEXT = 60 # Порог для переноса последующего текста

    # Рисуем заголовки таблицы в первый раз
    _draw_table_headers(c, table_x, table_y, col_widths, header_row_height, headers)

    # Данные таблицы
    data_y = table_y - header_row_height
    c.setFont("DejaVu", 10)
    
    # Определяем порядок колонок для извлечения данных из словаря
    column_keys = ['№ п/п', 'Должность', 'ФИО', 'Наименование ПЭВМ в ИС Заказчика', 'Период контроля']

    # Для каждой строки данных
    for i, row_data in enumerate(control_list_data):
        # Для каждой строки определяем максимальную необходимую высоту текстового контента
        current_row_max_text_height = 0 
        wrapped_cells = []

        # Подготавливаем данные для каждой ячейки, рассчитывая необходимую высоту
        # Если в таблице есть столбец '№ п/п', используем его, иначе генерируем по порядку
        cell_data_npp = row_data.get(column_keys[0], str(i + 1))
        lines_npp, height_npp = _get_wrapped_text_lines(c, cell_data_npp, "DejaVu", 10, col_widths[0])
        wrapped_cells.append(lines_npp)
        current_row_max_text_height = max(current_row_max_text_height, height_npp) 

        cell_data_pos = row_data.get(column_keys[1], '')
        lines_pos, height_pos = _get_wrapped_text_lines(c, cell_data_pos, "DejaVu", 10, col_widths[1])
        wrapped_cells.append(lines_pos)
        current_row_max_text_height = max(current_row_max_text_height, height_pos)

        cell_data_fio = row_data.get(column_keys[2], '')
        lines_fio, height_fio = _get_wrapped_text_lines(c, cell_data_fio, "DejaVu", 10, col_widths[2])
        wrapped_cells.append(lines_fio)
        current_row_max_text_height = max(current_row_max_text_height, height_fio)

        cell_data_pem = row_data.get(column_keys[3], '')
        lines_pem, height_pem = _get_wrapped_text_lines(c, cell_data_pem, "DejaVu", 10, col_widths[3])
        wrapped_cells.append(lines_pem)
        current_row_max_text_height = max(current_row_max_text_height, height_pem)

        cell_data_period = row_data.get(column_keys[4], '')
        lines_period, height_period = _get_wrapped_text_lines(c, cell_data_period, "DejaVu", 10, col_widths[4])
        wrapped_cells.append(lines_period)
        current_row_max_text_height = max(current_row_max_text_height, height_period)

        # Теперь, рассчитываем фактическую max_row_height для этой строки, учитывая минимальную высоту и вертикальный отступ.
        min_cell_height = 30 # Для визуальной привлекательности и предотвращения слишком тонких строк
        vertical_padding_for_cell = 14 # Желаемый отступ сверху и снизу от текстового блока (увеличено)
        max_row_height = max(min_cell_height, current_row_max_text_height + vertical_padding_for_cell)
        
        # Проверяем, достаточно ли места для следующей строки
        if data_y - max_row_height < Y_THRESHOLD_FOR_ROWS:
            c.showPage()
            data_y = A4[1] - 60
            _draw_table_headers(c, table_x, data_y, col_widths, header_row_height, headers)
            data_y -= header_row_height

        current_x = table_x
        # Отрисовка данных в ячейках
        for col_idx, lines in enumerate(wrapped_cells):
            font_size = 10
            line_height = 12 # Межстрочный интервал для контента
            total_text_height = len(lines) * line_height # Это высота фактического блока текста

            # Вычисляем вертикальное центрирование
            # max_row_height - это общая высота текущей ячейки (рассчитана выше)
            # total_text_height - это высота конкретного блока текста в этой ячейке

            y_cell_center = data_y - (max_row_height / 2)
            text_y_start = y_cell_center + (total_text_height / 2) - line_height - 2 # Добавлено небольшое смещение вниз

            for line_text in lines:
                text_width = c.stringWidth(line_text, "DejaVu", font_size)
                x_offset = (col_widths[col_idx] - text_width) / 2
                c.drawString(current_x + x_offset, text_y_start, line_text)
                text_y_start -= line_height # Межстрочный интервал
            current_x += col_widths[col_idx]
        
        # Рисуем рамку строки
        c.rect(table_x, data_y - max_row_height, sum(col_widths), max_row_height)
        current_x = table_x
        for j in range(len(col_widths)):
            if j > 0:
                c.line(current_x, data_y - max_row_height, current_x, data_y) # Вертикальные линии
            current_x += col_widths[j]
        
        data_y -= max_row_height

    y_position = data_y - 20 # Отступ после таблицы

    # Проверка на перенос оставшегося текста на новую страницу
    remaining_text_height = 7 * 20 + 20 # Приблизительная высота всех последующих строк текста
    if y_position - remaining_text_height < Y_THRESHOLD_FOR_TEXT:
        c.showPage()
        y_position = A4[1] - 60 # Сброс Y-позиции для новой страницы


    c.setFont("DejaVu", 12)
    c.drawString(60, y_position, f"— Количество выявленных инцидентов: {num_incidents_section1}")
    y_position -= 20
    c.drawString(60, y_position, f"— Количество выявленных/заблокированных вредоносных ресурсов: {num_blocked_resources}")
    y_position -= 20
    c.drawString(60, y_position, f"— Количество выявленных неустановленных внешних носителей: {num_unidentified_carriers}")
    y_position -= 20
    c.drawString(60, y_position, f"— Количество подготовленных информационных сообщений в адрес заказчика за месяц: {num_info_messages}")
    y_position -= 20
    c.drawString(60, y_position, f"— Количество документов находящихся на постоянном контроле: {num_controlled_docs}")
    y_position -= 20
    c.drawString(60, y_position, f"— Выявлено лиц с нарушением регламента рабочего времени: {num_time_violations} (ФИО)")
    y_position -= 20

    # НЕ вызываем c.showPage() здесь, так как управление страницами теперь в generate_full_pdf_from_data
    c.save()
    buffer.seek(0)
    return buffer

def generate_full_pdf_from_data(org_id, start_date, end_date, executor_id, project_manager_id, report_filename, contract_id,
                                 num_licenses, control_list_data, num_incidents_section1, num_blocked_resources,
                                 num_unidentified_carriers, num_info_messages, num_controlled_docs, num_time_violations):
    org_name = db.get_organization_by_id(org_id)
    executor_full_name_for_main_page = db.get_executor_by_id(executor_id, include_position=False)
    executor_position_for_section1 = db.get_executor_position_by_id(executor_id)
    pm_full_name = db.get_project_manager_by_id(project_manager_id)
    contract_data = db.get_contract_by_id(contract_id)
    contract_number = contract_data[0] if contract_data else "Н/Д"
    contract_date = contract_data[1] if contract_data else "Н/Д"

    writer = PdfWriter()

    # Главная страница
    main_template_path = os.path.join(CURRENT_DIR, 'templates', 'main_pdf_template.pdf')
    overlay_buffer_main = create_overlay(org_name, start_date, end_date, executor_full_name_for_main_page, pm_full_name)
    overlay_pdf_main = PdfReader(overlay_buffer_main)
    main_template_pdf = PdfReader(main_template_path)
    main_template_page = main_template_pdf.pages[0]
    overlay_page_main = overlay_pdf_main.pages[0]
    main_template_page.merge_page(overlay_page_main)
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

    # Раздел "Статистические сведения"
    statistical_section_overlay_buffer = create_statistical_section_overlay(
        num_licenses, control_list_data, num_incidents_section1, num_blocked_resources,
        num_unidentified_carriers, num_info_messages, num_controlled_docs, num_time_violations
    )
    statistical_section_overlay_pdf = PdfReader(statistical_section_overlay_buffer)
    
    # Путь к шаблону для статистического раздела
    statistical_template_path = os.path.join(CURRENT_DIR, 'templates', 'pdf_template.pdf')

    # Перебираем все страницы, сгенерированные в оверлее статистического раздела
    for i in range(len(statistical_section_overlay_pdf.pages)):
        # Важно: Создаем новый PdfReader для шаблона в каждой итерации, 
        # чтобы получить свежую, неизмененную страницу шаблона для каждого слияния.
        statistical_template_pdf_reader_fresh = PdfReader(statistical_template_path)
        statistical_template_page = statistical_template_pdf_reader_fresh.pages[0] 
        statistical_overlay_page = statistical_section_overlay_pdf.pages[i]
        statistical_template_page.merge_page(statistical_overlay_page)
        writer.add_page(statistical_template_page)

    # Создаем буфер для записи PDF
    output_buffer = BytesIO()
    writer.write(output_buffer)
    output_buffer.seek(0)
    
    # Возвращаем содержимое файла для скачивания
    return output_buffer.getvalue()
