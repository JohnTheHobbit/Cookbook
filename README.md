# Home Cookbook

A self-hosted recipe management application for your home network. Built with Flask, SQLite, and Bootstrap.

## Features

- **Search recipes** by name, description, or ingredients
- **Filter recipes** by category
- **Add/edit recipes** with a user-friendly form
- **Recipe sections** - organize complex recipes into parts (e.g., "Shell" and "Filling" for cannoli)
- **Rich text notes** - format notes with bold, italic, lists, and links
- **Import recipes** from CSV with downloadable template
- **Export recipes** to CSV for backup
- **Favorite recipes** for quick access
- **US/Metric conversion** toggle on recipe view
- **Print-friendly** layout for recipes
- **Download PDF** - export recipes as PDF files
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

## Kubernetes (K3S) Deployment

For K3S clusters with persistent storage:

1. **Create namespace and PVC:**
   ```yaml
   # 01-namespace.yaml
   apiVersion: v1
   kind: Namespace
   metadata:
     name: cookbook
   ---
   # 02-pvc.yaml
   apiVersion: v1
   kind: PersistentVolumeClaim
   metadata:
     name: cookbook-data
     namespace: cookbook
   spec:
     accessModes:
       - ReadWriteOnce
     storageClassName: local-path
     resources:
       requests:
         storage: 1Gi
   ```

2. **Deploy with volume mount:**
   ```yaml
   # deployment.yaml
   spec:
     containers:
       - name: cookbook
         image: registry.example.com/home-cookbook:latest
         volumeMounts:
           - name: data
             mountPath: /app/data
     volumes:
       - name: data
         persistentVolumeClaim:
           claimName: cookbook-data
   ```

3. **Apply with kubectl or ArgoCD**

## CSV Import Format

Download the template from the Import page or use this format:

| Column | Required | Description |
|--------|----------|-------------|
| title | Yes | Recipe name |
| category | No | Category name (created if new) |
| description | No | Short description |
| prep_time_minutes | No | Prep time in minutes |
| cook_time_minutes | No | Cook time in minutes |
| rest_time_minutes | No | Rest/inactive time (rising, chilling, marinating) |
| servings | No | Number of servings |
| servings_unit | No | e.g., "servings", "pieces" |
| ingredients | No | Pipe-separated: `2 cups flour\|1 tsp salt` |
| instructions | Yes | Step-by-step instructions |
| notes | No | Additional tips (supports HTML formatting) |
| source | No | Where recipe came from |

### Ingredient Format

Ingredients are parsed automatically:
- `2 cups all-purpose flour` → quantity: 2, unit: cups, name: all-purpose flour
- `1/2 tsp salt` → quantity: 0.5, unit: tsp, name: salt
- `butter, melted` → name: butter, preparation: melted
- `parsley (optional)` → name: parsley, optional: true

### Sectioned Recipes

For recipes with multiple sections (e.g., a cannoli with separate Shell and Filling), use section markers:

**Ingredients column:**
```
[Shell]2 cups flour|1/2 cup butter[Filling]2 cups ricotta|1 cup sugar
```

**Instructions column:**
```
[Shell]Step 1 for shell
Step 2 for shell[Filling]Step 1 for filling
Step 2 for filling
```

Each section name in square brackets groups the ingredients and instructions that follow it.

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
- **Frontend:** Bootstrap 5, htmx, Quill Editor
- **PDF Generation:** WeasyPrint
- **Security:** Bleach for HTML sanitization
- **Deployment:** Docker, Gunicorn, Kubernetes/K3S

## License

MIT License - Feel free to use and modify for your home.
