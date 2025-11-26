import sqlite3
import json
import csv
import yaml
import xml.etree.ElementTree as ET
import os

# ---------------- Инициализация базы ----------------
def init_db(cursor):
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS User (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        password TEXT
    );
    CREATE TABLE IF NOT EXISTS Administrator (
        admin_id INTEGER PRIMARY KEY,
        username TEXT,
        password TEXT
    );
    CREATE TABLE IF NOT EXISTS Parcel (
        parcel_id INTEGER PRIMARY KEY,
        weight_kg REAL,
        description TEXT,
        parcel_type TEXT
    );
    CREATE TABLE IF NOT EXISTS Delivery (
        parcel_id INTEGER PRIMARY KEY,
        user_id INTEGER,
        admin_id INTEGER,
        recipient_name TEXT,
        status TEXT,
        created_at TEXT,
        FOREIGN KEY(user_id) REFERENCES User(user_id),
        FOREIGN KEY(admin_id) REFERENCES Administrator(admin_id)
    );
    CREATE TABLE IF NOT EXISTS Notification (
        notification_id INTEGER PRIMARY KEY,
        delivery_id INTEGER,
        message TEXT,
        sent_at TEXT,
        FOREIGN KEY(delivery_id) REFERENCES Delivery(parcel_id)
    );
    """)

    # Начальные данные 
    cursor.execute("SELECT COUNT(*) FROM User")
    if cursor.fetchone()[0] == 0:
        users = [
            (1, "ivan", "pass123"),
            (2, "olga", "secure456")
        ]
        admins = [
            (1, "admin1", "adminpass"),
            (2, "admin2", "adminsecure")
        ]
        parcels = [
            (1, 2.5, "Books", "Standard"),
            (2, 1.2, "Electronics", "Express")
        ]
        deliveries = [
            (1, 1, 1, "Sergey Petrov", "In Transit", "2025-11-10"),
            (2, 2, 2, "Anna Ivanova", "Delivered", "2025-11-09")
        ]
        notifications = [
            (1, 1, "Your parcel is on the way", "2025-11-10 10:00"),
            (2, 2, "Your parcel has been delivered", "2025-11-09 15:30")
        ]

        cursor.executemany("INSERT INTO User VALUES (?, ?, ?)", users)
        cursor.executemany("INSERT INTO Administrator VALUES (?, ?, ?)", admins)
        cursor.executemany("INSERT INTO Parcel VALUES (?, ?, ?, ?)", parcels)
        cursor.executemany("INSERT INTO Delivery VALUES (?, ?, ?, ?, ?, ?)", deliveries)
        cursor.executemany("INSERT INTO Notification VALUES (?, ?, ?, ?)", notifications)

# ---------------- Экспорт ----------------
def export_users(cursor):
    cursor.execute("SELECT user_id, username, password FROM User")
    users = cursor.fetchall()

    with open("users.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["user_id", "username", "password"])
        writer.writerows(users)

    data = [{"user_id": u[0], "username": u[1], "password": u[2]} for u in users]
    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    root = ET.Element("users")
    for u in users:
        user_elem = ET.SubElement(root, "user", id=str(u[0]))
        ET.SubElement(user_elem, "username").text = u[1]
        ET.SubElement(user_elem, "password").text = u[2]
    tree = ET.ElementTree(root)
    tree.write("users.xml", encoding="utf-8", xml_declaration=True)

    with open("users.yaml", "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

def export_parcels(cursor):
    cursor.execute("""
    SELECT d.parcel_id, u.username, a.username, d.recipient_name, d.status, d.created_at,
           p.weight_kg, p.description, p.parcel_type
    FROM Delivery d
    JOIN User u ON d.user_id = u.user_id
    JOIN Administrator a ON d.admin_id = a.admin_id
    JOIN Parcel p ON d.parcel_id = p.parcel_id
    """)
    rows = cursor.fetchall()

    with open("parcels.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["parcel_id", "user", "admin", "recipient", "status", "created_at",
                         "weight_kg", "description", "parcel_type"])
        writer.writerows(rows)

    data = []
    for r in rows:
        data.append({
            "parcel_id": r[0],
            "user": r[1],
            "admin": r[2],
            "recipient": r[3],
            "status": r[4],
            "created_at": r[5],
            "weight_kg": r[6],
            "description": r[7],
            "parcel_type": r[8]
        })
    with open("parcels.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    root = ET.Element("parcels")
    for r in rows:
        parcel = ET.SubElement(root, "parcel", id=str(r[0]))
        ET.SubElement(parcel, "user").text = r[1]
        ET.SubElement(parcel, "admin").text = r[2]
        ET.SubElement(parcel, "recipient").text = r[3]
        ET.SubElement(parcel, "status").text = r[4]
        ET.SubElement(parcel, "created_at").text = r[5]
        ET.SubElement(parcel, "weight_kg").text = str(r[6])
        ET.SubElement(parcel, "description").text = r[7]
        ET.SubElement(parcel, "parcel_type").text = r[8]
    tree = ET.ElementTree(root)
    tree.write("parcels.xml", encoding="utf-8", xml_declaration=True)

    with open("parcels.yaml", "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

# ---------------- Авторизация и регистрация ----------------
def login(cursor, conn):
    print("=== Авторизация ===")
    username = input("Введите имя пользователя/администратора: ")
    password = input("Введите пароль: ")

    cursor.execute("SELECT * FROM User WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    if user:
        print(f"Добро пожаловать, пользователь {username}!")
        return ("user", user[0])

    cursor.execute("SELECT * FROM Administrator WHERE username=? AND password=?", (username, password))
    admin = cursor.fetchone()
    if admin:
        print(f"Добро пожаловать, администратор {username}!")
        return ("admin", admin[0])

    print("Пользователь/администратор не найден.")
    choice = input("Хотите зарегистрироваться? (y/n): ")
    if choice.lower() == "y":
        role = input("Введите роль (user/admin): ").strip().lower()
        if role == "user":
            cursor.execute("SELECT COALESCE(MAX(user_id),0)+1 FROM User")
            new_id = cursor.fetchone()[0]
            cursor.execute("INSERT INTO User VALUES (?, ?, ?)", (new_id, username, password))
            conn.commit()
            print(f"Пользователь {username} успешно зарегистрирован!")
            export_users(cursor)
            return ("user", new_id)
        elif role == "admin":
            cursor.execute("SELECT COALESCE(MAX(admin_id),0)+1 FROM Administrator")
            new_id = cursor.fetchone()[0]
            cursor.execute("INSERT INTO Administrator VALUES (?, ?, ?)", (new_id, username, password))
            conn.commit()
            print(f"Администратор {username} успешно зарегистрирован!")
            return ("admin", new_id)
    return None

# ---------------- Операции ----------------
def search_parcel(cursor):
    print("\n=== Поиск посылки ===")
    parcel_id = input("Введите ID посылки: ")
    cursor.execute("""
    SELECT d.parcel_id, u.username, a.username, d.recipient_name, d.status, d.created_at,
           p.weight_kg, p.description, p.parcel_type, n.message, n.sent_at
    FROM Delivery d
    JOIN User u ON d.user_id = u.user_id
    JOIN Administrator a ON d.admin_id = a.admin_id
    JOIN Parcel p ON d.parcel_id = p.parcel_id
    LEFT JOIN Notification n ON d.parcel_id = n.delivery_id
    WHERE d.parcel_id=?
    """, (parcel_id,))
    row = cursor.fetchone()
    if row:
        print("\n--- Информация о посылке ---")
        print(f"ID: {row[0]}")
        print(f"Пользователь: {row[1]}")
        print(f"Администратор: {row[2]}")
        print(f"Получатель: {row[3]}")
        print(f"Статус: {row[4]}")
        print(f"Дата создания: {row[5]}")
        print(f"Вес: {row[6]} кг")
        print(f"Описание: {row[7]}")
        print(f"Тип: {row[8]}")
        if row[9]:
            print(f"Уведомление: {row[9]} (в {row[10]})")
    else:
        print("Посылка не найдена.")

def add_parcel(cursor, conn, user_id):
    print("\n=== Добавление новой посылки ===")
    parcel_id = int(input("Введите ID посылки: "))
    weight = float(input("Введите вес (кг): "))
    description = input("Введите описание: ")
    parcel_type = input("Введите тип (Standard/Express): ")
    recipient_name = input("Введите имя получателя: ")
    status = input("Введите статус (например, In Transit): ")
    created_at = input("Введите дату создания (ГГГГ-ММ-ДД): ")
    admin_id = int(input("Введите ID администратора: "))

    cursor.execute("SELECT COUNT(*) FROM Parcel WHERE parcel_id=?", (parcel_id,))
    if cursor.fetchone()[0] > 0:
        print(f"Ошибка: посылка с ID {parcel_id} уже существует.")
        return

    cursor.execute("INSERT INTO Parcel VALUES (?, ?, ?, ?)", (parcel_id, weight, description, parcel_type))
    cursor.execute("INSERT INTO Delivery VALUES (?, ?, ?, ?, ?, ?)",
                   (parcel_id, user_id, admin_id, recipient_name, status, created_at))
    conn.commit()
    print("Посылка успешно добавлена и сохранена в базе.")
    export_parcels(cursor)

def update_status(cursor, conn):
    print("\n=== Изменение статуса посылки (админ) ===")
    parcel_id = input("Введите ID посылки: ")

    cursor.execute("SELECT COUNT(*) FROM Delivery WHERE parcel_id=?", (parcel_id,))
    if cursor.fetchone()[0] == 0:
        print(f"Ошибка: посылка с ID {parcel_id} не существует.")
        return

    new_status = input("Введите новый статус: ")
    cursor.execute("UPDATE Delivery SET status=? WHERE parcel_id=?", (new_status, parcel_id))
    conn.commit()
    print("Статус успешно обновлён.")
    export_parcels(cursor)

def delete_user(cursor, conn):
    print("\n=== Удаление пользователя (админ) ===")
    user_id = input("Введите ID пользователя для удаления: ")

    # Проверка существования пользователя
    cursor.execute("SELECT COUNT(*) FROM User WHERE user_id=?", (user_id,))
    if cursor.fetchone()[0] == 0:
        print(f"Ошибка: пользователь с ID {user_id} не существует.")
        return

    # Проверка наличия связанных доставок
    cursor.execute("SELECT COUNT(*) FROM Delivery WHERE user_id=?", (user_id,))
    cnt = cursor.fetchone()[0]
    if cnt > 0:
        confirm = input(f"У пользователя есть {cnt} доставок. Удалить пользователя и его доставки? (y/n): ")
        if confirm.lower() != "y":
            print("Отмена удаления.")
            return
        # Удаляем доставки и уведомления
        cursor.execute("SELECT parcel_id FROM Delivery WHERE user_id=?", (user_id,))
        parcel_ids = [row[0] for row in cursor.fetchall()]
        for pid in parcel_ids:
            cursor.execute("DELETE FROM Notification WHERE delivery_id=?", (pid,))
            cursor.execute("DELETE FROM Delivery WHERE parcel_id=?", (pid,))
            cursor.execute("DELETE FROM Parcel WHERE parcel_id=?", (pid,))

    cursor.execute("DELETE FROM User WHERE user_id=?", (user_id,))
    conn.commit()
    print(f"Пользователь с ID {user_id} удалён.")
    export_users(cursor)
    export_parcels(cursor)

def delete_parcel(cursor, conn):
    print("\n=== Удаление посылки (админ) ===")
    parcel_id = input("Введите ID посылки для удаления: ")

    # Проверка существования посылки
    cursor.execute("SELECT COUNT(*) FROM Parcel WHERE parcel_id=?", (parcel_id,))
    if cursor.fetchone()[0] == 0:
        print(f"Ошибка: посылка с ID {parcel_id} не существует.")
        return

    # Удаление 
    cursor.execute("DELETE FROM Notification WHERE delivery_id=?", (parcel_id,))
    cursor.execute("DELETE FROM Delivery WHERE parcel_id=?", (parcel_id,))
    cursor.execute("DELETE FROM Parcel WHERE parcel_id=?", (parcel_id,))
    conn.commit()
    print(f"Посылка с ID {parcel_id} удалена.")
    export_parcels(cursor)

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

# ---------------- Главная функция ----------------
def main():
    DB_NAME = "delivery.db"
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    init_db(cursor)
    conn.commit()

    # Первичная выгрузка
    export_users(cursor)
    export_parcels(cursor)

    login_result = login(cursor, conn)
    if login_result:
        role, user_or_admin_id = login_result
        while True:
            print("\nВыберите действие:")
            print("1 — Поиск посылки")
            if role == "user":
                print("2 — Добавить новую посылку")
            if role == "admin":
                print("2 — Изменить статус посылки")
                print("3 — Удалить пользователя")
                print("4 — Удалить посылку")
            print("0 — Выход")
            action = input("Ваш выбор: ")

            if action == "1":
                clear_screen()
                search_parcel(cursor)
            elif action == "2" and role == "user":
                clear_screen()
                add_parcel(cursor, conn, user_or_admin_id)
            elif action == "2" and role == "admin":
                clear_screen()
                update_status(cursor, conn)
            elif action == "3" and role == "admin":
                clear_screen()
                delete_user(cursor, conn)
            elif action == "4" and role == "admin":
                clear_screen()
                delete_parcel(cursor, conn)
            elif action == "0":
                break
            else:
                clear_screen()
                print("Неверный выбор. Попробуйте снова.")
    conn.close()

if __name__ == "__main__":
    main()


