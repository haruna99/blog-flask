from flask import Flask, render_template, url_for
import requests

app = Flask(__name__)

response = requests.get("https://api.npoint.io/338826d1ef3417713ca3")
posts = response.json()


@app.route('/')
def home():
    return render_template("index.html", posts=posts)


@app.route('/contact')
def contact():
    return render_template("contact.html")


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
