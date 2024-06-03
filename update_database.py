import sqlite3

DATABASE = 'recipe_app.db'

def update_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Drop the existing recipes table
    cursor.execute('DROP TABLE IF EXISTS recipes')
    
    # Recreate the recipes table with the image column
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            ingredients TEXT NOT NULL,
            instructions TEXT NOT NULL,
            image TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    update_db()
