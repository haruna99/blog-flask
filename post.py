import requests
blog_url = "https://api.npoint.io/d8ac0f18e2b7fc75e7d7"


class Post:
    def __init__(self):
        response = requests.get(url=blog_url)
        self.posts = response.json()

