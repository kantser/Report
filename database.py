import sqlite3
import bcrypt
from pathlib import Path

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
                  middle_name TEXT)''')
    
    # Создание таблицы руководителей проекта
    c.execute('''CREATE TABLE IF NOT EXISTS project_managers
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  first_name TEXT,
                  last_name TEXT,
                  middle_name TEXT)''')
    
    # Создание таблицы отчетов
    # Проверяем, существует ли старая таблица reports с колонкой report_content
    c.execute("PRAGMA table_info(reports)")
    columns = [col[1] for col in c.fetchall()]
    if "report_content" in columns:
        c.execute("DROP TABLE reports")
        conn.commit()
        st.warning("База данных отчетов была сброшена из-за изменения структуры. Старые отчеты удалены.")

    c.execute('''CREATE TABLE IF NOT EXISTS reports
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  organization_id INTEGER NOT NULL,
                  start_date TEXT NOT NULL,
                  end_date TEXT NOT NULL,
                  executor_id INTEGER NOT NULL,
                  project_manager_id INTEGER NOT NULL,
                  report_filename TEXT,
                  FOREIGN KEY (organization_id) REFERENCES organizations (id),
                  FOREIGN KEY (executor_id) REFERENCES executors (id),
                  FOREIGN KEY (project_manager_id) REFERENCES project_managers (id))''')
    
    # Добавление ролей по умолчанию
    c.execute("INSERT OR IGNORE INTO roles (name) VALUES ('Администратор'), ('Пользователь')")
    
    # Добавление пользователя admin по умолчанию
    admin_password = bcrypt.hashpw('admin'.encode('utf-8'), bcrypt.gensalt())
    c.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
              ('admin', admin_password))
    
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
    c.execute("SELECT id, first_name, last_name, middle_name FROM executors")
    executors = c.fetchall()
    conn.close()
    return executors

def add_executor(first_name, last_name, middle_name):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("INSERT INTO executors (first_name, last_name, middle_name) VALUES (?, ?, ?)",
              (first_name, last_name, middle_name))
    conn.commit()
    conn.close()
    return True

def update_executor(executor_id, first_name, last_name, middle_name):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("UPDATE executors SET first_name = ?, last_name = ?, middle_name = ? WHERE id = ?",
              (first_name, last_name, middle_name, executor_id))
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
    c.execute("INSERT INTO project_managers (first_name, last_name, middle_name) VALUES (?, ?, ?)",
              (first_name, last_name, middle_name))
    conn.commit()
    conn.close()
    return True

def update_project_manager(manager_id, first_name, last_name, middle_name):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("UPDATE project_managers SET first_name = ?, last_name = ?, middle_name = ? WHERE id = ?",
              (first_name, last_name, middle_name, manager_id))
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
def add_report(organization_id, start_date, end_date, executor_id, project_manager_id, report_filename):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("INSERT INTO reports (organization_id, start_date, end_date, executor_id, project_manager_id, report_filename) VALUES (?, ?, ?, ?, ?, ?)",
              (organization_id, start_date, end_date, executor_id, project_manager_id, report_filename))
    conn.commit()
    conn.close()
    return True

def get_report(report_id):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("SELECT id, organization_id, start_date, end_date, executor_id, project_manager_id, report_filename FROM reports WHERE id = ?", (report_id,))
    report = c.fetchone()
    conn.close()
    return report

def get_all_reports():
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("SELECT r.id, o.name, r.start_date, r.end_date, e.first_name, e.last_name, e.middle_name, pm.first_name, pm.last_name, pm.middle_name, r.report_filename FROM reports r LEFT JOIN organizations o ON r.organization_id = o.id LEFT JOIN executors e ON r.executor_id = e.id LEFT JOIN project_managers pm ON r.project_manager_id = pm.id")
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

def get_executor_by_id(exec_id):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("SELECT first_name, last_name, middle_name FROM executors WHERE id = ?", (exec_id,))
    executor = c.fetchone()
    conn.close()
    return f"{executor[1]} {executor[0]} {executor[2] if executor[2] else ''}".strip() if executor else None

def get_project_manager_by_id(pm_id):
    conn = sqlite3.connect('report.db')
    c = conn.cursor()
    c.execute("SELECT first_name, last_name, middle_name FROM project_managers WHERE id = ?", (pm_id,))
    pm = c.fetchone()
    conn.close()
    return f"{pm[1]} {pm[0]} {pm[2] if pm[2] else ''}".strip() if pm else None 