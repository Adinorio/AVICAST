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

## Project Setup & File Management

### What's Not Tracked by Git (and Why)

The following files and folders are **not tracked** by git (see `.gitignore`):

- **Virtual environments:**  
  `AVICAST_WEB_311/`, `venv/`, `env/`, `.venv/`, etc.  
  _Reason: These are machine-specific and can be recreated using `requirements.txt`._
- **Compiled Python files and caches:**  
  `__pycache__/`, `*.pyc`, etc.  
  _Reason: These are auto-generated and not needed in version control._
- **Database files:**  
  `db.sqlite3`, `*.sql`, `*.sql.gz`  
  _Reason: Databases are environment-specific and can be recreated via migrations or dumps._
- **Media, static, and collected static files:**  
  `media/`, `static/`, `staticfiles/`  
  _Reason: These are generated or user-uploaded content, not source code._
- **IDE/editor settings:**  
  `.vscode/`, `.idea/`, etc.  
  _Reason: These are user-specific._
- **Environment variables:**  
  `.env`  
  _Reason: Contains sensitive info; use `.env.example` as a template._
- **Model files, datasets, and training outputs:**  
  `models/`, `runs/`, `dataset/`, `*.pt`, `*.pth`, `*.h5`  
  _Reason: These are large, binary, or generated files. Download or generate them separately._
- **Large archives:**  
  `*.zip`, `*.tar.gz`, `*.tar`, `*.7z`  
  _Reason: Large files should not be in git; download as needed._

#### Migration Scripts

- **Migration scripts** (e.g., `app_name/migrations/0001_initial.py`) **are tracked**.  
  Only migration cache files (like `__pycache__` or `*.pyc` in migrations) are ignored.

---

### What You Need to Download or Set Up Separately

After cloning the repo, you'll need to:

1. **Create a virtual environment**  
   (e.g., `python -m venv venv`)
2. **Install dependencies**  
   - For runtime/inference:  
     `pip install -r requirements.txt`
   - For training (if needed):  
     `pip install -r requirements-train.txt`
3. **Set up your environment variables**  
   - Copy `.env.example` to `.env` and fill in your values.
4. **Download or generate required files:**  
   - **Models:** Place pre-trained or custom model files in the `models/` directory.
   - **Datasets:** Place datasets in the `dataset/` directory if needed.
   - **Training outputs:** Place or generate training results in the `runs/` directory.
5. **Set up the database:**  
   - Run migrations:  
     `python manage.py migrate`
   - (Optional) Load initial data if provided.
6. **Collect static files (if needed):**  
   `python manage.py collectstatic`
7. **Run the server:**  
   `python manage.py runserver`

---

### Example Directory Structure (after setup)

```
your-project/
├── app1/
├── app2/
├── models/           # <--- Downloaded/added separately
├── runs/             # <--- Training outputs, not tracked
├── dataset/          # <--- Datasets, not tracked
├── manage.py
├── requirements.txt
├── requirements-train.txt
├── .env              # <--- Your local config, not tracked
├── .env.example      # <--- Template for .env
├── .gitignore
└── ...
```

---

### Notes

- **Never commit large files, datasets, or model weights to git.**  
  Use the provided folders and download or generate them as needed.
- **If you need to share large files, use cloud storage or a dedicated file server.**
- **If you need to clean your git history of large files, see the [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/) instructions.**

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