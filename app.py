import streamlit as st
import database # Импортируем новый модуль для работы с БД
import ui # Будет импортирован после создания ui.py

# Инициализация состояния сессии
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark' # По умолчанию темная тема


def main():
    # Инициализация базы данных
    database.init_db()
    
    if not st.session_state.authenticated:
        ui.display_login_form()
    else:
        ui.display_sidebar()

        if st.session_state.menu_choice == "Главная страница":
            ui.display_home_page()
        
        elif st.session_state.menu_choice == "Ведение пользователей":
            ui.display_user_management()
            
        elif st.session_state.menu_choice == "Ведение ролей":
            ui.display_role_management()
            
        elif st.session_state.menu_choice == "Назначение ролей":
            ui.display_role_assignment()
        elif st.session_state.menu_choice == "Ведение организаций":
            ui.display_organization_management()
        elif st.session_state.menu_choice == "Ведение исполнителей":
            ui.display_executor_management()
        elif st.session_state.menu_choice == "Ведение руководителей проекта":
            ui.display_project_manager_management()
        elif st.session_state.menu_choice == "Формирование отчета":
            ui.display_report_form()
        elif st.session_state.menu_choice == "Назначение полномочий":
            ui.display_role_permissions_management()
        elif st.session_state.menu_choice == "Ведение должностей":
            ui.display_position_management()
        elif st.session_state.menu_choice == "Ведение договоров":
            ui.display_contract_management()

if __name__ == "__main__":
    main()
