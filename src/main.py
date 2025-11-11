import os
import sqlite3
import json
import csv
import xml.etree.ElementTree as ET

def main():
    DB_NAME = "delivery.db"
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.executescript("""
    DROP TABLE IF EXISTS Notification;
    DROP TABLE IF EXISTS Delivery;
    DROP TABLE IF EXISTS Parcel;
    DROP TABLE IF EXISTS Administrator;
    DROP TABLE IF EXISTS User;

    CREATE TABLE User (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        password TEXT
    );

    CREATE TABLE Administrator (
        admin_id INTEGER PRIMARY KEY,
        username TEXT,
        password TEXT
    );

    CREATE TABLE Parcel (
        parcel_id INTEGER PRIMARY KEY,
        weight_kg REAL,
        description TEXT,
        parcel_type TEXT
    );

    CREATE TABLE Delivery (
        parcel_id INTEGER PRIMARY KEY,
        user_id INTEGER,
        admin_id INTEGER,
        recipient_name TEXT,
        status TEXT,
        created_at TEXT,
        FOREIGN KEY(user_id) REFERENCES User(user_id),
        FOREIGN KEY(admin_id) REFERENCES Administrator(admin_id)
    );

    CREATE TABLE Notification (
        notification_id INTEGER PRIMARY KEY,
        delivery_id INTEGER,
        message TEXT,
        sent_at TEXT,
        FOREIGN KEY(delivery_id) REFERENCES Delivery(parcel_id)
    );
    """)

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

    conn.commit()

    cursor.execute("""
    SELECT d.parcel_id, u.username, a.username, d.recipient_name, d.status, d.created_at,
           p.weight_kg, p.description, p.parcel_type,
           n.message, n.sent_at
    FROM Delivery d
    JOIN User u ON d.user_id = u.user_id
    JOIN Administrator a ON d.admin_id = a.admin_id
    JOIN Parcel p ON d.parcel_id = p.parcel_id
    LEFT JOIN Notification n ON d.parcel_id = n.delivery_id
    """)
    rows = cursor.fetchall()

    data = []
    for row in rows:
        data.append({
            "parcel_id": row[0],
            "user": row[1],
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
            } if row[9] else None
        })

    os.makedirs("out", exist_ok=True)

    with open("out/delivery.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    with open("out/delivery.csv", "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "parcel_id", "user", "admin", "recipient_name", "status", "created_at",
            "weight_kg", "description", "parcel_type", "message", "sent_at"
        ])
        writer.writeheader()
        for d in data:
            writer.writerow({
                "parcel_id": d["parcel_id"],
                "user": d["user"],
                "admin": d["admin"],
                "recipient_name": d["recipient_name"],
                "status": d["status"],
                "created_at": d["created_at"],
                "weight_kg": d["parcel"]["weight_kg"],
                "description": d["parcel"]["description"],
                "parcel_type": d["parcel"]["parcel_type"],
                "message": d["notification"]["message"] if d["notification"] else "",
                "sent_at": d["notification"]["sent_at"] if d["notification"] else ""
            })

    root = ET.Element("deliveries")
    for d in data:
        delivery_elem = ET.SubElement(root, "delivery")
        for key in ["parcel_id", "user", "admin", "recipient_name", "status", "created_at"]:
            ET.SubElement(delivery_elem, key).text = str(d[key])
        parcel_elem = ET.SubElement(delivery_elem, "parcel")
        for k, v in d["parcel"].items():
            ET.SubElement(parcel_elem, k).text = str(v)
        if d["notification"]:
            notif_elem = ET.SubElement(delivery_elem, "notification")
            ET.SubElement(notif_elem, "message").text = d["notification"]["message"]
            ET.SubElement(notif_elem, "sent_at").text = d["notification"]["sent_at"]

    tree = ET.ElementTree(root)
    tree.write("out/delivery.xml", encoding="utf-8", xml_declaration=True)

    with open("out/delivery.yaml", "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

if __name__ == "__main__":
    main()
