import streamlit as st
import pandas as pd
import database as db
import report_generator as rg
import json
import base64
import datetime as dt

def display_login_form():
    st.markdown(
        """
        <style>
        .custom-login-title-main {
            font-size: clamp(2rem, 6vw, 3.2rem);
            font-weight: 800;
            margin-bottom: 0.2em;
            margin-top: 0.5em;
            max-width: 100vw;
            overflow: hidden;
            display: block;
            text-align: center;
            line-height: 1.1;
        }
        .custom-login-title-sub {
            font-size: clamp(1.1rem, 3vw, 1.7rem);
            font-weight: 700;
            margin-bottom: 1.2em;
            margin-top: 0.1em;
            max-width: 100vw;
            overflow: hidden;
            display: block;
            text-align: center;
            line-height: 1.1;
        }
        </style>
        <h1 class='custom-login-title-main'>RV GROUP отчетность</h1>
        <div class='custom-login-title-sub'>Вход в систему</div>
        """,
        unsafe_allow_html=True
    )
    with st.form("login_form"):
        username = st.text_input("Логин")
        password = st.text_input("Пароль", type="password")
        submit = st.form_submit_button("Войти")
        if submit:
            user = db.login(username, password)
            if user:
                st.session_state.authenticated = True
                st.session_state.current_user = user
                st.session_state.current_user_id = db.get_user_id_by_username(user)
                st.session_state.menu_choice = "Главная страница"
                st.rerun()
            else:
                st.error("Неверный логин или пароль")

