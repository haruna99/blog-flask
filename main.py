from flask import Flask, render_template, url_for, request
import requests
from smtplib import SMTP
import os

MY_EMAIL = os.environ.get("MY_EMAIL")
MY_PASSWORD = os.environ.get("MY_PASSWORD")

app = Flask(__name__)

response = requests.get("https://api.npoint.io/338826d1ef3417713ca3")
posts = response.json()


@app.route('/')
def home():
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
    single_post = None
    for new_post in posts:
        if post_id == new_post["id"]:
            single_post = new_post
    return render_template("post.html", post=single_post)


if __name__ == "__main__":
    app.run(debug=True)
