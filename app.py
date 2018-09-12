from flask import Flask, render_template, flash, redirect, url_for, session, request, logging

from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps


app = Flask(__name__)

#app config

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'shivam'
app.config['MYSQL_DB'] = 'blogdb'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)



@app.route('/')
def index():
    return render_template('home.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

class RegisterForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=25)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')



@app.route('/register',methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
    
        username = form.username.data
        password = form.password.data

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO Users(Username, pwd) VALUES(%s, %s)", (username, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        # return redirect(url_for('login'))
        return "registration done"
    return render_template('register.html', form=form)

class BlogForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    content = TextAreaField('Body', [validators.Length(min=10)])
@app.route('/addBlog',methods=['GET','POST'])
@is_logged_in
def addBlog():
    form =BlogForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        content=form.content.data
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO blogs(title, content, Username) VALUES(%s, %s, %s)", (title, content, session['username']))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('dashboard'))
    return render_template('addBlog.html',form=form)

class CommentForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    comment = TextAreaField('comment', [validators.Length(min=5)])

@app.route('/comment/<blogname>',methods=['GET','POST'])
@is_logged_in
def comment(blogname):
    form=CommentForm(request.form)
    if request.method == 'POST' and form.validate():
       title=form.title.data
       comment=form.comment.data
       cur = mysql.connection.cursor()
       cur.execute("INSERT INTO Comments(title, comment) VALUES(%s, %s)", (title, comment))
       mysql.connection.commit()
       cur.close()
       return redirect(url_for('dashboard'))
       
    return render_template('addComment.html',form=form,titlename=blogname)

@app.route('/blogs')
def getblogs():
     cur = mysql.connection.cursor()
     res=cur.execute("select * from blogs")
     mysql.connection.commit()
     if res>0:
         data=cur.fetchall()
         return render_template('blogs.html',data=data)
     cur.close()
     
     return "No blog currently"

@app.route('/blogs/<blogname>')
def showblog(blogname):
    cur = mysql.connection.cursor()
    cur2 = mysql.connection.cursor()
    res=cur.execute("select * from blogs where title=%s",[blogname])
    res2=cur2.execute("select * from Comments where title=%s",[blogname])

    if res>0 or res2>0:
        data=cur.fetchall()
        data2=cur2.fetchall()
        return render_template('blog.html',tosend=data+data2,length=len(data+data2))
    cur.close()
    return "fail"



# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM blogs")

    blogs = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', blogs=blogs)
    else:
        msg = 'No logs Found'
        return render_template('dashboard.html', msg=msg)
    # Close connection
    cur.close()

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM Users WHERE Username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['pwd']

            # Compare Passwords
            if password==password_candidate:
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')



if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)