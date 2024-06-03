import os
from flask import Flask, abort, render_template, request, redirect, url_for, flash, session, g
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from functools import wraps

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif','avif'}

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    db = sqlite3.connect('database.db')
    db.row_factory = sqlite3.Row
    return db

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        db = get_db()
        g.user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone() is not None:
            error = f'User {username} is already registered.'

        if error is None:
            db.execute(
                'INSERT INTO users (username, password) VALUES (?, ?)',
                (username, generate_password_hash(password))
            )
            db.commit()
            flash('You have successfully signed up! Please log in.')
            return redirect(url_for('login'))

        flash(error)
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if user and check_password_hash(user['password'], password):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/search', methods=['GET'])
@login_required
def search():
    query = request.args.get('query')
    db = get_db()
    if query:
        recipes = db.execute('SELECT * FROM recipes WHERE name LIKE ?', ('%' + query + '%',)).fetchall()
    else:
        recipes = db.execute('SELECT * FROM recipes').fetchall()
    return render_template('search.html', recipes=recipes)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        name = request.form['name']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']
        file = request.files['image']
        user_id = session.get('user_id')

        if not user_id:
            flash('User not logged in')
            return redirect(url_for('login'))

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = url_for('static', filename='uploads/' + filename)
        else:
            image_url = None

        db = get_db()
        db.execute('INSERT INTO recipes (name, ingredients, instructions, image_url, user_id) VALUES (?, ?, ?, ?, ?)',
                   (name, ingredients, instructions, image_url, user_id))
        db.commit()
        flash('Recipe uploaded successfully!')
        return redirect(url_for('dashboard'))
    
    return render_template('upload.html')

@app.route('/recipe/<int:recipe_id>')
def recipe_detail(recipe_id):
    conn = get_db()
    recipe = conn.execute('SELECT * FROM recipes WHERE id = ?', (recipe_id,)).fetchone()
    conn.close()
    if recipe is None:
        abort(404)
    return render_template('recipe_detail.html', recipe=recipe)


@app.route('/update_recipe/<int:recipe_id>', methods=['GET', 'POST'])
@login_required
def update_recipe(recipe_id):
    db = get_db()
    recipe = db.execute('SELECT * FROM recipes WHERE id = ?', (recipe_id,)).fetchone()
    user_id = session.get('user_id')

    if not user_id:
        flash('User not logged in')
        return redirect(url_for('login'))

    if recipe['user_id'] != user_id:
        flash('You do not have permission to update this recipe.')
        return redirect(url_for('your_recipes'))
    
    if request.method == 'POST':
        name = request.form['name']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']
        file = request.files['image']
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = url_for('static', filename='uploads/' + filename)
        else:
            image_url = recipe['image_url']

        db.execute('UPDATE recipes SET name = ?, ingredients = ?, instructions = ?, image_url = ? WHERE id = ?',
                   (name, ingredients, instructions, image_url, recipe_id))
        db.commit()
        flash('Recipe updated successfully!')
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))
    
    return render_template('update_recipe.html', recipe=recipe)

@app.route('/your_recipes')
@login_required
def your_recipes():
    user_id = session.get('user_id')
    db = get_db()
    recipes = db.execute('SELECT * FROM recipes WHERE user_id = ?', (user_id,)).fetchall()
    return render_template('your_recipes.html', recipes=recipes)

@app.route('/about_us')
def about():
    return render_template('aboutus.html')

@app.route('/reset_db')
def reset_db():
    db = get_db()
    with app.open_resource('reset_db.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    flash('Database has been reset.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