def display_sidebar():
    st.sidebar.image("images/rv_group_logo.jpg")
    st.sidebar.write(f"Текущий пользователь: {st.session_state.current_user}")

    st.sidebar.markdown(
        "<div style='font-weight:600; font-size:16px; margin-bottom:0; margin-top:10px;'>Меню пользователя</div>",
        unsafe_allow_html=True
    )
    st.sidebar.markdown("<hr style='margin-top:4px; margin-bottom:8px;'>", unsafe_allow_html=True)

    if 'menu_choice' not in st.session_state:
        st.session_state.menu_choice = "Главная страница"

    user_roles = db.get_user_roles(st.session_state.current_user_id) if hasattr(st.session_state, 'current_user_id') else []
    is_admin = 'Администратор' in [r[1] for r in user_roles]

    menu_items = [
        'Главная страница',
        'Ведение пользователей',
        'Ведение ролей',
        'Назначение ролей',
        'Назначение полномочий',
        'Ведение организаций',
        'Ведение исполнителей',
        'Ведение руководителей проекта',
        'Ведение должностей',
        'Ведение договоров',
        'Ведение угроз',
        'Выход'
    ]

    if is_admin:
        allowed_menu_items = set(menu_items)
    else:
        allowed_menu_items = set()
        for role in user_roles:
            allowed_menu_items.update(db.get_allowed_menu_items_for_role(role[0]))

    # Главная страница
    if 'Главная страница' in allowed_menu_items:
        if st.sidebar.button("Главная страница", use_container_width=True):
            st.session_state.menu_choice = "Главная страница"

    # --- Управление пользователями ---
    user_management_items = ['Ведение пользователей', 'Ведение ролей', 'Назначение ролей', 'Назначение полномочий']
    has_user_management = any(item in allowed_menu_items for item in user_management_items)
    if has_user_management:
        st.sidebar.markdown(
            "<div style='font-weight:600; font-size:16px; margin-bottom:0; margin-top:10px;'>Управление пользователями</div>",
            unsafe_allow_html=True
        )
        st.sidebar.markdown("<hr style='margin-top:4px; margin-bottom:8px;'>", unsafe_allow_html=True)
        for item in user_management_items:
            if item in allowed_menu_items:
                if st.sidebar.button(item, use_container_width=True):
                    st.session_state.menu_choice = item

    # --- Ведение справочников ---
    reference_items = ['Ведение организаций', 'Ведение исполнителей', 'Ведение руководителей проекта', 'Ведение должностей', 'Ведение договоров', 'Ведение угроз']
    has_reference_management = any(item in allowed_menu_items for item in reference_items)
    if has_reference_management:
        st.sidebar.markdown(
            "<div style='font-weight:600; font-size:16px; margin-bottom:0; margin-top:10px;'>Ведение справочников</div>",
            unsafe_allow_html=True
        )
        st.sidebar.markdown("<hr style='margin-top:4px; margin-bottom:8px;'>", unsafe_allow_html=True)
        with st.sidebar.expander("Ведение справочников", expanded=True):
            for item in reference_items:
                if item in allowed_menu_items:
                    if st.sidebar.button(item, use_container_width=True):
                        st.session_state.menu_choice = item

    # --- Системные действия ---
    system_items = ['Выход']
    has_system_actions = any(item in allowed_menu_items for item in system_items)
    if has_system_actions:
        st.sidebar.markdown(
            "<div style='font-weight:600; font-size:16px; margin-bottom:0; margin-top:10px;'>Системные действия</div>",
            unsafe_allow_html=True
        )
        st.sidebar.markdown("<hr style='margin-top:4px; margin-bottom:8px;'>", unsafe_allow_html=True)
        if 'Выход' in allowed_menu_items:
            if st.sidebar.button("Выход", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.current_user = None
                st.rerun()
    st.sidebar.markdown("Разработано компанией NaviTech© 2025")
    st.sidebar.markdown(
        '<a href="mailto:support@navitechlabs.ru" style="color:#fff;text-decoration:underline;">Связаться с поддержкой</a>',
        unsafe_allow_html=True
    )

def display_home_page():
    st.title("Главная страница")
    if st.button("Сформировать отчет"):
        st.session_state.menu_choice = "Формирование отчета"
        st.rerun()

    reports = db.get_all_reports()
    
    if reports:
        processed_reports = []
        for r in reports:
            print('DEBUG report row:', r)
            # Индексы последних двух столбцов (создал, дата)
            created_by_idx = len(r) - 2
            created_at_idx = len(r) - 1
            processed_reports.append([
                r[0], # ID
                r[1], # Организация
                r[2], # Начало периода
                r[3], # Конец периода
                f"{r[5]} {r[4]} {r[6] if r[6] else ''}".strip(), # ФИО исполнителя
                f"{r[8]} {r[7]} {r[9] if r[9] else ''}".strip(), # ФИО руководителя проекта
                r[10], # Имя файла
                r[created_by_idx], # Создал
                r[created_at_idx], # Дата и время создания
            ])

        df_reports = pd.DataFrame(processed_reports, columns=[
            "ID", "Организация", "Начало периода", "Конец периода", "ФИО исполнителя", "ФИО руководителя проекта", "Имя файла", "Создал", "Дата и время создания"
        ])
        report_ids = df_reports["ID"].tolist()
        
        selected_report_id = st.selectbox("Выберите отчет для печати", report_ids, key="report_select")

        if selected_report_id is not None:
            # report_data теперь содержит: id, organization_id, start_date, end_date, executor_id, project_manager_id, report_filename, contract_id
            report_data = db.get_report(selected_report_id)
            if report_data:
                # Извлекаем сырые данные для генерации PDF
                org_id = report_data['organization_id']
                start_date = report_data['start_date']
                end_date = report_data['end_date']
                executor_id = report_data['executor_id']
                project_manager_id = report_data['project_manager_id']
                report_filename = report_data['report_filename']
                contract_id = report_data['contract_id']

                # Извлекаем все статистические данные для полной версии отчета
                num_licenses = report_data['num_licenses']
                control_list_json = report_data['control_list_json']
                num_incidents_section1 = report_data['num_incidents_section1']
                num_blocked_resources = report_data['num_blocked_resources']
                num_unidentified_carriers = report_data['num_unidentified_carriers']
                num_info_messages = report_data['num_info_messages']
                num_controlled_docs = report_data['num_controlled_docs']
                num_time_violations = report_data['num_time_violations']

                # Десериализуем JSON-строку обратно в список словарей
                control_list_data = json.loads(control_list_json) if control_list_json else []
                # Добавляем автонумерацию строк
                for idx, row in enumerate(control_list_data, 1):
                    row['№ п/п'] = idx

                # Перед генерацией PDF убедимся, что incidents_section2 — список, а не строка
                incidents_section2 = report_data.get('incidents_section2_json', "[]")
                if isinstance(incidents_section2, str):
                    try:
                        incidents_section2 = json.loads(incidents_section2)
                    except Exception:
                        incidents_section2 = []
                selected_threat_direction = report_data.get('selected_threat_direction', "-")

                # --- Раздел III: объекты контроля ---
                control_objects_for_pdf = []
                external_control_objects_json = report_data.get('external_control_objects_json')
                if external_control_objects_json:
                    try:
                        control_objects_for_pdf = json.loads(external_control_objects_json)
                    except Exception:
                        control_objects_for_pdf = []
                if not control_objects_for_pdf:
                    fio_external = report_data.get('fio_external', '')
                    external_disks_table_json = report_data.get('external_disks_table_json', '[]')
                    try:
                        external_disks_table = json.loads(external_disks_table_json)
                    except Exception:
                        external_disks_table = []
                    control_objects_for_pdf = [{
                        'fio_external': fio_external,
                        'external_disks_table': external_disks_table
                    }]

                print('DEBUG: serializable_control_objects =', control_objects_for_pdf)
                # --- Раздел IV: продуктивность сотрудников ---
                productivity_violations = []
                productivity_violations_json = report_data.get('productivity_violations_json')
                if productivity_violations_json:
                    try:
                        productivity_violations = json.loads(productivity_violations_json)
                    except Exception:
                        productivity_violations = []
                pdf_output = rg.generate_full_pdf_from_data(
                    org_id, start_date, end_date, executor_id, project_manager_id, report_filename, contract_id,
                    num_licenses, control_list_data, num_incidents_section1, num_blocked_resources,
                    num_unidentified_carriers, num_info_messages, num_controlled_docs, num_time_violations,
                    incidents_section2,
                    control_objects_for_pdf,
                    productivity_violations
                )
                print('DEBUG: control_objects_for_pdf =', control_objects_for_pdf)

                # Гарантируем, что external_disks_table — список
                for obj in control_objects_for_pdf:
                    table = obj.get('external_disks_table')
                    if isinstance(table, str):
                        try:
                            obj['external_disks_table'] = json.loads(table)
                        except Exception:
                            obj['external_disks_table'] = []
                    elif not isinstance(table, list):
                        obj['external_disks_table'] = []

                col1, col2 = st.columns(2, gap="small")
                with col1:
                    st.download_button(
                        label=f"Скачать отчет {selected_report_id} в PDF",
                        data=pdf_output,
                        file_name=report_filename,
                        mime="application/pdf",
                        key=f"download_selected_report_{selected_report_id}",
                        use_container_width=True
                    )
                with col2:
                    if st.button(f"Удалить отчет {selected_report_id}", key=f"delete_selected_report_{selected_report_id}", use_container_width=True):
                        db.delete_report(selected_report_id)
                        st.success(f"Отчет {selected_report_id} успешно удален.")
                        st.rerun()
            else:
                st.error("Не удалось получить данные отчета.")
        else:
            st.info("Выберите отчет для печати.")
        
        st.subheader("Существующие отчеты")
        st.dataframe(df_reports, hide_index=True)
    else:
        st.info("Отчеты пока не сформированы.")

def display_report_form():
    if 'control_list_df' not in st.session_state or st.session_state.current_page == 'report_form': # Reset table when entering report form
        st.session_state.control_list_df = pd.DataFrame(
            columns=['№ п/п', 'Должность', 'ФИО', 'Наименование ПЭВМ в ИС Заказчика', 'Период контроля']
        )
    # Сброс инцидентов при каждом переходе в раздел
    prev_page = st.session_state.get('current_page')
    if prev_page != 'report_form':
        st.session_state['incidents_section2'] = []
        st.session_state['productivity_violations'] = []
    st.session_state.current_page = 'report_form' # Track current page
    st.title("Формирование отчета")
    st.markdown("<h3 style='margin-bottom: 1em;'>Формирование главной страницы</h3>", unsafe_allow_html=True)

    organizations = db.get_all_organizations()
    org_options = {org[1]: org[0] for org in organizations}
    selected_org_name = st.selectbox("Компания", list(org_options.keys()))
    selected_org_id = org_options.get(selected_org_name)

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("За период с")
    with col2:
        end_date = st.date_input("по")

    contracts = db.get_all_contracts()
    contract_options = {f"{c[1]} от {c[2]}": c[0] for c in contracts}
    selected_contract = st.selectbox("Договор", list(contract_options.keys())) if contract_options else None
    selected_contract_id = contract_options.get(selected_contract) if selected_contract else None

    positions = db.get_all_positions()
    pos_options = {p[1]: p[0] for p in positions}
    selected_position = st.selectbox("Должность исполнителя", list(pos_options.keys())) if pos_options else None
    selected_position_id = pos_options.get(selected_position) if selected_position else None

    executors = db.get_all_executors()
    filtered_executors = [e for e in executors if e[4] == selected_position_id] if selected_position_id else executors
    exec_options = {f"{e[2]} {e[1]} {e[3] if e[3] else ''}".strip(): e[0] for e in filtered_executors}
    selected_exec_name = st.selectbox("Исполнил", list(exec_options.keys())) if exec_options else None
    selected_exec_id = exec_options.get(selected_exec_name) if selected_exec_name else None

    project_managers = db.get_all_project_managers()
    pm_options = {f"{pm[2]} {pm[1]} {pm[3] if pm[3] else ''}".strip(): pm[0] for pm in project_managers}
    selected_pm_name = st.selectbox("Руководитель проекта", list(pm_options.keys()))
    selected_pm_id = pm_options.get(selected_pm_name)

    # Инициализация DataFrame для списка контроля
    if 'control_list_df' not in st.session_state:
        st.session_state.control_list_df = pd.DataFrame([
            {'№ п/п': 1, 'Должность': '', 'ФИО': '', 'Наименование ПЭВМ в ИС Заказчика': '', 'Период контроля': ''}
        ], columns=['№ п/п', 'Должность', 'ФИО', 'Наименование ПЭВМ в ИС Заказчика', 'Период контроля'])

    st.markdown("<h4 style='margin-top: 1em; margin-bottom: 0.5em;'>Раздел I. Статистические сведения</h4>", unsafe_allow_html=True)
    
    st.markdown("<h5 style='margin-top: 0.5em; margin-bottom: 0.2em;'>— Количество задействованных лицензий</h5>", unsafe_allow_html=True)
    num_licenses = st.number_input("", min_value=0, value=0, key="num_licenses", label_visibility="collapsed")

    st.markdown("<h5 style='margin-top: 0.5em; margin-bottom: 0.2em;'>— Перечень лиц находящихся на контроле (должность, ФИО)</h5>", unsafe_allow_html=True)
    
    # Редактируемая таблица
    # --- после редактирования ---
    # Автонумерация для всех строк, даже если они пустые
    if isinstance(st.session_state.control_list_df, pd.DataFrame):
        st.session_state.control_list_df['№ п/п'] = range(1, len(st.session_state.control_list_df) + 1)

    edited_df = st.data_editor(
        st.session_state.control_list_df,
        column_config={
            "№ п/п": st.column_config.NumberColumn("№ п/п", help="Порядковый номер", min_value=1, format="%d"),
            "Должность": st.column_config.TextColumn("Должность лица"),
            "ФИО": st.column_config.TextColumn("ФИО лица"),
            "Наименование ПЭВМ в ИС Заказчика": st.column_config.TextColumn("Наименование ПЭВМ в ИС Заказчика", help="Наименование ПЭВМ"),
            "Период контроля": st.column_config.TextColumn("Период контроля", help="Период контроля (например, 'ежемесячно')")
        },
        hide_index=True,
        num_rows="dynamic",
        use_container_width=True,
        key="control_list_editor"
    )
    # Сохраняем актуальные данные обратно в session_state
    st.session_state.control_list_df = edited_df.copy()

    st.markdown("<h5 style='margin-top: 0.5em; margin-bottom: 0.2em;'>— Количество выявленных инцидентов</h5>", unsafe_allow_html=True)
    num_incidents_section1 = st.number_input("", min_value=0, value=0, key="num_incidents_section1", label_visibility="collapsed")

    st.markdown("<h5 style='margin-top: 0.5em; margin-bottom: 0.2em;'>— Количество выявленных/заблокированных вредоносных ресурсов</h5>", unsafe_allow_html=True)
    num_blocked_resources = st.number_input("", min_value=0, value=0, key="num_blocked_resources", label_visibility="collapsed")

    st.markdown("<h5 style='margin-top: 0.5em; margin-bottom: 0.2em;'>— Количество выявленных неустановленных внешних носителей</h5>", unsafe_allow_html=True)
    num_unidentified_carriers = st.number_input("", min_value=0, value=0, key="num_unidentified_carriers", label_visibility="collapsed")

    st.markdown("<h5 style='margin-top: 0.5em; margin-bottom: 0.2em;'>— Количество подготовленных информационных сообщений в адрес заказчика за месяц</h5>", unsafe_allow_html=True)
    num_info_messages = st.number_input("", min_value=0, value=0, key="num_info_messages", label_visibility="collapsed")

    st.markdown("<h5 style='margin-top: 0.5em; margin-bottom: 0.2em;'>— Количество документов находящихся на постоянном контроле</h5>", unsafe_allow_html=True)
    num_controlled_docs = st.number_input("", min_value=0, value=0, key="num_controlled_docs", label_visibility="collapsed")

    st.markdown("<h5 style='margin-top: 0.5em; margin-bottom: 0.2em;'>— Выявлено лиц с нарушением регламента рабочего времени</h5>", unsafe_allow_html=True)
    num_time_violations = st.number_input("", min_value=0, value=0, key="num_time_violations", label_visibility="collapsed")

    st.markdown("<h4 style='margin-top: 2em; margin-bottom: 0.5em;'>Раздел II. Результаты объективного контроля</h4>", unsafe_allow_html=True)
    st.markdown("<b>Выявленные инциденты:</b>", unsafe_allow_html=True)

    # --- Динамические инциденты ---
    threat_list = db.get_all_threats()
    threat_names = [t[1] for t in threat_list]
    if not threat_names:
        threat_names = ["Нет данных"]
    if 'incidents_section2' not in st.session_state or not isinstance(st.session_state['incidents_section2'], list):
        st.session_state['incidents_section2'] = []

    if st.button("Добавить инцидент"):
        st.session_state['incidents_section2'].append({
            'threat_direction': threat_names[0] if threat_names and threat_names[0] != "Нет данных" else "",
            'description': ""
        })

    for idx, incident in enumerate(st.session_state['incidents_section2']):
        st.markdown(f"<b>Инцидент №{idx+1}</b>", unsafe_allow_html=True)
        st.session_state['incidents_section2'][idx]['threat_direction'] = st.selectbox(
            f"Направленность выявленной угрозы (Инцидент №{idx+1}):",
            threat_names,
            key=f"threat_direction_{idx}",
            index=threat_names.index(incident.get('threat_direction', threat_names[0])) if incident.get('threat_direction', threat_names[0]) in threat_names else 0,
            disabled=(threat_names == ["Нет данных"])
        )
        st.session_state['incidents_section2'][idx]['description'] = st.text_area(
            f"Описание инцидента (Инцидент №{idx+1}):",
            value=incident.get('description', ""),
            key=f"incident_desc_{idx}"
        )
        uploaded_files = st.file_uploader(
            f"Скриншоты для инцидента №{idx+1} (можно выбрать несколько)",
            type=["png", "jpg", "jpeg", "bmp"],
            accept_multiple_files=True,
            key=f"screenshots_{idx}"
        )
        st.session_state['incidents_section2'][idx]['screenshots'] = uploaded_files

    # --- КОНЕЦ раздела II ---

    # --- НОВЫЙ РАЗДЕЛ III ---
    st.markdown("<h4 style='margin-top: 2em; margin-bottom: 0.5em;'>Раздел III. Подключение внешних магнитных носителей информации</h4>", unsafe_allow_html=True)
    st.markdown("<b>Объекты контроля:</b>", unsafe_allow_html=True)

    # --- Динамические объекты контроля ---
    if 'external_control_objects' not in st.session_state or not isinstance(st.session_state['external_control_objects'], list):
        st.session_state['external_control_objects'] = []

    if st.button("Добавить объект контроля"):
        st.session_state['external_control_objects'].append({
            'fio_external': '',
            'external_disks_table': pd.DataFrame(columns=["Дата/Время", "Тип события", "Компьютер", "Пользователь", "Событие"])
        })

    for idx, control_object in enumerate(st.session_state['external_control_objects']):
        st.markdown(f"<b>Объект контроля №{idx+1}</b>", unsafe_allow_html=True)
        
        # ФИО сотрудника для текущего объекта контроля
        st.session_state['external_control_objects'][idx]['fio_external'] = st.text_input(
            f"ФИО сотрудника (Объект контроля №{idx+1}):",
            value=control_object.get('fio_external', ''),
            key=f"fio_external_{idx}"
        )

        # Таблица подключений внешних дисков для текущего объекта контроля
        st.markdown(f"<b>Список подключений внешних дисков сотрудника:</b>", unsafe_allow_html=True)
        
        # Инициализация таблицы если её нет
        if 'external_disks_table' not in control_object or not isinstance(control_object['external_disks_table'], pd.DataFrame):
            st.session_state['external_control_objects'][idx]['external_disks_table'] = pd.DataFrame(
                columns=["Дата/Время", "Тип события", "Компьютер", "Пользователь", "Событие"]
            )

        # Форма для добавления новой строки в таблицу
        with st.form(f"add_external_disk_row_form_{idx}", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                new_date = st.date_input("Дата", value=dt.date.today(), key=f"external_disk_date_{idx}")
            with col2:
                new_time = st.time_input("Время", value=dt.datetime.now().time(), key=f"external_disk_time_{idx}")
            new_type = st.text_input("Тип события", key=f"external_disk_type_{idx}")
            new_pc = st.text_input("Компьютер", key=f"external_disk_pc_{idx}")
            new_user = st.text_input("Пользователь", key=f"external_disk_user_{idx}")
            new_event = st.text_area("Событие", key=f"external_disk_event_{idx}")
            add_row = st.form_submit_button("Добавить запись")
            if add_row and new_date and new_time:
                dt_str = f"{new_time.strftime('%H:%M:%S')} {new_date.strftime('%d.%m.%Y')}"
                new_row = {
                    "Дата/Время": dt_str,
                    "Тип события": new_type,
                    "Компьютер": new_pc,
                    "Пользователь": new_user,
                    "Событие": new_event
                }
                st.session_state['external_control_objects'][idx]['external_disks_table'] = pd.concat([
                    st.session_state['external_control_objects'][idx]['external_disks_table'],
                    pd.DataFrame([new_row])
                ], ignore_index=True)
                print('DEBUG: st.session_state[external_control_objects] =', st.session_state['external_control_objects'])

        # Удаляем строки, где 'Дата/Время' пустая или None
        st.session_state['external_control_objects'][idx]['external_disks_table'] = st.session_state['external_control_objects'][idx]['external_disks_table'][
            st.session_state['external_control_objects'][idx]['external_disks_table']['Дата/Время'].notnull() & 
            (st.session_state['external_control_objects'][idx]['external_disks_table']['Дата/Время'] != '')
        ]

        # Отображение таблицы с возможностью редактирования
        external_disks_df = st.data_editor(
            st.session_state['external_control_objects'][idx]['external_disks_table'],
            column_config={
                "Дата/Время": st.column_config.TextColumn("Дата/Время", help="Дата и время события"),
                "Тип события": st.column_config.TextColumn("Тип события"),
                "Компьютер": st.column_config.TextColumn("Компьютер"),
                "Пользователь": st.column_config.TextColumn("Пользователь"),
                "Событие": st.column_config.TextColumn("Событие", help="Марка и устройство")
            },
            hide_index=True,
            num_rows="dynamic",
            use_container_width=True,
            key=f"external_disks_editor_{idx}"
        )
        st.session_state['external_control_objects'][idx]['external_disks_table'] = external_disks_df.copy()

        # Кнопка удаления объекта контроля
        if st.button(f"Удалить объект контроля №{idx+1}", key=f"delete_control_object_{idx}"):
            st.session_state['external_control_objects'].pop(idx)
            st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)

    # --- КОНЕЦ раздела III ---

    # --- НОВЫЙ РАЗДЕЛ IV ---
    st.markdown("<h4 style='margin-top: 2em; margin-bottom: 0.5em;'>Раздел IV. Продуктивность работы сотрудников</h4>", unsafe_allow_html=True)
    st.markdown("<b>Выявленные нарушения в расчете продуктивности рабочего дня:</b>", unsafe_allow_html=True)

    if 'productivity_violations' not in st.session_state or not isinstance(st.session_state['productivity_violations'], list):
        st.session_state['productivity_violations'] = []

    if st.button("Добавить сотрудника"):
        st.session_state['productivity_violations'].append({'employee': ''})

    for idx, violation in enumerate(st.session_state['productivity_violations']):
        st.session_state['productivity_violations'][idx]['employee'] = st.text_area(
            f"Сотрудник/нарушение №{idx+1}",
            value=violation.get('employee', ''),
            key=f"productivity_employee_{idx}"
        )
        if st.button(f"Удалить сотрудника №{idx+1}", key=f"delete_productivity_{idx}"):
            st.session_state['productivity_violations'].pop(idx)
            st.rerun()

    # --- КОНЕЦ раздела IV ---

    # Перемещённая и обновлённая кнопка "Сформировать отчёт" теперь в самом низу формы
    if st.button("Сформировать отчёт"):
        if selected_org_id and selected_exec_id and selected_pm_id and selected_contract_id:
            # Получаем актуальные данные из data_editor непосредственно перед формированием отчета
            # Streamlit автоматически обновляет st.session_state[key] при изменениях в виджете
            # raw_editor_data = st.session_state.get('control_list_editor', []) # default to empty list
            # print(f"DEBUG: raw_editor_data from session_state: {raw_editor_data}")

            # Преобразуем в DataFrame
            # if isinstance(raw_editor_data, pd.DataFrame):
            #     processed_control_list_df = raw_editor_data
            # else:
            #     try:
            #         processed_control_list_df = pd.DataFrame(raw_editor_data)
            #     except ValueError:
            #         # Если преобразование не удалось (например, некорректные данные или пустой список)
            #         processed_control_list_df = pd.DataFrame(columns=[
            #             '№ п/п', 'Должность', 'ФИО', 'Наименование ПЭВМ в ИС Заказчика', 'Период контроля'
            #         ])
            processed_control_list_df = st.session_state.control_list_df.copy() # Используем уже обновленный DataFrame
            # print(f"DEBUG: processed_control_list_df after conversion: {processed_control_list_df}")

            # Автонумерация для всех строк, даже если они пустые
            if not processed_control_list_df.empty:
                processed_control_list_df['№ п/п'] = range(1, len(processed_control_list_df) + 1)

            report_filename = f"Отчет_{selected_org_name}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}_full.pdf"
            
            # Сохранение всех данных, включая новые поля и таблицу
            serializable_incidents = serialize_incidents_for_db(st.session_state['incidents_section2'])
            
            # Сериализация объектов контроля для БД
            serializable_control_objects = serialize_control_objects_for_db(st.session_state['external_control_objects'])
            
            # Для обратной совместимости сохраняем первый объект контроля в старые поля
            first_control_object = st.session_state['external_control_objects'][0] if st.session_state['external_control_objects'] else {'fio_external': '', 'external_disks_table': pd.DataFrame()}
            
            print('DEBUG: serializable_control_objects =', serializable_control_objects)
            db.add_full_report(
                selected_org_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), 
                selected_exec_id, selected_pm_id, report_filename, selected_contract_id,
                num_licenses, processed_control_list_df.to_json(orient='records'), num_incidents_section1,
                num_blocked_resources, num_unidentified_carriers, num_info_messages,
                num_controlled_docs, num_time_violations,
                json.dumps(serializable_incidents),
                first_control_object.get('fio_external', ''),
                first_control_object.get('external_disks_table', pd.DataFrame()).to_json(orient='records'),
                json.dumps(serializable_control_objects),
                json.dumps(st.session_state.get('productivity_violations', [])),
                str(st.session_state.get('current_user', '') or ''),
                dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            control_list_data_for_pdf = processed_control_list_df.to_dict(orient='records')
            # print(f"DEBUG: control_list_data sent to PDF generator: {control_list_data_for_pdf}")
            # Перед генерацией PDF убедимся, что incidents_section2 — список, а не строка
            incidents_section2 = serializable_incidents
            if isinstance(incidents_section2, str):
                try:
                    incidents_section2 = json.loads(incidents_section2)
                except Exception:
                    incidents_section2 = []
            
            # Подготовка данных объектов контроля для PDF
            control_objects_for_pdf = serializable_control_objects
            if not control_objects_for_pdf:
                control_objects_for_pdf = [{
                    'fio_external': '',
                    'external_disks_table': []
                }]
            
            print('DEBUG: control_objects_for_pdf =', control_objects_for_pdf)
            pdf_output = rg.generate_full_pdf_from_data(
                selected_org_id, start_date.strftime('%d.%m.%Y'), end_date.strftime('%d.%m.%Y'), 
                selected_exec_id, selected_pm_id, report_filename, selected_contract_id,
                num_licenses, control_list_data_for_pdf, num_incidents_section1,
                num_blocked_resources, num_unidentified_carriers, num_info_messages,
                num_controlled_docs, num_time_violations,
                incidents_section2, control_objects_for_pdf,
                st.session_state.get('productivity_violations', [])
            )
            # Сброс данных объектов контроля после формирования отчета
            st.session_state['external_control_objects'] = []
            st.success("Отчёт успешно сформирован и сохранён!")
            st.session_state['incidents_section2'] = []
            st.session_state['productivity_violations'] = []
            st.download_button(
                label="Скачать отчёт в PDF",
                data=pdf_output,
                file_name=report_filename,
                mime="application/pdf"
            )
        else:
            st.error("Пожалуйста, заполните все обязательные поля для формирования отчета.")

def serialize_incidents_for_db(incidents):
    result = []
    for inc in incidents:
        inc_copy = inc.copy()
        inc_copy['screenshots'] = []
        for file in inc.get('screenshots', []):
            if hasattr(file, 'read'):
                file.seek(0)
                data = file.read()
                inc_copy['screenshots'].append(base64.b64encode(data).decode('utf-8'))
        result.append(inc_copy)
    return result

def serialize_control_objects_for_db(control_objects):
    result = []
    for obj in control_objects:
        obj_copy = obj.copy()
        table = obj.get('external_disks_table')
        if isinstance(table, pd.DataFrame):
            obj_copy['external_disks_table'] = table.to_dict(orient='records')
        elif isinstance(table, str):
            try:
                obj_copy['external_disks_table'] = json.loads(table)
            except Exception:
                obj_copy['external_disks_table'] = []
        elif isinstance(table, list):
            obj_copy['external_disks_table'] = table
        else:
            obj_copy['external_disks_table'] = []
        result.append(obj_copy)
    return result

def display_user_management():
    st.title("Ведение пользователей")

    with st.expander("Добавить нового пользователя"):
        with st.form("add_user_form"):
            new_username = st.text_input("Логин нового пользователя")
            new_password = st.text_input("Пароль нового пользователя", type="password")
            new_first_name = st.text_input("Имя (необязательно)")
            new_last_name = st.text_input("Фамилия (необязательно)")
            new_middle_name = st.text_input("Отчество (необязательно)")
            add_submit = st.form_submit_button("Добавить пользователя")

            if add_submit:
                if new_username and new_password:
                    if db.add_new_user(new_username, new_password, new_first_name, new_last_name, new_middle_name):
                        st.success(f"Пользователь {new_username} успешно добавлен!")
                        st.rerun()
                    else:
                        st.error(f"Пользователь с логином {new_username} уже существует.")
                else:
                    st.error("Логин и пароль не могут быть пустыми.")

    users = db.get_all_users()
    if users:
        with st.expander("Редактировать или удалить пользователя"):
            with st.form("edit_delete_user_form"):
                user_ids = [user[0] for user in users]
                selected_user_id = st.selectbox("Выберите пользователя по ID", user_ids)
                
                selected_user = next((user for user in users if user[0] == selected_user_id), None)
                
                if selected_user:
                    edit_username = st.text_input("Логин", value=selected_user[1])
                    edit_password = st.text_input("Новый пароль (оставьте пустым, чтобы не менять)", type="password")
                    edit_first_name = st.text_input("Имя", value=selected_user[2] if selected_user[2] else "")
                    edit_last_name = st.text_input("Фамилия", value=selected_user[3] if selected_user[3] else "")
                    edit_middle_name = st.text_input("Отчество", value=selected_user[4] if selected_user[4] else "")

                    col1, col2 = st.columns(2)
                    with col1:
                        update_submit = st.form_submit_button("Обновить пользователя")
                    with col2:
                        delete_submit = st.form_submit_button("Удалить пользователя")

                    if update_submit:
                        if edit_username:
                            db.update_existing_user(selected_user_id, edit_username, edit_password, edit_first_name, edit_last_name, edit_middle_name)
                            st.success("Пользователь успешно обновлен!")
                            st.rerun()
                        else:
                            st.error("Логин не может быть пустым.")
                    
                    if delete_submit:
                        db.delete_existing_user(selected_user_id)
                        st.success("Пользователь успешно удален!")
                        st.rerun()
    else:
        st.info("Пока нет пользователей для редактирования или удаления.")

    st.subheader("Существующие пользователи")
    if users:
        df = pd.DataFrame(users, columns=["ID", "Логин", "Имя", "Фамилия", "Отчество"])
        st.dataframe(df, hide_index=True)
    else:
        st.info("Пользователи пока не добавлены.")

def display_role_management():
    st.title("Ведение ролей")
    
    with st.expander("Добавить новую роль"):
        with st.form("add_role_form"):
            new_role_name = st.text_input("Название новой роли")
            add_role_submit = st.form_submit_button("Добавить роль")
            
            if add_role_submit:
                if new_role_name:
                    if db.add_new_role(new_role_name):
                        st.success(f"Роль '{new_role_name}' успешно добавлена!")
                        st.rerun()
                    else:
                        st.error(f"Роль с названием '{new_role_name}' уже существует.")
                else:
                    st.error("Название роли не может быть пустым.")

    roles = db.get_all_roles()
    if roles:
        with st.expander("Удалить роль"):
            with st.form("delete_role_form"):
                role_options = {role[1]: role[0] for role in roles if role[1] not in ["Администратор", "Пользователь"]} # Защита от удаления системных ролей
                
                if not role_options:
                    st.info("Нет ролей для удаления (системные роли защищены).")
                else:
                    selected_role_name_to_delete = st.selectbox("Выберите роль для удаления", list(role_options.keys()))
                    selected_role_id_to_delete = role_options.get(selected_role_name_to_delete)

                    delete_role_submit = st.form_submit_button("Удалить роль")

                    if delete_role_submit:
                        if selected_role_id_to_delete:
                            db.delete_role(selected_role_id_to_delete)
                            st.success(f"Роль '{selected_role_name_to_delete}' успешно удалена!")
                            st.rerun()
    
    st.subheader("Существующие роли")
    if roles:
        df_roles = pd.DataFrame(roles, columns=["ID", "Название роли"])
        st.dataframe(df_roles, hide_index=True)
    else:
        st.info("Роли пока не созданы.")

def display_role_assignment():
    st.title("Назначение ролей пользователям")
    
    users = db.get_all_users()
    roles = db.get_all_roles()

    if not users:
        st.info("Пока нет пользователей для назначения ролей. Добавьте пользователей в разделе 'Ведение пользователей'.")
        return

    if not roles:
        st.info("Пока нет ролей для назначения. Добавьте роли в разделе 'Ведение ролей'.")
        return
    
    user_options = {f"{user[0]} - {user[1]}": user[0] for user in users}
    selected_user_display = st.selectbox("Выберите пользователя", list(user_options.keys()))
    selected_user_id = user_options[selected_user_display]
    
    st.subheader(f"Роли для пользователя: {next((u[1] for u in users if u[0] == selected_user_id), 'Неизвестно')}")
    
    current_user_roles = db.get_user_roles(selected_user_id)
    if current_user_roles:
        df_user_roles = pd.DataFrame(current_user_roles, columns=["ID Роли", "Название роли"])
        st.dataframe(df_user_roles, hide_index=True)
    else:
        st.info("У этого пользователя пока нет назначенных ролей.")

    st.subheader("Назначить роль")
    available_roles_to_assign = [role for role in roles if role[0] not in [r[0] for r in current_user_roles]]
    if available_roles_to_assign:
        with st.form(key=f"assign_role_form_{selected_user_id}"):
            role_options_assign = {f"{role[0]} - {role[1]}": role[0] for role in available_roles_to_assign}
            selected_role_to_assign_display = st.selectbox("Выберите роль для назначения", list(role_options_assign.keys()))
            selected_role_id_to_assign = role_options_assign[selected_role_to_assign_display]
            assign_submit = st.form_submit_button("Назначить роль")

            if assign_submit:
                if db.assign_role_to_user(selected_user_id, selected_role_id_to_assign):
                    st.success("Роль успешно назначена!")
                    st.rerun()
                else:
                    st.error("Не удалось назначить роль (возможно, уже назначена).")
    else:
        st.info("Все доступные роли уже назначены этому пользователю.")

    st.subheader("Удалить роль")
    if current_user_roles:
        with st.form(key=f"remove_role_form_{selected_user_id}"):
            role_options_remove = {f"{role[0]} - {role[1]}": role[0] for role in current_user_roles}
            selected_role_to_remove_display = st.selectbox("Выберите роль для удаления", list(role_options_remove.keys()))
            selected_role_id_to_remove = role_options_remove[selected_role_to_remove_display]
            remove_submit = st.form_submit_button("Удалить роль")

            if remove_submit:
                db.remove_role_from_user(selected_user_id, selected_role_id_to_remove)
                st.success("Роль успешно удалена!")
                st.rerun()
    else:
        st.info("У этого пользователя нет назначенных ролей для удаления.")

def display_organization_management():
    st.title("Ведение организаций")

    with st.expander("Добавить новую организацию"):
        with st.form("add_organization_form"):
            new_org_name = st.text_input("Название организации")
            add_org_submit = st.form_submit_button("Добавить организацию")

            if add_org_submit:
                if new_org_name:
                    if db.add_organization(new_org_name):
                        st.success(f"Организация '{new_org_name}' успешно добавлена!")
                        st.rerun()
                    else:
                        st.error(f"Организация с названием '{new_org_name}' уже существует.")
                else:
                    st.error("Название организации не может быть пустым.")

    organizations = db.get_all_organizations()
    if organizations:
        with st.expander("Редактировать или удалить организацию"):
            with st.form("edit_delete_organization_form"):
                org_options = {org[1]: org[0] for org in organizations}
                selected_org_name = st.selectbox("Выберите организацию", list(org_options.keys()))
                selected_org_id = org_options.get(selected_org_name)

                if selected_org_id:
                    current_org_name = next((org[1] for org in organizations if org[0] == selected_org_id), None)
                    edit_org_name = st.text_input("Название организации", value=current_org_name)

                    col1, col2 = st.columns(2)
                    with col1:
                        update_org_submit = st.form_submit_button("Обновить организацию")
                    with col2:
                        delete_org_submit = st.form_submit_button("Удалить организацию")

                    if update_org_submit:
                        if edit_org_name:
                            if db.update_organization(selected_org_id, edit_org_name):
                                st.success("Организация успешно обновлена!")
                                st.rerun()
                            else:
                                st.error(f"Организация с названием '{edit_org_name}' уже существует.")
                        else:
                            st.error("Название организации не может быть пустым.")
                    
                    if delete_org_submit:
                        db.delete_organization(selected_org_id)
                        st.success("Организация успешно удалена!")
                        st.rerun()
    else:
        st.info("Пока нет организаций для редактирования или удаления.")

    st.subheader("Существующие организации")
    if organizations:
        df_organizations = pd.DataFrame(organizations, columns=["ID", "Название организации"])
        st.dataframe(df_organizations, hide_index=True)
    else:
        st.info("Организации пока не добавлены.")

def display_executor_management():
    st.title("Ведение исполнителей")

    positions = db.get_all_positions()
    pos_options = {p[1]: p[0] for p in positions}

    with st.expander("Добавить нового исполнителя"):
        with st.form("add_executor_form"):
            new_exec_first_name = st.text_input("Имя исполнителя")
            new_exec_last_name = st.text_input("Фамилия исполнителя")
            new_exec_middle_name = st.text_input("Отчество исполнителя (необязательно)")
            new_exec_position = st.selectbox("Должность", list(pos_options.keys()) if pos_options else ["Должности отсутствуют"], disabled=not bool(pos_options))
            add_exec_submit = st.form_submit_button("Добавить исполнителя")

            if add_exec_submit:
                if new_exec_first_name and new_exec_last_name:
                    if pos_options: # Check if there are actual positions to select from
                        db.add_executor(new_exec_first_name, new_exec_last_name, new_exec_middle_name, pos_options[new_exec_position])
                        st.success(f"Исполнитель {new_exec_first_name} {new_exec_last_name} успешно добавлен!")
                        st.rerun()
                    else:
                        st.error("Для добавления исполнителя необходимо сначала добавить хотя бы одну должность.")
                else:
                    st.error("Имя и фамилия исполнителя не могут быть пустыми.")

    executors = db.get_all_executors()
    if executors:
        with st.expander("Редактировать или удалить исполнителя"):
            with st.form("edit_delete_executor_form"):
                exec_ids = [exec[0] for exec in executors]
                selected_exec_id = st.selectbox("Выберите исполнителя по ID", exec_ids)
                selected_exec = next((exec for exec in executors if exec[0] == selected_exec_id), None)
                if selected_exec:
                    edit_exec_first_name = st.text_input("Имя", value=selected_exec[1])
                    edit_exec_last_name = st.text_input("Фамилия", value=selected_exec[2])
                    edit_exec_middle_name = st.text_input("Отчество", value=selected_exec[3] if selected_exec[3] else "")
                    # Ensure position selectbox is always visible even if no positions exist
                    edit_exec_position_options = list(pos_options.keys()) if pos_options else ["Должности отсутствуют"]
                    edit_exec_position_index = 0
                    if selected_exec[4] in pos_options.values():
                        edit_exec_position_index = list(pos_options.values()).index(selected_exec[4])
                    elif pos_options: # If there are positions but the selected one is not found, default to first
                        edit_exec_position_index = 0

                    edit_exec_position = st.selectbox("Должность",
                        options=edit_exec_position_options,
                        index=edit_exec_position_index,
                        disabled=not bool(pos_options))

                    col1, col2 = st.columns(2)
                    with col1:
                        update_exec_submit = st.form_submit_button("Обновить исполнителя")
                    with col2:
                        delete_exec_submit = st.form_submit_button("Удалить исполнителя")
                    if update_exec_submit:
                        if edit_exec_first_name and edit_exec_last_name:
                            if pos_options: # Check if there are actual positions to select from
                                db.update_executor(selected_exec_id, edit_exec_first_name, edit_exec_last_name, edit_exec_middle_name, pos_options[edit_exec_position])
                                st.success("Исполнитель успешно обновлен!")
                                st.rerun()
                            else:
                                st.error("Для обновления исполнителя необходимо сначала добавить хотя бы одну должность.")
                        else:
                            st.error("Имя и фамилия исполнителя не могут быть пустыми.")
                    
                    if delete_exec_submit:
                        db.delete_executor(selected_exec_id)
                        st.success("Исполнитель успешно удален!")
                        st.rerun()
    else:
        st.info("Пока нет исполнителей для редактирования или удаления.")

    st.subheader("Существующие исполнители")
    if executors:
        # Получаем названия должностей для отображения
        pos_dict = {p[0]: p[1] for p in positions}
        data = []
        for e in executors:
            data.append([
                e[0], e[1], e[2], e[3], pos_dict.get(e[4], "-")
            ])
        df_executors = pd.DataFrame(data, columns=["ID", "Имя", "Фамилия", "Отчество", "Должность"])
        st.dataframe(df_executors, hide_index=True)
    else:
        st.info("Исполнители пока не добавлены.")

def display_project_manager_management():
    st.title("Ведение руководителей проекта")

    with st.expander("Добавить нового руководителя проекта"):
        with st.form("add_pm_form"):
            new_pm_first_name = st.text_input("Имя руководителя проекта")
            new_pm_last_name = st.text_input("Фамилия руководителя проекта")
            new_pm_middle_name = st.text_input("Отчество руководителя проекта (необязательно)")
            add_pm_submit = st.form_submit_button("Добавить руководителя проекта")

            if add_pm_submit:
                if new_pm_first_name and new_pm_last_name:
                    if db.add_project_manager(new_pm_first_name, new_pm_last_name, new_pm_middle_name):
                        st.success(f"Руководитель проекта {new_pm_first_name} {new_pm_last_name} успешно добавлен!")
                        st.rerun()
                    else:
                        st.error(f"Руководитель проекта с ФИО {new_pm_first_name} {new_pm_last_name} {new_pm_middle_name if new_pm_middle_name else ''} уже существует.")
                else:
                    st.error("Имя и фамилия руководителя проекта не могут быть пустыми.")

    project_managers = db.get_all_project_managers()
    if project_managers:
        with st.expander("Редактировать или удалить руководителя проекта"):
            with st.form("edit_delete_pm_form"):
                pm_ids = [pm[0] for pm in project_managers]
                selected_pm_id = st.selectbox("Выберите руководителя проекта по ID", pm_ids)
                selected_pm = next((pm for pm in project_managers if pm[0] == selected_pm_id), None)
                if selected_pm:
                    edit_pm_first_name = st.text_input("Имя", value=selected_pm[1])
                    edit_pm_last_name = st.text_input("Фамилия", value=selected_pm[2])
                    edit_pm_middle_name = st.text_input("Отчество", value=selected_pm[3] if selected_pm[3] else "")

                    col1, col2 = st.columns(2)
                    with col1:
                        update_pm_submit = st.form_submit_button("Обновить руководителя проекта")
                    with col2:
                        delete_pm_submit = st.form_submit_button("Удалить руководителя проекта")

                    if update_pm_submit:
                        if edit_pm_first_name and edit_pm_last_name:
                            if db.update_project_manager(selected_pm_id, edit_pm_first_name, edit_pm_last_name, edit_pm_middle_name):
                                st.success("Руководитель проекта успешно обновлен!")
                                st.rerun()
                            else:
                                st.error(f"Руководитель проекта с ФИО {edit_pm_first_name} {edit_pm_last_name} {edit_pm_middle_name if edit_pm_middle_name else ''} уже существует.")
                        else:
                            st.error("Имя и фамилия руководителя проекта не могут быть пустыми.")

                    if delete_pm_submit:
                        db.delete_project_manager(selected_pm_id)
                        st.success("Руководитель проекта успешно удален!")
                        st.rerun()
    else:
        st.info("Пока нет руководителей проекта для редактирования или удаления.")

    st.subheader("Существующие руководители проекта")
    if project_managers:
        df_project_managers = pd.DataFrame(project_managers, columns=["ID", "Имя", "Фамилия", "Отчество"])
        st.dataframe(df_project_managers, hide_index=True)
    else:
        st.info("Руководители проекта пока не добавлены.")

def display_role_permissions_management():
    st.title("Назначение полномочий для ролей")

    roles = db.get_all_roles()
    if not roles:
        st.info("Роли не найдены. Пожалуйста, сначала добавьте роли.")
        return

    role_names = [role[1] for role in roles]
    selected_role_name = st.selectbox("Выберите роль", role_names)
    selected_role_id = [role[0] for role in roles if role[1] == selected_role_name][0]

    st.subheader(f"Настройка полномочий для роли: {selected_role_name}")

    # Получаем текущие полномочия для выбранной роли
    current_permissions = db.get_role_permissions(selected_role_id)
    current_permissions_dict = {key: bool(value) for key, value in current_permissions.items()}

    # Определяем все возможные пункты меню
    all_menu_items = [
        'Главная страница',
        'Ведение пользователей',
        'Ведение ролей',
        'Назначение ролей',
        'Назначение полномочий',
        'Ведение организаций',
        'Ведение исполнителей',
        'Ведение руководителей проекта',
        'Ведение должностей',
        'Ведение договоров',
        'Ведение угроз',
        'Выход'
    ]

    with st.form("role_permissions_form"):
        new_permissions = {}
        for item in all_menu_items:
            default_value = current_permissions_dict.get(item, False)
            new_permissions[item] = st.checkbox(f"Разрешить доступ к: {item}", value=default_value)

        save_permissions = st.form_submit_button("Сохранить полномочия")
        if save_permissions:
            # Преобразуем булевы значения в 0 или 1
            permissions_to_save = {item: (1 if allowed else 0) for item, allowed in new_permissions.items()}
            db.set_role_permissions(selected_role_id, permissions_to_save)
            st.success("Полномочия успешно обновлены!")
            st.rerun()

def display_position_management():
    st.title("Ведение должностей")

    with st.expander("Добавить новую должность"):
        with st.form("add_position_form"):
            new_position_name = st.text_input("Название должности")
            add_position_submit = st.form_submit_button("Добавить должность")

            if add_position_submit:
                if new_position_name:
                    if db.add_position(new_position_name):
                        st.success(f"Должность '{new_position_name}' успешно добавлена!")
                        st.rerun()
                    else:
                        st.error(f"Должность с названием '{new_position_name}' уже существует.")
                else:
                    st.error("Название должности не может быть пустым.")

    positions = db.get_all_positions()
    if positions:
        with st.expander("Редактировать или удалить должность"):
            with st.form("edit_delete_position_form"):
                pos_options = {pos[1]: pos[0] for pos in positions}
                selected_pos_name = st.selectbox("Выберите должность", list(pos_options.keys()))
                selected_pos_id = pos_options.get(selected_pos_name)

                if selected_pos_id:
                    current_pos_name = next((pos[1] for pos in positions if pos[0] == selected_pos_id), None)
                    edit_pos_name = st.text_input("Название должности", value=current_pos_name)

                    col1, col2 = st.columns(2)
                    with col1:
                        update_pos_submit = st.form_submit_button("Обновить должность")
                    with col2:
                        delete_pos_submit = st.form_submit_button("Удалить должность")

                    if update_pos_submit:
                        if edit_pos_name:
                            if db.update_position(selected_pos_id, edit_pos_name):
                                st.success("Должность успешно обновлена!")
                                st.rerun()
                            else:
                                st.error(f"Должность с названием '{edit_pos_name}' уже существует.")
                        else:
                            st.error("Название должности не может быть пустым.")

                    if delete_pos_submit:
                        db.delete_position(selected_pos_id)
                        st.success("Должность успешно удалена!")
                        st.rerun()
    else:
        st.info("Пока нет должностей для редактирования или удаления.")

    st.subheader("Существующие должности")
    if positions:
        df_positions = pd.DataFrame(positions, columns=["ID", "Название должности"])
        st.dataframe(df_positions, hide_index=True)
    else:
        st.info("Должности пока не добавлены.")

def display_contract_management():
    st.title("Ведение договоров")

    with st.expander("Добавить новый договор"):
        with st.form("add_contract_form"):
            new_contract_number = st.text_input("Номер договора")
            new_contract_date = st.date_input("Дата договора", value=None)
            add_contract_submit = st.form_submit_button("Добавить договор")

            if add_contract_submit:
                if new_contract_number and new_contract_date:
                    # Format date to string for database storage
                    new_contract_date_str = new_contract_date.strftime("%Y-%m-%d")
                    db.add_contract(new_contract_number, new_contract_date_str)
                    st.success(f"Договор №{new_contract_number} от {new_contract_date} успешно добавлен!")
                    st.rerun()
                else:
                    st.error("Номер и дата договора не могут быть пустыми.")

    contracts = db.get_all_contracts()
    if contracts:
        with st.expander("Редактировать или удалить договор"):
            with st.form("edit_delete_contract_form"):
                contract_ids = [contract[0] for contract in contracts]
                selected_contract_id = st.selectbox("Выберите договор по ID", contract_ids)
                selected_contract = next((c for c in contracts if c[0] == selected_contract_id), None)

                if selected_contract:
                    edit_contract_number = st.text_input("Номер договора", value=selected_contract[1])
                    # Convert string date from DB to date object for st.date_input
                    edit_contract_date = pd.to_datetime(selected_contract[2]).date()
                    edited_date_input = st.date_input("Дата договора", value=edit_contract_date)

                    col1, col2 = st.columns(2)
                    with col1:
                        update_contract_submit = st.form_submit_button("Обновить договор")
                    with col2:
                        delete_contract_submit = st.form_submit_button("Удалить договор")

                    if update_contract_submit:
                        if edit_contract_number and edited_date_input:
                            edited_date_input_str = edited_date_input.strftime("%Y-%m-%d")
                            db.update_contract(selected_contract_id, edit_contract_number, edited_date_input_str)
                            st.success("Договор успешно обновлен!")
                            st.rerun()
                        else:
                            st.error("Номер и дата договора не могут быть пустыми.")

                    if delete_contract_submit:
                        db.delete_contract(selected_contract_id)
                        st.success("Договор успешно удален!")
                        st.rerun()
    else:
        st.info("Пока нет договоров для редактирования или удаления.")

    st.subheader("Существующие договоры")
    if contracts:
        df_contracts = pd.DataFrame(contracts, columns=["ID", "Номер договора", "Дата договора"])
        st.dataframe(df_contracts, hide_index=True)
    else:
        st.info("Договоры пока не добавлены.")

def display_threats_management():
    st.title("Ведение угроз")

    with st.expander("Добавить новую угрозу"):
        with st.form("add_threat_form"):
            new_threat_name = st.text_input("Название угрозы")
            add_threat_submit = st.form_submit_button("Добавить угрозу")
            if add_threat_submit:
                if new_threat_name:
                    if db.add_threat(new_threat_name):
                        st.success(f"Угроза '{new_threat_name}' успешно добавлена!")
                        st.rerun()
                    else:
                        st.error(f"Угроза с названием '{new_threat_name}' уже существует.")
                else:
                    st.error("Название угрозы не может быть пустым.")

    threats = db.get_all_threats()
    if threats:
        with st.expander("Редактировать или удалить угрозу"):
            with st.form("edit_delete_threat_form"):
                threat_options = {th[1]: th[0] for th in threats}
                selected_threat_name = st.selectbox("Выберите угрозу", list(threat_options.keys()))
                selected_threat_id = threat_options.get(selected_threat_name)
                if selected_threat_id:
                    edit_threat_name = st.text_input("Название угрозы", value=selected_threat_name)
                    col1, col2 = st.columns(2)
                    with col1:
                        update_threat_submit = st.form_submit_button("Обновить угрозу")
                    with col2:
                        delete_threat_submit = st.form_submit_button("Удалить угрозу")
                    if update_threat_submit:
                        if edit_threat_name:
                            db.update_threat(selected_threat_id, edit_threat_name)
                            st.success("Угроза успешно обновлена!")
                            st.rerun()
                        else:
                            st.error("Название угрозы не может быть пустым.")
                    if delete_threat_submit:
                        db.delete_threat(selected_threat_id)
                        st.success("Угроза успешно удалена!")
                        st.rerun()
    else:
        st.info("Пока нет угроз для редактирования или удаления.")

    st.subheader("Существующие угрозы")
    if threats:
        df_threats = pd.DataFrame(threats, columns=["ID", "Название угрозы"])
        st.dataframe(df_threats, hide_index=True)
    else:
        st.info("Угрозы пока не добавлены.")

