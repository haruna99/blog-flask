from flask import Flask, render_template
from post import Post

app = Flask(__name__)
post = Post().posts


@app.route('/')
def home():
    return render_template("index.html", posts=post)


@app.route("/post/<int:post_id>")
def single_post(post_id):
    requested_post = None
    for blog_post in post:
        if blog_post["id"] == post_id:
            requested_post = blog_post
    return render_template("post.html", id=post_id, post=requested_post)


if __name__ == "__main__":
    app.run(debug=True)
