import sqlite3
import json
import os

DB_NAME = "menu.db" # Default name, can be overridden

def init_db(menu_data_path="menu_data/menu.json", db_path=None):
    if db_path is None:
        db_path = DB_NAME # Use default if not provided

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id TEXT PRIMARY KEY,
            category_id INTEGER,
            name TEXT,
            price REAL,
            description TEXT,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS item_options (
            item_id TEXT,
            option_type TEXT,
            option_value TEXT,
            PRIMARY KEY (item_id, option_type, option_value),
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS item_sides (
            item_id TEXT,
            side_name TEXT,
            is_default INTEGER, -- 1 for default, 0 for available
            PRIMARY KEY (item_id, side_name),
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    ''')

    # Load data from JSON
    with open(menu_data_path, 'r') as f:
        menu = json.load(f)

    for category in menu['categories']:
        cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (category['name'],))
        category_id = cursor.execute("SELECT id FROM categories WHERE name = ?", (category['name'],)).fetchone()[0]

        for item in category['items']:
            cursor.execute("INSERT OR IGNORE INTO items (id, category_id, name, price, description) VALUES (?, ?, ?, ?, ?)",
                           (item['id'], category_id, item['name'], item['price'], item.get('description', '')))

            for option_type, values in item.get('options', {}).items():
                for value in values:
                    cursor.execute("INSERT OR IGNORE INTO item_options (item_id, option_type, option_value) VALUES (?, ?, ?)",
                                   (item['id'], option_type, value))

            for side in item.get('default_sides', []):
                cursor.execute("INSERT OR REPLACE INTO item_sides (item_id, side_name, is_default) VALUES (?, ?, ?)",
                               (item['id'], side, 1))
            for side in item.get('available_sides', []):
                # Ensure available sides are added, but not marked as default if they are not
                if side not in item.get('default_sides', []):
                    cursor.execute("INSERT OR REPLACE INTO item_sides (item_id, side_name, is_default) VALUES (?, ?, ?)",
                                   (item['id'], side, 0))

    conn.commit()
    conn.close()

def get_menu_data(db_path=None):
    if db_path is None:
        db_path = DB_NAME

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row # Return rows as dict-like objects
    cursor = conn.cursor()

    menu = {"categories": []}
    categories = cursor.execute("SELECT id, name FROM categories").fetchall()

    for cat_row in categories:
        category = {"name": cat_row['name'], "items": []}
        items = cursor.execute("SELECT id, name, price, description FROM items WHERE category_id = ?", (cat_row['id'],)).fetchall()

        for item_row in items:
            item = {
                "id": item_row['id'],
                "name": item_row['name'],
                "price": item_row['price'],
                "description": item_row['description'],
                "options": {},
                "default_sides": [],
                "available_sides": []
            }

            options = cursor.execute("SELECT option_type, option_value FROM item_options WHERE item_id = ?", (item_row['id'],)).fetchall()
            for opt_row in options:
                item['options'].setdefault(opt_row['option_type'], []).append(opt_row['option_value'])

            sides = cursor.execute("SELECT side_name, is_default FROM item_sides WHERE item_id = ?", (item_row['id'],)).fetchall()
            for side_row in sides:
                if side_row['is_default']:
                    item['default_sides'].append(side_row['side_name'])
                item['available_sides'].append(side_row['side_name'])

            category['items'].append(item)
        menu['categories'].append(category)

    conn.close()
    return menu

if __name__ == "__main__":
    # This part runs during Docker build to initialize the DB
    # The Dockerfile handles calling this with the correct paths
    pass
