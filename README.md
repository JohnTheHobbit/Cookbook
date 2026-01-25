# Home Cookbook

A self-hosted recipe management application for your home network. Built with Flask, SQLite, and Bootstrap.

## Features

- **Search recipes** by name, description, or ingredients
- **Filter recipes** by category
- **Add/edit recipes** with a user-friendly form
- **Import recipes** from CSV with downloadable template
- **Export recipes** to CSV for backup
- **Favorite recipes** for quick access
- **US/Metric conversion** toggle on recipe view
- **Print-friendly** layout for recipes
- **Kitchen mode** - keeps screen on with larger text
- **Mobile responsive** design

## Quick Start

### Local Development

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the development server:**
   ```bash
   python run.py
   ```

4. **Open in browser:**
   ```
   http://localhost:5000
   ```

### Docker Deployment

1. **Build and run with Docker Compose:**
   ```bash
   docker-compose up -d --build
   ```

2. **Access the app:**
   ```
   http://localhost:8080
   ```

## Synology NAS Deployment

### Using Container Manager (Docker)

1. **Copy project files** to your Synology NAS:
   ```
   /volume1/docker/cookbook/
   ```

2. **Create data directory** for persistence:
   ```bash
   mkdir -p /volume1/docker/cookbook/data
   ```

3. **Open Container Manager** in DSM

4. **Create a new Project:**
   - Go to Project → Create
   - Set path to `/volume1/docker/cookbook`
   - Use the included `docker-compose.yml`

5. **Build and start** the container

6. **Access the app:**
   ```
   http://<your-synology-ip>:8080
   ```

### Backup

Add the data directory to Hyper Backup:
```
/volume1/docker/cookbook/data/
```

The SQLite database is a single file (`cookbook.db`), making backups simple.

## CSV Import Format

Download the template from the Import page or use this format:

| Column | Required | Description |
|--------|----------|-------------|
| title | Yes | Recipe name |
| category | No | Category name (created if new) |
| description | No | Short description |
| prep_time_minutes | No | Prep time in minutes |
| cook_time_minutes | No | Cook time in minutes |
| servings | No | Number of servings |
| servings_unit | No | e.g., "servings", "pieces" |
| ingredients | No | Pipe-separated: `2 cups flour\|1 tsp salt` |
| instructions | Yes | Step-by-step instructions |
| notes | No | Additional tips |
| source | No | Where recipe came from |

### Ingredient Format

Ingredients are parsed automatically:
- `2 cups all-purpose flour` → quantity: 2, unit: cups, name: all-purpose flour
- `1/2 tsp salt` → quantity: 0.5, unit: tsp, name: salt
- `butter, melted` → name: butter, preparation: melted
- `parsley (optional)` → name: parsley, optional: true

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| FLASK_ENV | development | Set to `production` for deployment |
| DATABASE_URL | sqlite:///data/cookbook.db | Database connection string |
| SECRET_KEY | dev-secret-key | Change this in production! |

## Project Structure

```
cookbook/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Configuration
│   ├── models/              # Database models
│   ├── routes/              # URL routes
│   ├── services/            # Business logic
│   ├── static/              # CSS, JS, images
│   └── templates/           # HTML templates
├── data/                    # SQLite database
├── templates/               # CSV template
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── run.py                   # Development server
└── wsgi.py                  # Production entry point
```

## Tech Stack

- **Backend:** Python 3.11, Flask
- **Database:** SQLite with SQLAlchemy ORM
- **Frontend:** Bootstrap 5, htmx
- **Deployment:** Docker, Gunicorn

## License

MIT License - Feel free to use and modify for your home.
