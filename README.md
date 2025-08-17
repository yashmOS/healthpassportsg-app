# healthpassportsg-app
This repo is the main app for healthpassportsg. It manages both frontend and backend using flask framework.

## Getting Started
This repo uses `uv` to manage dependencies and virtual environment. Follow this [guide](https://docs.astral.sh/uv/getting-started/) to set up `uv`. 

To create virtual environment and install all dependencies, run: 

```sh
uv sync
```

Activate virtual environment:

```sh
source .venv/bin/activate
```

Run application with this command   
```
flask run
```
Or with debugging mode on
```
flask --app app.py --debug run
```

### Some info
Database: `healthpassportsg.db`