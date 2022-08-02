from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditor, CKEditorField
from smtplib import SMTP
import os
import datetime as dt

MY_EMAIL = os.environ.get("MY_EMAIL")
MY_PASSWORD = os.environ.get("MY_PASSWORD")

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog_posts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return f"<Post: {self.title}>"


# db.create_all()


class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    author = StringField("Your Name", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


@app.route('/')
def home():
    posts = BlogPost.query.all()
    return render_template("index.html", posts=posts)


@app.route('/contact', methods=["POST", "GET"])
def contact():
    if request.method == "GET":
        success = False
    if request.method == "POST":
        data = request.form
        name = data["username"]
        email = data["email"]
        message = data["message"]
        phone = data["phone"]
        with SMTP("smtp.mail.yahoo.com") as connection:
            connection.starttls()
            connection.login(user=MY_EMAIL, password=MY_PASSWORD)
            connection.sendmail(
                from_addr=MY_EMAIL,
                to_addrs=MY_EMAIL,
                msg=f"Subject:Haruna's Blog\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nMessage: {message}")
        success = True
    return render_template("contact.html", success=success)


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/post/<int:post_id>')
def post(post_id):
    single_post = BlogPost.query.get(post_id)
    return render_template("post.html", post=single_post)


@app.route("/new-post", methods=["GET", "POST"])
def new_post():
    form = CreatePostForm()
    today = dt.datetime.today()
    if form.validate_on_submit():
        blog_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            date=today.strftime("%B %d, %Y"),
            body=form.body.data,
            author=form.author.data,
            img_url=form.img_url.data
        )

        db.session.add(blog_post)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("make-post.html", form=form, title="New Post")


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    blog_post = BlogPost.query.get(post_id)
    form = CreatePostForm(
        title=blog_post.title,
        subtitle=blog_post.subtitle,
        img_url=blog_post.img_url,
        author=blog_post.author,
        body=blog_post.body
    )
    print(form.title.data)
    if form.validate_on_submit():
        blog_post.title = form.title.data
        blog_post.subtitle = form.subtitle.data
        blog_post.body = form.body.data
        blog_post.author = form.author.data
        blog_post.img_url = form.img_url.data
        db.session.commit()
        return redirect(url_for("post", post_id=blog_post.id))

    return render_template("make-post.html", form=form, title="Edit Post")


@app.route("/delete/<int:post_id>")
def delete_post(post_id):
    blog_post = BlogPost.query.get(post_id)
    db.session.delete(blog_post)
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)
