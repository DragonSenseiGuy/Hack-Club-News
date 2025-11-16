# Hack Club News

Hack Club News is a platform like [Hacker News](https://news.ycombinator.com/) for Hack Clubbers to share any new and interesting news.

## Features

Hack Club News incudes
- Hacker News like posting capabilities
- User creation
- Data storage in a JSON file(I know it's not good practice, but it is simple)
- Custom Themes
- Commenting
- Upvoting


## Setup(macOS)

Make a virtual environment
```
python3 -m venv .venv
```

Activate virtual environment

Windows:
```
.venv\Scripts\activate
```

Linux/macOS:
```
source .venv/bin/activate
```

Instal dependencies:

This project uses `uv` so you need uv installed
```
uv sync
```

Start the development server

```
flask run --debug
```

## Screenshots
![Demo Image of Hack Club News](demo_img.png)
