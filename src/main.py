import sqlite3
import json
import csv
import yaml
import xml.etree.ElementTree as ET

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

    # Добавляем тестовые данные только один раз
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


def login(cursor):
    print("=== Авторизация ===")
    username = input("Введите имя пользователя: ")
    password = input("Введите пароль: ")

    cursor.execute("SELECT * FROM User WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    if user:
        print(f"Добро пожаловать, {username}!")
        return user[0]  # user_id
    else:
        print("Неверное имя пользователя или пароль.")
        return None


def search_parcel(cursor):
    print("\n=== Поиск посылки ===")
    choice = input("Искать по (1) ID посылки или (2) имени получателя? ")

    if choice == "1":
        parcel_id = input("Введите ID посылки: ")
        cursor.execute("""
        SELECT d.parcel_id, u.username, a.username, d.recipient_name, d.status, d.created_at,
               p.weight_kg, p.description, p.parcel_type,
               n.message, n.sent_at
        FROM Delivery d
        JOIN User u ON d.user_id = u.user_id
        JOIN Administrator a ON d.admin_id = a.admin_id
        JOIN Parcel p ON d.parcel_id = p.parcel_id
        LEFT JOIN Notification n ON d.parcel_id = n.delivery_id
        WHERE d.parcel_id=?
        """, (parcel_id,))
    else:
        recipient = input("Введите имя получателя: ")
        cursor.execute("""
        SELECT d.parcel_id, u.username, a.username, d.recipient_name, d.status, d.created_at,
               p.weight_kg, p.description, p.parcel_type,
               n.message, n.sent_at
        FROM Delivery d
        JOIN User u ON d.user_id = u.user_id
        JOIN Administrator a ON d.admin_id = a.admin_id
        JOIN Parcel p ON d.parcel_id = p.parcel_id
        LEFT JOIN Notification n ON d.parcel_id = n.delivery_id
        WHERE d.recipient_name LIKE ?
        """, (f"%{recipient}%",))

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


def export_data(cursor):
    cursor.execute("""
    SELECT d.parcel_id, u.username, a.username, d.recipient_name, d.status, d.created_at,
           p.weight_kg, p.description, p.parcel_type
    FROM Delivery d
    JOIN User u ON d.user_id = u.user_id
    JOIN Administrator a ON d.admin_id = a.admin_id
    JOIN Parcel p ON d.parcel_id = p.parcel_id
    """)
    rows = cursor.fetchall()

    # CSV
    with open("parcels.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["parcel_id", "user", "admin", "recipient", "status", "created_at",
                         "weight_kg", "description", "parcel_type"])
        writer.writerows(rows)

    # JSON
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

    # XML
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

    # YAML
    with open("parcels.yaml", "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)


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

    cursor.execute("INSERT INTO Parcel VALUES (?, ?, ?, ?)", (parcel_id, weight, description, parcel_type))
    cursor.execute("INSERT INTO Delivery VALUES (?, ?, ?, ?, ?, ?)",
                   (parcel_id, user_id, admin_id, recipient_name, status, created_at))

    conn.commit()
    print("Посылка успешно добавлена и сохранена в базе.")

    # Экспортируем данные во все форматы
    export_data(cursor)
    print("Данные обновлены в файлах: delivery.db, parcels.csv, parcels.json, parcels.xml, parcels.yaml")


def main():
    DB_NAME = "delivery.db"
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    init_db(cursor)
    conn.commit()

    user_id = login(cursor)
    if user_id:
        while True:
            print("\nВыберите действие:")
            print("1 — Поиск посылки")
            print("2 — Добавить новую посылку")
            print("0 — Выход")
            action = input("Ваш выбор: ")

            if action == "1":
                search_parcel(cursor)
            elif action == "2":
                add_parcel(cursor, conn, user_id)
            elif action == "0":
                break
            else:
                print("Неверный выбор. Попробуйте снова.")

    conn.close()


if __name__ == "__main__":
    main()