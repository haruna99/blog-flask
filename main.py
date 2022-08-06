from flask import Flask, render_template, redirect, url_for, flash, abort, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_ckeditor import CKEditor
import datetime as dt
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm, ContactForm
from flask_gravatar import Gravatar
from functools import wraps
from smtplib import SMTP
import os

MY_EMAIL = os.environ.get("MY_EMAIL")
MY_PASSWORD = os.environ.get("MY_PASSWORD")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
ckeditor = CKEditor(app)
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///blog_posts.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

gravatar = Gravatar(
    app,
    size=100,
    rating='g',
    default='retro',
    force_default=False,
    force_lower=False,
    use_ssl=False,
    base_url=None
)


class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")

    def __repr__(self):
        return f"<Post: {self.name}>"


class BlogPost(db.Model):
    __tablename__ = "blog_post"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post_author")

    def __repr__(self):
        return f"<Post: {self.title}>"


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    comment_author = relationship("User", back_populates="comments")
    post_id = db.Column(db.Integer, db.ForeignKey("blog_post.id"))
    post_author = relationship("BlogPost", back_populates="comments")


db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.context_processor
def inject_user():
    return dict(logged_in=current_user.is_authenticated)


def admin_only(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_user.is_authenticated:
            if current_user.id != 1:
                return abort(403)
            else:
                return f(*args, **kwargs)
        else:
            return abort(403)

    return wrapper


@app.route('/')
def home():
    posts = BlogPost.query.all()
    return render_template("index.html", posts=posts)


@app.route('/register', methods=["GET", "POST"])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        email = register_form.email.data
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash("You already signed up. Log in instead!")
            return redirect(url_for('login'))
        else:
            hashed_password = generate_password_hash(
                register_form.password.data,
                method='pbkdf2:sha256',
                salt_length=8
            )
            new_user = User(
                name=register_form.name.data,
                email=email,
                password=hashed_password
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for("home"))

    return render_template("register.html", form=register_form)


@app.route('/login', methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('This email does not exist, try again!')
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('The password you entered is not correct, try again!')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))

    return render_template("login.html", form=login_form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        phone = form.phone.data
        message = form.message.data
        with SMTP("smtp.mail.yahoo.com") as connection:
            connection.starttls()
            connection.login(user=MY_EMAIL, password=MY_PASSWORD)
            connection.sendmail(
                from_addr=MY_EMAIL,
                to_addrs=MY_EMAIL,
                msg=f"Subject:Haruna's Blog\n\nName: {name}\nEmail: {email}\nPhone Number: {phone}\nMessage: {message}"
            )
        form.name.data = ""
        form.email.data = ""
        form.phone.data = ""
        form.message.data = ""
        return render_template("contact.html", form=form, message_sent=True)

    return render_template("contact.html", form=form, message_sent=False)


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/post/<int:post_id>', methods=["GET", "POST"])
def post(post_id):
    single_post = BlogPost.query.get(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        if current_user.is_authenticated:
            new_comment = Comment(
                text=form.body.data,
                comment_author=current_user,
                post_author=single_post
            )
            db.session.add(new_comment)
            db.session.commit()
            return redirect(url_for("post", post_id=post_id))
        else:
            flash("You need to login or register to comment")
            return redirect(url_for("login"))
    return render_template("post.html", post=single_post, form=form)


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def new_post():
    form = CreatePostForm()
    today = dt.datetime.today()
    if form.validate_on_submit():
        blog_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            date=today.strftime("%B %d, %Y"),
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user
        )

        db.session.add(blog_post)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("make-post.html", form=form, title="New Post")


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    blog_post = BlogPost.query.get(post_id)
    form = CreatePostForm(
        title=blog_post.title,
        subtitle=blog_post.subtitle,
        img_url=blog_post.img_url,
        body=blog_post.body
    )
    if form.validate_on_submit():
        blog_post.title = form.title.data
        blog_post.subtitle = form.subtitle.data
        blog_post.body = form.body.data
        blog_post.author = current_user
        blog_post.img_url = form.img_url.data
        db.session.commit()
        return redirect(url_for("post", post_id=blog_post.id))

    return render_template("make-post.html", form=form, title="Edit Post")


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    blog_post = BlogPost.query.get(post_id)
    db.session.delete(blog_post)
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)
