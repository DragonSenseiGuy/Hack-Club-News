from flask import Flask, render_template, request, redirect, make_response, send_from_directory
from feed2json import feed2json
import os #noqa: F401
from dotenv import load_dotenv
import dateutil.parser
import json
from werkzeug.utils import secure_filename
from datetime import datetime

UPLOAD_FOLDER = 'data' 
ALLOWED_EXTENSIONS = {'json'}
JSON_DIR="data"
JSON_FILENAME="feeds.json"

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
load_dotenv()

def get_feeds():
    if not os.path.exists('data/feeds.json'):
        return []
    else:
        with open('data/feeds.json', 'r') as f:
            try:
                data = json.load(f)
                return data.get('urls', [])
            except json.JSONDecodeError:
                return []
    return "Unexpected Error Occured", 500

def get_all_items():
    all_items = []
    rss_feeds = get_feeds()
    for feed_url in rss_feeds:
        json_feed:dict = feed2json(feed_url)
        if "items" in json_feed:
            all_items.extend(json_feed["items"])
    
    if os.path.exists('data/posts.json'):
        with open('data/posts.json', 'r') as f:
            try:
                posts = json.load(f)
                all_items.extend(posts)
            except json.JSONDecodeError:
                pass

    all_items.sort(key=lambda item: dateutil.parser.parse(item.get("date_published", "1970-01-01T00:00:00Z")), reverse=True)
    return all_items

@app.route("/")
def home():
    items = get_all_items()[0:30]
    custom_theme_cookie = request.cookies.get("custom_theme")
    custom_theme = json.loads(custom_theme_cookie) if custom_theme_cookie else None
    current_theme = request.cookies.get("theme", "Hacker News")
    return render_template("home.html", items=items, custom_theme=custom_theme, current_theme=current_theme)


@app.route("/post/<int:item_number>")
def post(item_number):
    items = get_all_items()
    custom_theme_cookie = request.cookies.get("custom_theme")
    custom_theme = json.loads(custom_theme_cookie) if custom_theme_cookie else None
    current_theme = request.cookies.get("theme", "Hacker News")
    if 0 <= item_number < len(items):
        return render_template("post.html", item=items[item_number], custom_theme=custom_theme, current_theme=current_theme, item_number=item_number)
    return None


@app.route("/settings")
def settings():
    current_theme = request.cookies.get("theme", "Hacker News")
    custom_theme_cookie = request.cookies.get("custom_theme")
    custom_theme = json.loads(custom_theme_cookie) if custom_theme_cookie else None
    return render_template("settings.html", current_theme=current_theme, custom_theme=custom_theme)

@app.route("/change_theme", methods=["POST"])
def change_theme():
    theme = request.form.get("theme")
    if theme == "Custom":
        custom_theme = {
            "background_color": request.form.get("background_color"),
            "text_color": request.form.get("text_color"),
            "nav_bar_color": request.form.get("nav_bar_color"),
            "nav_bar_links_color": request.form.get("nav_bar_links_color"),
            "homepage_links_color": request.form.get("homepage_links_color"),
            "visited_homepage_links_color": request.form.get("visited_homepage_links_color"),
        }
        resp = make_response(redirect("/settings"))
        resp.set_cookie("theme", "Custom")
        resp.set_cookie("custom_theme", json.dumps(custom_theme))
    else:
        resp = make_response(redirect("/settings"))
        resp.set_cookie("theme", theme)
        resp.delete_cookie("custom_theme")
    return resp


@app.route("/custom_theme")
def custom_theme():
    custom_theme_cookie = request.cookies.get("custom_theme")
    custom_theme = json.loads(custom_theme_cookie) if custom_theme_cookie else None
    current_theme = request.cookies.get("theme", "Hacker News")
    return render_template("custom_theme.html", custom_theme=custom_theme, current_theme=current_theme)


@app.route("/clear_custom_theme", methods=["POST"])
def clear_custom_theme():
    resp = make_response(redirect("/settings"))
    resp.delete_cookie("custom_theme")
    return resp

@app.route("/add_post", methods=["POST"])
def add_post():
    post_title = request.form.get("post_title")
    post_url = request.form.get("post_url")
    post_content = request.form.get("post_content")
    if post_title and post_url and post_content:
        with open('data/posts.json', 'r') as f:
            posts = json.load(f)
        
        posts.append({
            "title": post_title,
            "url": post_url,
            "content": post_content,
            "date_published": datetime.utcnow().isoformat(),
            "upvotes": 0,
            "comment_number": 0,
            "comments": [],
            "upvoted_by": []
        })

        with open('data/posts.json', 'w') as f:
            json.dump(posts, f, indent=4)

    return redirect("/")

@app.route("/upvote/<int:item_number>")
def upvote(item_number):
    items = get_all_items()
    username = request.cookies.get("username")
    if 0 <= item_number < len(items) and username:
        # this is not a good way to do this, but it's the only way with the current structure
        # I should really be using a database for this
        with open('data/posts.json', 'r') as f:
            posts = json.load(f)
        
        for post in posts:
            if post['title'] == items[item_number]['title']:
                if username not in post.get('upvoted_by', []):
                    post['upvotes'] += 1
                    if 'upvoted_by' not in post:
                        post['upvoted_by'] = []
                    post['upvoted_by'].append(username)
                break
        
        with open('data/posts.json', 'w') as f:
            json.dump(posts, f, indent=4)

    return redirect("/")

@app.route("/add_comment/<int:item_number>", methods=["POST"])
def add_comment(item_number):
    items = get_all_items()
    if 0 <= item_number < len(items):
        with open('data/posts.json', 'r') as f:
            posts = json.load(f)
        
        for post in posts:
            if post['title'] == items[item_number]['title']:
                post['comments'].append({
                    "username": request.cookies.get("username"),
                    "comment": request.form.get("comment")
                })
                post['comment_number'] += 1
                break
        
        with open('data/posts.json', 'w') as f:
            json.dump(posts, f, indent=4)

    return redirect(f"/post/{item_number}")

@app.route("/newpost")
def newpost():
    return render_template("newpost.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/auth", methods=["POST"])
def auth():
    username = request.form.get("username")
    password = request.form.get("password")
    if username and password:
        try:
            with open('data/users.json', 'r') as f:
                users = json.load(f)
                for user in users:
                    if user['username'] == username and user['password'] == password:
                        resp = make_response(redirect("/"))
                        resp.set_cookie("logged_in", "true")
                        resp.set_cookie("username", username)
                        return resp
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    return redirect("/login")

@app.route("/sign_up", methods=["POST"])
def sign_up():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")
    if username and email and password:
        try:
            with open('data/users.json', 'r') as f:
                users = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            users = []
        
        users.append({
            "username": username,
            "email": email,
            "password": password
        })

        with open('data/users.json', 'w') as f:
            json.dump(users, f, indent=4)
            
        resp = make_response(redirect("/"))
        resp.set_cookie("logged_in", "true")
        resp.set_cookie("username", username)
        return resp

@app.route("/logout")
def logout():
    resp = make_response(redirect("/"))
    resp.delete_cookie("logged_in")
    resp.delete_cookie("username")
    return resp



if __name__=="__main__":
    app.run()