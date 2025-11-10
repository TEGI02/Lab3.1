import os
import sqlite3
import json
import csv
import xml.etree.ElementTree as ET

def main():
    #  Подключение к бд
    DB_NAME = "students.db"
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Создание таблиц
    cursor.executescript("""
    DROP TABLE IF EXISTS address;
    DROP TABLE IF EXISTS student;
    
    CREATE TABLE address (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT NOT NULL,
        street TEXT NOT NULL
    );
    
    CREATE TABLE student (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        Student BOOLEAN NOT NULL,
        address_id INTEGER,
        FOREIGN KEY(address_id) REFERENCES address(id)
    );
    """)
    
    # Добавление тестовых данных
    addresses = [
        ("Нижний Новгород", "ул. Карла Маркса, 52"),
        ("Нижний Новгород", "ул. Карла Маркса, 12"),
    ]
    cursor.executemany("INSERT INTO address (city, street) VALUES (?, ?)", addresses)
    
    students = [
        ("Илья", 19, True, 1),
        ("Миша", 18, False, 2),
    ]
    cursor.executemany("INSERT INTO student (name, age, Student, address_id) VALUES (?, ?, ?, ?)", students)
    
    conn.commit()
    
    # Извлечение данных
    cursor.execute("""
    SELECT s.id, s.name, s.age, s.Student, a.city, a.street
    FROM student s
    LEFT JOIN address a ON s.address_id = a.id
    """)
    rows = cursor.fetchall()
    
    data = []
    for row in rows:
        data.append({
            "id": row[0],
            "name": row[1],
            "age": row[2],
            "Student": bool(row[3]),
            "address": {"city": row[4], "street": row[5]}
        })

    os.makedirs("out", exist_ok=True)
    
    # JSON
    with open("out/data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    #  CSV
    with open("out/data.csv", "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "name", "age", "Student", "city", "street"])
        writer.writeheader()
        for d in data:
            writer.writerow({
                "id": d["id"],
                "name": d["name"],
                "age": d["age"],
                "Student": d["Student"],
                "city": d["address"]["city"],
                "street": d["address"]["street"]
            })
    
    # XML
    root = ET.Element("students")
    for d in data:
        student_elem = ET.SubElement(root, "student")
        for key in ["id", "name", "age", "Student"]:
            ET.SubElement(student_elem, key).text = str(d[key])
        addr_elem = ET.SubElement(student_elem, "address")
        ET.SubElement(addr_elem, "city").text = d["address"]["city"]
        ET.SubElement(addr_elem, "street").text = d["address"]["street"]
    
    tree = ET.ElementTree(root)
    tree.write("out/data.xml", encoding="utf-8", xml_declaration=True)
    
    # YAML 
    with open("out/data.yaml", "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

if __name__ == "__main__":
    main()