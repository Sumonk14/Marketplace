import os
import uuid
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from functools import wraps
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from werkzeug.utils import secure_filename
from forms import EditArticleForm, ArticleForm
  

app = Flask(__name__)


# config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '12341234'
app.config['MYSQL_DB'] = 'MyFlaskApp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['UPLOAD_FOLDER'] = 'static/item_pics'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
# init MySQL

mysql = MySQL(app)  

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():

    cur = mysql.connection.cursor()
    # Ensure all columns are selected here:
    result = cur.execute("SELECT *, contact_info, price, image_file FROM articles")
    articles = cur.fetchall()


    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', msg=msg)
    # Close connection
    cur.close()


#Single Article
@app.route('/article/<string:id>/')
def article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article

    result = cur.execute("SELECT *, contact_info, price, details, image_file FROM articles WHERE id = %s", [id]) 
    article = cur.fetchone()

    return render_template('article.html', article=article)


# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Password do not match')
    ])
    confirm = PasswordField('Confirm Password')

# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        #create cursor
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", 
                    (name, email, username, password))

        # commit to DB
        mysql.connection.commit()

        #close connection
        cur.close()

        flash('You are now registered and now log in', 'success')

        return redirect(url_for('login '))
    return render_template('register.html', form=form)

#user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # GET FORM Fields
        username = request.form['username'] 
        password_candidate = request.form['password']

        # CREATE CURSOR
        cur = mysql.connection.cursor()

        #get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", (username,))

        if result > 0:
            # Get started hash
            data = cur.fetchone()
            password = data['password']

            # compare password
            if sha256_crypt.verify(password_candidate, password):  
                #passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else: 
                error = 'Invalid login'
                return render_template('login.html', error=error)
            #CLOSE CONNECTION   
            cur.close()
        else:
            error = 'username not found'
            return render_template('login.html', error=error)


    return render_template('login.html')
# check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    
    if request.method == 'POST' and form.validate():
        
        # 1. Handle Image Upload
        file = form.image.data # Get the file object from the validated form
        
        # Generate a unique and secure filename
        original_filename = secure_filename(file.filename)
        # Use a unique UUID prefix and the file extension to prevent name collisions
        unique_prefix = uuid.uuid4().hex[:8] 
        unique_filename = f"{unique_prefix}_{original_filename}"
        
        # Save the file to the configured folder
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)

        # 2. Get Other Form Data
        title = form.title.data
        price = form.price.data
        details = form.details.data
        contact_info = form.contact_info.data
        
        # 3. Database Insertion
        try:
            cur = mysql.connection.cursor()
            
            # NOTE: Ensure your SQL matches the new columns: price, details, contact_info, image_file
            cur.execute(
                """INSERT INTO articles(title, author, price, details, contact_info, image_file) 
                   VALUES(%s, %s, %s, %s, %s, %s)""", 
                (title, session['username'], price, details, contact_info, unique_filename)
            )
            
            mysql.connection.commit()
            cur.close()

            flash('Item Posted Successfully!', 'success')
            return redirect(url_for('dashboard'))

        except Exception as e:
            # Good practice: if DB fails, delete the uploaded file
            if os.path.exists(file_path):
                 os.remove(file_path)
            # You might want to print(e) for debugging
            flash('An error occurred while posting the item. File upload reverted.', 'danger')
            return render_template('add_article.html', form=form)

    return render_template('add_article.html', form=form)

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


# Dasboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    #Get article
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No Article Found'
        return render_template('dashboard.html', msg=msg)
    #close connection
    cur.close()


# app.py

@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # 1. Fetch the original article data
    cur = mysql.connection.cursor()
    # Select all fields and verify the user is the author
    result = cur.execute("SELECT * FROM articles WHERE id = %s AND author = %s", [id, session['username']])
    article = cur.fetchone() # Fetch the item as a dictionary
    
    if not article:
        flash('Item not found or you are not the owner.', 'danger')
        return redirect(url_for('dashboard'))

    # 2. Instantiate the NEW form (EditArticleForm)
    form = EditArticleForm(request.form) 

    if request.method == 'POST' and form.validate():
        
        # Data from the form submission
        title = form.title.data
        price = form.price.data
        details = form.details.data
        contact_info = form.contact_info.data
        current_image = article['image_file']
        image_to_save = current_image # Default: keep the old image

        # 3. Handle Image Replacement
        file = form.image.data
        if file and file.filename: # Checks if a new file was actually uploaded
            
            # Save new file
            original_filename = secure_filename(file.filename)
            unique_prefix = uuid.uuid4().hex[:8] 
            new_filename = f"{unique_prefix}_{original_filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
            file.save(file_path)

            # Delete the old file from the server
            old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], current_image)
            if os.path.exists(old_file_path) and current_image:
                os.remove(old_file_path)
                
            # Update the image filename for the database
            image_to_save = new_filename

        # 4. Update Database
        cur.execute("""
            UPDATE articles SET title=%s, price=%s, details=%s, contact_info=%s, image_file=%s 
            WHERE id=%s
        """, (title, price, details, contact_info, image_to_save, id))
        
        mysql.connection.commit()
        cur.close()

        flash('Item Updated Successfully', 'success')
        return redirect(url_for('dashboard'))

    # GET request: Pre-fill the form fields for the user
    form.title.data = article['title']
    form.price.data = article['price']
    form.details.data = article['details']
    form.contact_info.data = article['contact_info']
    
    # Pass the 'article' data to the template to display the current image
    return render_template('edit_article.html', form=form, article=article)

# Delete Article
# app.py

@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    cur = mysql.connection.cursor()

    # 1. Fetch the image filename BEFORE deleting the record
    # We also check for ownership (author = session['username']) here for security
    cur.execute("SELECT image_file FROM articles WHERE id = %s AND author = %s", [id, session['username']])
    result = cur.fetchone()
    
    if not result:
        # Item not found or user is not the owner
        flash('Item not found or you are not authorized to delete it.', 'danger')
        return redirect(url_for('dashboard'))

    image_filename = result['image_file'] # Get the filename

    # 2. Delete the file from the server
    if image_filename:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
        
        # Ensure the file exists before trying to delete it
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                # Log an error if file deletion fails but proceed with DB deletion
                print(f"Error deleting file {file_path}: {e}")
                
    # 3. Delete the record from the database
    cur.execute("DELETE FROM articles WHERE id = %s", [id])
    
    mysql.connection.commit()
    cur.close()

    flash('Item Deleted Successfully, including image cleanup.', 'success')
    
    # Check if request is AJAX (typical for the delete button) or a standard redirect
    if request.is_json:
        return {'status': 'success'}
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.secret_key ='secret123'
    app.run(debug = True)