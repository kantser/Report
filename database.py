import sqlite3
import bcrypt
import streamlit as st

def init_db():
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    
    # Создание таблицы пользователей
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  first_name TEXT,
                  last_name TEXT,
                  middle_name TEXT)''')
    
    # Создание таблицы ролей
    c.execute('''CREATE TABLE IF NOT EXISTS roles
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT UNIQUE NOT NULL)''')
    
    # Создание таблицы связей пользователей и ролей
    c.execute('''CREATE TABLE IF NOT EXISTS user_roles
                 (user_id INTEGER,
                  role_id INTEGER,
                  UNIQUE(user_id, role_id),
                  FOREIGN KEY (user_id) REFERENCES users (id),
                  FOREIGN KEY (role_id) REFERENCES roles (id))''')
    
    # Создание таблицы организаций
    c.execute('''CREATE TABLE IF NOT EXISTS organizations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT UNIQUE NOT NULL)''')
    
    # Создание таблицы исполнителей
    c.execute('''CREATE TABLE IF NOT EXISTS executors
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  first_name TEXT,
                  last_name TEXT,
                  middle_name TEXT,
                  position_id INTEGER REFERENCES positions(id))''')
    
    # Создание таблицы руководителей проекта
    c.execute('''CREATE TABLE IF NOT EXISTS project_managers
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  first_name TEXT,
                  last_name TEXT,
                  middle_name TEXT)''')
    
    # Создание таблицы отчетов
    c.execute("PRAGMA table_info(reports)")
    columns = [col[1] for col in c.fetchall()]
    
    # Проверяем, существует ли старая таблица reports или отсутствуют необходимые колонки
    required_columns = ["organization_id", "start_date", "end_date", "executor_id", "project_manager_id", "contract_id", "report_filename", 
                        "num_licenses", "control_list_json", "num_incidents_section1", "num_blocked_resources", 
                        "num_unidentified_carriers", "num_info_messages", "num_controlled_docs", "num_time_violations"]
    
    # Проверяем наличие всех требуемых колонок
    if not all(col in columns for col in required_columns):
        c.execute("DROP TABLE IF EXISTS reports")
        conn.commit()
        st.warning("База данных отчетов была сброшена из-за изменения структуры. Старые отчеты удалены.")

    c.execute('''CREATE TABLE IF NOT EXISTS reports
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  organization_id INTEGER NOT NULL,
                  start_date TEXT NOT NULL,
                  end_date TEXT NOT NULL,
                  executor_id INTEGER NOT NULL,
                  project_manager_id INTEGER NOT NULL,
                  contract_id INTEGER NOT NULL,
                  report_filename TEXT,
                  num_licenses INTEGER,
                  control_list_json TEXT,
                  num_incidents_section1 INTEGER,
                  num_blocked_resources INTEGER,
                  num_unidentified_carriers INTEGER,
                  num_info_messages INTEGER,
                  num_controlled_docs INTEGER,
                  num_time_violations INTEGER,
                  FOREIGN KEY (organization_id) REFERENCES organizations (id),
                  FOREIGN KEY (executor_id) REFERENCES executors (id),
                  FOREIGN KEY (project_manager_id) REFERENCES project_managers (id),
                  FOREIGN KEY (contract_id) REFERENCES contracts (id))''')
    
    # Создание таблицы разрешений для ролей
    c.execute('''CREATE TABLE IF NOT EXISTS role_permissions (
        role_id INTEGER,
        menu_item TEXT,
        allowed INTEGER DEFAULT 0,
        UNIQUE(role_id, menu_item),
        FOREIGN KEY (role_id) REFERENCES roles (id)
    )''')
    
    # Создание таблицы должностей
    c.execute('''CREATE TABLE IF NOT EXISTS positions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT UNIQUE NOT NULL)''')
    
    # Создание таблицы договоров
    c.execute('''CREATE TABLE IF NOT EXISTS contracts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  number TEXT NOT NULL,
                  date TEXT NOT NULL)''')
    
    # Миграция: добавление поля position_id в executors
    c.execute("PRAGMA table_info(executors)")
    columns = [col[1] for col in c.fetchall()]
    if "position_id" not in columns:
        c.execute("ALTER TABLE executors ADD COLUMN position_id INTEGER REFERENCES positions(id)")
    
    # Добавление ролей по умолчанию
    c.execute("INSERT OR IGNORE INTO roles (name) VALUES ('Администратор'), ('Пользователь')")
    
    # Добавление пользователя admin по умолчанию
    admin_password = bcrypt.hashpw('admin'.encode('utf-8'), bcrypt.gensalt())
    c.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
              ('admin', admin_password))
    
    # Назначение роли 'Администратор' пользователю 'admin'
    c.execute("SELECT id FROM users WHERE username = 'admin'")
    admin_user_id = c.fetchone()[0]
    c.execute("SELECT id FROM roles WHERE name = 'Администратор'")
    admin_role_id = c.fetchone()[0]
    c.execute("INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES (?, ?)", (admin_user_id, admin_role_id))
    
    # Получаем id роли 'Администратор'
    c.execute("SELECT id FROM roles WHERE name = 'Администратор'")
    admin_role_id = c.fetchone()[0]
    # Список всех пунктов меню
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
        'Выход'
    ]
    # Для администратора разрешить все
    for item in menu_items:
        c.execute("INSERT OR IGNORE INTO role_permissions (role_id, menu_item, allowed) VALUES (?, ?, 1)", (admin_role_id, item))
    
    # Получаем id роли 'Пользователь'
    c.execute("SELECT id FROM roles WHERE name = 'Пользователь'")
    user_role_id = c.fetchone()[0]

    # Для пользователя запретить все по умолчанию
    for item in menu_items:
        c.execute("INSERT OR IGNORE INTO role_permissions (role_id, menu_item, allowed) VALUES (?, ?, 0)", (user_role_id, item))
    
    conn.commit()
    conn.close()

def login(username, password):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("SELECT id, username, password FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    
    if user and bcrypt.checkpw(password.encode('utf-8'), user[2]):
        return user[1]  # Возвращаем username
    return None

# Функции для управления пользователями
def get_all_users():
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("SELECT id, username, first_name, last_name, middle_name FROM users")
    users = c.fetchall()
    conn.close()
    return users

def add_new_user(username, password, first_name=None, last_name=None, middle_name=None):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    try:
        c.execute("INSERT INTO users (username, password, first_name, last_name, middle_name) VALUES (?, ?, ?, ?, ?)",
                  (username, hashed_password, first_name, last_name, middle_name))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Имя пользователя уже существует
    finally:
        conn.close()

def update_existing_user(user_id, username, password=None, first_name=None, last_name=None, middle_name=None):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    if password:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        c.execute("UPDATE users SET username = ?, password = ?, first_name = ?, last_name = ?, middle_name = ? WHERE id = ?",
                  (username, hashed_password, first_name, last_name, middle_name, user_id))
    else:
        c.execute("UPDATE users SET username = ?, first_name = ?, last_name = ?, middle_name = ? WHERE id = ?",
                  (username, first_name, last_name, middle_name, user_id))
    conn.commit()
    conn.close()
    return True

def delete_existing_user(user_id):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return True

# Функции для управления ролями
def get_all_roles():
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("SELECT id, name FROM roles")
    roles = c.fetchall()
    conn.close()
    return roles

def add_new_role(role_name):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO roles (name) VALUES (?)", (role_name,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Роль с таким именем уже существует
    finally:
        conn.close()

def delete_role(role_id):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("DELETE FROM roles WHERE id = ?", (role_id,))
    conn.commit()
    conn.close()
    return True

# Функции для управления назначением ролей
def get_user_roles(user_id):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("SELECT r.id, r.name FROM roles r INNER JOIN user_roles ur ON r.id = ur.role_id WHERE ur.user_id = ?", (user_id,))
    roles = c.fetchall()
    conn.close()
    return roles

def assign_role_to_user(user_id, role_id):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)", (user_id, role_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Роль уже назначена этому пользователю
    finally:
        conn.close()

def remove_role_from_user(user_id, role_id):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("DELETE FROM user_roles WHERE user_id = ? AND role_id = ?", (user_id, role_id))
    conn.commit()
    conn.close()
    return True

# Функции для управления организациями
def get_all_organizations():
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("SELECT id, name FROM organizations")
    organizations = c.fetchall()
    conn.close()
    return organizations

def add_organization(name):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO organizations (name) VALUES (?)", (name,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def update_organization(org_id, name):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    try:
        c.execute("UPDATE organizations SET name = ? WHERE id = ?", (name, org_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def delete_organization(org_id):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("DELETE FROM organizations WHERE id = ?", (org_id,))
    conn.commit()
    conn.close()
    return True

# Функции для управления исполнителями
def get_all_executors():
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("SELECT id, first_name, last_name, middle_name, position_id FROM executors")
    executors = c.fetchall()
    conn.close()
    return executors

def add_executor(first_name, last_name, middle_name, position_id=None):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("INSERT INTO executors (first_name, last_name, middle_name, position_id) VALUES (?, ?, ?, ?)",
              (first_name, last_name, middle_name, position_id))
    conn.commit()
    conn.close()
    return True

def update_executor(executor_id, first_name, last_name, middle_name, position_id=None):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("UPDATE executors SET first_name = ?, last_name = ?, middle_name = ?, position_id = ? WHERE id = ?",
              (first_name, last_name, middle_name, position_id, executor_id))
    conn.commit()
    conn.close()
    return True

def delete_executor(executor_id):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("DELETE FROM executors WHERE id = ?", (executor_id,))
    conn.commit()
    conn.close()
    return True

# Функции для управления руководителями проекта
def get_all_project_managers():
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("SELECT id, first_name, last_name, middle_name FROM project_managers")
    managers = c.fetchall()
    conn.close()
    return managers

def add_project_manager(first_name, last_name, middle_name):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()

    # Normalize empty string to None for consistent storage and lookup
    normalized_middle_name = middle_name if middle_name else None

    # Check for existing record
    if normalized_middle_name is None:
        c.execute("SELECT id FROM project_managers WHERE first_name = ? AND last_name = ? AND middle_name IS NULL",
                  (first_name, last_name))
    else:
        c.execute("SELECT id FROM project_managers WHERE first_name = ? AND last_name = ? AND middle_name = ?",
                  (first_name, last_name, normalized_middle_name))

    existing_pm = c.fetchone()
    if existing_pm:
        conn.close()
        return False # Руководитель проекта с таким ФИО уже существует

    # Insert the new project manager
    c.execute("INSERT INTO project_managers (first_name, last_name, middle_name) VALUES (?, ?, ?)",
              (first_name, last_name, normalized_middle_name))
    conn.commit()
    conn.close()
    return True

def update_project_manager(manager_id, first_name, last_name, middle_name):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()

    # Normalize empty string to None for consistent storage
    normalized_middle_name = middle_name if middle_name else None

    # Before updating, check for duplicates with other records
    # Exclude the current record being updated from the duplicate check
    if normalized_middle_name is None:
        c.execute("SELECT id FROM project_managers WHERE first_name = ? AND last_name = ? AND middle_name IS NULL AND id != ?",
                  (first_name, last_name, manager_id))
    else:
        c.execute("SELECT id FROM project_managers WHERE first_name = ? AND last_name = ? AND middle_name = ? AND id != ?",
                  (first_name, last_name, normalized_middle_name, manager_id))

    existing_duplicate_pm = c.fetchone()
    if existing_duplicate_pm:
        conn.close()
        return False # Руководитель проекта с таким ФИО уже существует у другой записи

    c.execute("UPDATE project_managers SET first_name = ?, last_name = ?, middle_name = ? WHERE id = ?",
              (first_name, last_name, normalized_middle_name, manager_id))
    conn.commit()
    conn.close()
    return True

def delete_project_manager(manager_id):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("DELETE FROM project_managers WHERE id = ?", (manager_id,))
    conn.commit()
    conn.close()
    return True

# Функции для управления отчетами
def add_report(organization_id, start_date, end_date, executor_id, project_manager_id, report_filename, contract_id):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("INSERT INTO reports (organization_id, start_date, end_date, executor_id, project_manager_id, report_filename, contract_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (organization_id, start_date, end_date, executor_id, project_manager_id, report_filename, contract_id))
    conn.commit()
    conn.close()

def add_full_report(organization_id, start_date, end_date, executor_id, project_manager_id, report_filename, contract_id,
                     num_licenses, control_list_json, num_incidents_section1, num_blocked_resources,
                     num_unidentified_carriers, num_info_messages, num_controlled_docs, num_time_violations):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("INSERT INTO reports (organization_id, start_date, end_date, executor_id, project_manager_id, report_filename, contract_id, num_licenses, control_list_json, num_incidents_section1, num_blocked_resources, num_unidentified_carriers, num_info_messages, num_controlled_docs, num_time_violations) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
              (organization_id, start_date, end_date, executor_id, project_manager_id, report_filename, contract_id,
               num_licenses, control_list_json, num_incidents_section1, num_blocked_resources,
               num_unidentified_carriers, num_info_messages, num_controlled_docs, num_time_violations))
    conn.commit()
    conn.close()

def get_report(report_id):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("SELECT id, organization_id, start_date, end_date, executor_id, project_manager_id, report_filename, contract_id, num_licenses, control_list_json, num_incidents_section1, num_blocked_resources, num_unidentified_carriers, num_info_messages, num_controlled_docs, num_time_violations FROM reports WHERE id = ?", (report_id,))
    report = c.fetchone()
    conn.close()
    return report

def get_all_reports():
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("""SELECT
        r.id,
        o.name,
        r.start_date,
        r.end_date,
        e.first_name,
        e.last_name,
        e.middle_name,
        pm.first_name,
        pm.last_name,
        pm.middle_name,
        r.report_filename,
        r.num_licenses,
        r.control_list_json,
        r.num_incidents_section1,
        r.num_blocked_resources,
        r.num_unidentified_carriers,
        r.num_info_messages,
        r.num_controlled_docs,
        r.num_time_violations
    FROM reports r
    JOIN organizations o ON r.organization_id = o.id
    JOIN executors e ON r.executor_id = e.id
    JOIN project_managers pm ON r.project_manager_id = pm.id""")
    reports = c.fetchall()
    conn.close()
    return reports

def delete_report(report_id):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("DELETE FROM reports WHERE id = ?", (report_id,))
    conn.commit()
    conn.close()
    return True

def get_organization_by_id(org_id):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("SELECT name FROM organizations WHERE id = ?", (org_id,))
    org = c.fetchone()
    conn.close()
    return org[0] if org else None

def get_executor_by_id(exec_id, include_position=True):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("SELECT e.first_name, e.last_name, e.middle_name, p.name FROM executors e LEFT JOIN positions p ON e.position_id = p.id WHERE e.id = ?", (exec_id,))
    row = c.fetchone()
    conn.close()
    if row:
        fio = f"{row[1]} {row[0]} {row[2] if row[2] else ''}".strip()
        if include_position and row[3]:
            return f"{fio}, {row[3]}"
        return fio
    return ""

def get_executor_position_by_id(exec_id):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("SELECT p.name FROM executors e JOIN positions p ON e.position_id = p.id WHERE e.id = ?", (exec_id,))
    position = c.fetchone()
    conn.close()
    return position[0] if position else ""

def get_project_manager_by_id(pm_id):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("SELECT first_name, last_name, middle_name FROM project_managers WHERE id = ?", (pm_id,))
    pm = c.fetchone()
    conn.close()
    return f"{pm[1]} {pm[0]} {pm[2] if pm[2] else ''}".strip() if pm else None

def get_role_permissions(role_id):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("SELECT menu_item, allowed FROM role_permissions WHERE role_id = ?", (role_id,))
    permissions = c.fetchall()
    conn.close()
    return dict(permissions)

def set_role_permissions(role_id, permissions_dict):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    for menu_item, allowed in permissions_dict.items():
        c.execute("INSERT OR REPLACE INTO role_permissions (role_id, menu_item, allowed) VALUES (?, ?, ?)", (role_id, menu_item, int(allowed)))
    conn.commit()
    conn.close()

def get_allowed_menu_items_for_role(role_id):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("SELECT menu_item FROM role_permissions WHERE role_id = ? AND allowed = 1", (role_id,))
    items = [row[0] for row in c.fetchall()]
    conn.close()
    return items

def get_user_id_by_username(username):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

# CRUD для должностей

def get_all_positions():
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("SELECT id, name FROM positions")
    positions = c.fetchall()
    conn.close()
    return positions

def add_position(name):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO positions (name) VALUES (?)", (name,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def update_position(position_id, name):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("UPDATE positions SET name = ? WHERE id = ?", (name, position_id))
    conn.commit()
    conn.close()
    return True

def delete_position(position_id):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("DELETE FROM positions WHERE id = ?", (position_id,))
    conn.commit()
    conn.close()
    return True

# CRUD для договоров

def get_all_contracts():
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("SELECT id, number, date FROM contracts")
    contracts = c.fetchall()
    conn.close()
    return contracts

def add_contract(number, date):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("INSERT INTO contracts (number, date) VALUES (?, ?)", (number, date))
    conn.commit()
    conn.close()
    return True

def update_contract(contract_id, number, date):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("UPDATE contracts SET number = ?, date = ? WHERE id = ?", (number, date, contract_id))
    conn.commit()
    conn.close()
    return True

def delete_contract(contract_id):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("DELETE FROM contracts WHERE id = ?", (contract_id,))
    conn.commit()
    conn.close()
    return True

def get_contract_by_id(contract_id):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("SELECT number, date FROM contracts WHERE id = ?", (contract_id,))
    contract = c.fetchone()
    conn.close()
    return contract if contract else None 