from flask import Flask, render_template, request, redirect, make_response, send_from_directory
from feed2json import feed2json
import os #noqa: F401
from dotenv import load_dotenv
import dateutil.parser
import json
from werkzeug.utils import secure_filename

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
    all_items.sort(key=lambda item: dateutil.parser.parse(item.get("date_published", "1970-01-01T00:00:00Z")), reverse=True)
    return all_items

@app.route("/")
def home():
    items = get_all_items()[0:30]
    custom_theme_cookie = request.cookies.get("custom_theme")
    custom_theme = json.loads(custom_theme_cookie) if custom_theme_cookie else None
    current_theme = request.cookies.get("theme", "Hacker News")
    return render_template("home.html", items=items, custom_theme=custom_theme, current_theme=current_theme)


@app.route("/blog/<int:item_number>")
def blog(item_number):
    items = get_all_items()
    custom_theme_cookie = request.cookies.get("custom_theme")
    custom_theme = json.loads(custom_theme_cookie) if custom_theme_cookie else None
    current_theme = request.cookies.get("theme", "Hacker News")
    if 0 <= item_number < len(items):
        return render_template("blog.html", item=items[item_number], custom_theme=custom_theme, current_theme=current_theme)
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

@app.route("/add_feed", methods=["POST"])
def add_feed():
    feed_url = request.form.get("feed_url")
    if feed_url:
        try:
            with open('data/feeds.json', 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {'urls': []}

        if feed_url not in data['urls']:
            data['urls'].append(feed_url)

        with open('data/feeds.json', 'w') as f:
            json.dump(data, f, indent=4)
            
    return redirect("/settings")

@app.route("/remove_feed", methods=["POST"])
def remove_feed():
    feed_url = request.form.get("feed_url")
    if feed_url:
        try:
            with open('data/feeds.json', 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {'urls': []}

        if 'urls' in data and feed_url in data['urls']:
            data['urls'].remove(feed_url)

        with open('data/feeds.json', 'w') as f:
            json.dump(data, f, indent=4)

    return redirect("/settings")

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return "No file part in the request", 400
    
    file = request.files["file"]

    if file.filename == "":
        return "No selected file", 400
    
    if file :
        filename = secure_filename("feeds.json")
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        return redirect("/")
    
@app.route("/export_json")
def export_json():
    return send_from_directory(
        directory=JSON_DIR, 
        path=JSON_FILENAME, 
        as_attachment=True
    )

if __name__=="__main__":
    app.run()