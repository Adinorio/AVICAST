# Django Project Setup Guide

## 1. Prerequisites
- Python 3.11.6
- MySQL/MariaDB server (for database)
- (Optional) Virtual environment tool: `venv` or `virtualenv`

## 2. Clone the Repository
```sh
git clone <your-repo-url>
cd <your-project-folder>
```

## 3. Create and Activate a Virtual Environment
```sh
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

## 4. Install Dependencies
### For all users (runtime/inference only):
```sh
pip install -r requirements.txt
```
### For users who want to train or update the model (includes heavy ML packages):
```sh
pip install -r requirements-train.txt
```

## 5. Set Up Environment Variables
- Copy `.env.example` to `.env` and fill in your database credentials and any other secrets.

## 6. Set Up the Database
- Create a database and user in MySQL/MariaDB matching your `.env` settings.

## 7. Run Migrations
```sh
python manage.py migrate
```

## 8. (Optional) Create a Superuser
```sh
python manage.py createsuperuser
```

## 9. Collect Static Files (if needed)
```sh
python manage.py collectstatic
```

## 10. Download the Pre-trained Model
- Download the pre-trained model file (e.g., `yolov8x.pt`) from the provided link or release page.
- Place it in the `models/` directory (or as specified in the code).
- If the file is missing, the system will prompt you with instructions.

## 11. Run the Development Server
```sh
python manage.py runserver
```

---

## Notes on Caches, Migrations, and Model Files
- **Migrations:** Migration scripts are tracked in version control. Only cache files (`__pycache__`, `*.pyc`) inside `migrations/` are ignored.
- **Caches:** All Python cache files (`__pycache__`, `*.pyc`) are ignored globally. No cache or temporary files are committed.
- **Database:** Never commit your database or SQL dumps. Each user sets up their own DB.
- **Media/Static:** User-uploaded files and generated static files are not committed. Use `collectstatic` to generate static files as needed.
- **Model Files:** Large pre-trained model files are not committed. Download them as needed.

---

## Example .env File
Create a `.env` file in your project root with the following content:

```
DB_NAME=yourdbname
DB_USER=yourdbuser
DB_PASSWORD=yourdbpassword
DB_HOST=localhost
DB_PORT=3306
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

---

## Troubleshooting
- If you encounter issues with dependencies, ensure you are using Python 3.11.6.
- If migrations fail, check your database connection and credentials.
- If the model file is missing, follow the prompt to download it.
- For image processing or other system-level dependencies, see the project documentation for additional requirements. 