import os
import sqlite3
import json
import csv
import yaml
import xml.etree.ElementTree as ET

def main():
    DB_NAME = "delivery.db"
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Создание таблиц
    cursor.executescript("""
    DROP TABLE IF EXISTS Notification;
    DROP TABLE IF EXISTS Delivery;
    DROP TABLE IF EXISTS Parcel;
    DROP TABLE IF EXISTS Administrator;
    DROP TABLE IF EXISTS User;

    CREATE TABLE User (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL
    );

    CREATE TABLE Administrator (
        admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL
    );

    CREATE TABLE Parcel (
        parcel_id INTEGER PRIMARY KEY AUTOINCREMENT,
        weight_kg REAL,
        description TEXT,
        parcel_type TEXT
    );

    CREATE TABLE Delivery (
        delivery_id INTEGER PRIMARY KEY AUTOINCREMENT,
        parcel_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        admin_id INTEGER NOT NULL,
        recipient_name TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(parcel_id) REFERENCES Parcel(parcel_id),
        FOREIGN KEY(user_id) REFERENCES User(user_id),
        FOREIGN KEY(admin_id) REFERENCES Administrator(admin_id)
    );

    CREATE TABLE Notification (
        notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
        delivery_id INTEGER UNIQUE NOT NULL,
        message TEXT,
        sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(delivery_id) REFERENCES Delivery(delivery_id)
    );
    """)

    # Тестовые данные
    cursor.execute("INSERT INTO User (username, password) VALUES ('alex', 'pass123')")
    cursor.execute("INSERT INTO Administrator (username, password) VALUES ('admin1', 'adminpass')")
    cursor.execute("INSERT INTO Parcel (weight_kg, description, parcel_type) VALUES (2.5, 'Документы в конверте', 'Документы')")
    cursor.execute("""
        INSERT INTO Delivery (parcel_id, user_id, admin_id, recipient_name, status)
        VALUES (1, 1, 1, 'Иван Петров', 'Создана')
    """)
    cursor.execute("""
        INSERT INTO Notification (delivery_id, message)
        VALUES (1, 'Посылка создана и ожидает обработки')
    """)

    conn.commit()

    # Извлечение данных
    cursor.execute("""
    SELECT d.delivery_id, u.username, a.username, d.recipient_name, d.status, d.created_at,
           p.weight_kg, p.description, p.parcel_type,
           n.message, n.sent_at
    FROM Delivery d
    JOIN User u ON d.user_id = u.user_id
    JOIN Administrator a ON d.admin_id = a.admin_id
    JOIN Parcel p ON d.parcel_id = p.parcel_id
    JOIN Notification n ON d.delivery_id = n.delivery_id
    """)
    rows = cursor.fetchall()

    deliveries = []
    for row in rows:
        deliveries.append({
            "delivery_id": row[0],
            "sender": row[1],
            "admin": row[2],
            "recipient_name": row[3],
            "status": row[4],
            "created_at": row[5],
            "parcel": {
                "weight_kg": row[6],
                "description": row[7],
                "parcel_type": row[8]
            },
            "notification": {
                "message": row[9],
                "sent_at": row[10]
            }
        })

    os.makedirs("out", exist_ok=True)

    # JSON
    with open("out/delivery.json", "w", encoding="utf-8") as f:
        json.dump(deliveries, f, ensure_ascii=False, indent=2)

    # CSV
    with open("out/delivery.csv", "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "delivery_id", "sender", "admin", "recipient_name", "status", "created_at",
            "weight_kg", "description", "parcel_type", "message", "sent_at"
        ])
        writer.writeheader()
        for d in deliveries:
            writer.writerow({
                "delivery_id": d["delivery_id"],
                "sender": d["sender"],
                "admin": d["admin"],
                "recipient_name": d["recipient_name"],
                "status": d["status"],
                "created_at": d["created_at"],
                "weight_kg": d["parcel"]["weight_kg"],
                "description": d["parcel"]["description"],
                "parcel_type": d["parcel"]["parcel_type"],
                "message": d["notification"]["message"],
                "sent_at": d["notification"]["sent_at"]
            })

    # XML
    root = ET.Element("deliveries")
    for d in deliveries:
        delivery_elem = ET.SubElement(root, "delivery")
        for key in ["delivery_id", "sender", "admin", "recipient_name", "status", "created_at"]:
            ET.SubElement(delivery_elem, key).text = str(d[key])
        parcel_elem = ET.SubElement(delivery_elem, "parcel")
        for k, v in d["parcel"].items():
            ET.SubElement(parcel_elem, k).text = str(v)
        notif_elem = ET.SubElement(delivery_elem, "notification")
        for k, v in d["notification"].items():
            ET.SubElement(notif_elem, k).text = str(v)

    tree = ET.ElementTree(root)
    tree.write("out/delivery.xml", encoding="utf-8", xml_declaration=True)

    # YAML
    with open("out/delivery.yaml", "w", encoding="utf-8") as f:
        yaml.dump(deliveries, f, allow_unicode=True, sort_keys=False)

if __name__ == "__main__":
    main()