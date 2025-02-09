import datetime
from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_mail import Mail
import pymysql
import json

local_server = True
with open("server/config.json",'r') as c:
    params = json.load(c)["params"]

pymysql.install_as_MySQLdb()  # This makes pymysql work as MySQLdb

app = Flask(__name__)
app.secret_key="my secret key"
app.config.update(
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_PORT = "465",
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params["gmail_user"],
    MAIL_PASSWORD = params["gmail_password"]
)

mail = Mail(app)

if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["local_uri"]
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["prod_uri"]

db = SQLAlchemy(app)

class Contacts(db.Model):
    """
    Represents contacts.

    Attributes:
        id (int): Primary key, auto-incremented.
        name (str): Unique username of the user.
        phone (str): Phone number od the user.
        email (str): Unique email address (max 50 chars).
        msg (str): Input message.
        date (datetime): Timestamp when the contact was saved.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(12), nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    date = db.Column(db.DateTime(timezone=True),server_default=func.now())
    msg = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<Contacts {self.name}>'


class Posts(db.Model):
    """
    Represents contacts.

    Attributes:
        id (int): Primary key, auto-incremented.
        title (str): Title of the blog.
        subtitle (str): Subtitle if any.
        slug (str): unique url text.
        content (str): Blog content.
        created_by (str): Blogger name.
        date (datetime): Timestamp when the contact was saved.
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    subtitle = db.Column(db.Text, nullable=False)
    slug = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime(timezone=True),server_default=func.now())

    def __repr__(self):
        return f'<Posts {self.title}>'


@app.route("/")
def home():
    posts = Posts.query.filter_by().all()[0:params["no_of_posts"]]
    return render_template("index.html", params = params, posts = posts)

@app.route("/dashboard", methods = ["GET","POST"])
def dashboard():
    if 'user' in session and session['user'] == params["admin_user"]:
        posts = Posts.query.all()
        return render_template("dashboard.html",params = params, posts=posts)

    if request.method == "POST":
        username = request.form.get('uname')
        password = request.form.get('pass')
        if username == params["admin_user"] and password == params["admin_password"]:
            #SET SESSION VARIABLE
            session['user'] = username
            posts = Posts.query.all()
            return render_template("dashboard.html", params = params, posts = posts)
    return render_template("login.html", params = params)

@app.route("/about")
def about():
    return render_template('about.html', params = params )

@app.route("/post/<string:post_slug>", methods = ["GET"])
def post(post_slug):
    new_post = Posts.query.filter_by(slug = post_slug).first()
    return render_template('post.html', params = params, post = new_post)


@app.route("/edit/<string:id>", methods = ["GET","POST"])
def edit(id):
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == "POST":
            box_title = request.form.get("title")
            subtitle = request.form.get("subtitle")
            content = request.form.get("content")
            slug = request.form.get("slug")
            date = datetime.datetime.now()
            created_by = params['admin_user']
            if id == "0":
                post = Posts(title= box_title, subtitle= subtitle, content= content, slug= slug, date= date, created_by= created_by)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(id=id).first()
                post.title = box_title
                post.subtitle = subtitle
                post.slug = slug
                post.content = content
                post.date = date
                post.created_by = created_by
                db.session.commit()
                return redirect('/edit/' + id)

    post = Posts.query.filter_by(id=id).first()
    return render_template('edit.html', params = params, post = post)

#TODO : Implement delete API
@app.route("/delete/<string:id>", methods = ["GET","POST"])
def delete(id):
    return render_template('contact.html', params = params)


@app.route("/contact", methods = ["GET","POST"])
def contact():
    if request.method == "POST":
        '''Add entry to the database'''
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        msg = request.form.get("message")
        entry = Contacts(name= name, phone= phone, email= email, msg= msg)
        db.session.add(entry)
        db.session.commit()
        '''
        Google doesn't allow access like this,
        until we allow mails from less secure app. 
        Therefore we keep this only for knowledge.
        '''
        # mail.send_message('New message from '+ name, sender = email, recipients = [params["gmail_user"]], body = msg + "\n" + phone)
    return render_template('contact.html', params = params)

app.run(debug=True)