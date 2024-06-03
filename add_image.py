import sqlite3

DATABASE = 'recipe_app.db'

def add_image_column():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Add the image column to the recipes table
    try:
        cursor.execute('ALTER TABLE recipes ADD COLUMN image TEXT')
    except sqlite3.OperationalError as e:
        # This error occurs if the column already exists, ignore it
        if 'duplicate column name' in str(e):
            pass
        else:
            raise e
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    add_image_column()
