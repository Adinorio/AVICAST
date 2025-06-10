# AVICAST Web Application

A Django-based web application for bird identification and management, featuring real-time bird detection using YOLOv8.

## Features

- Real-time bird detection using YOLOv8
- Bird species management system
- Family and species categorization
- Admin dashboard for data management
- RESTful API endpoints
- Responsive web interface

## Login tutorial

- **User ID:**
```python
010101
```
- **Password:**
```python
Avicast123
```

1. **Login** using the super admin account stated above to access the user management system, and then create a new user in the user management tab.
2. **Use** the ID and password of your new user as **Admin** or **Field worker** to access the main website.

## Quick Setup Guide

1. **Clone the repository:**
```bash
git clone <repository-url>
cd Web-Development
```

2. **Install MariaDB:**
   - Download and install MariaDB from [MariaDB Downloads](https://mariadb.org/download/)
   - During installation:
     - Set root password as: `root`
     - Set port as: `3306`
   - Create a new database named `avicast`

3. **Configure Database Settings:**
   - The database settings are already configured in the project:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'admin5.0_db',
        'USER': 'root',
        'PASSWORD': 'root',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}
```

4. **Download Required Files:**
   - Download files from the Google Drive link
   - Paste all downloaded files into the cloned repository folder

5. **Run Setup:**
```bash
python setup
```

6. **Start the Application:**
```bash
python run
```

If you encounter any issues:
- Check MariaDB configuration (password, port, database name)
- If database migrations are needed, run:
```bash
python migrate
```

## Detailed Setup Instructions

### Prerequisites
- Python 3.11.6
- MariaDB
- Git
- CUDA-capable GPU (recommended for model training)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Web-Development
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Unix/MacOS
source venv/bin/activate
```

3. Install dependencies:
   - For basic usage (testing the system):
   ```bash
   pip install -r requirements-base.txt
   ```
   - For development (including model training):
   ```bash
   pip install -r requirements-dev.txt
   ```

4. Set up the database:
   - Create a MySQL database
```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'admin5.0_db',
        'USER': 'root',
        'PASSWORD': 'root',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}
```
   # Edit .env with your database settings
   ```
   - Run migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. Run the development server:
```bash
python manage.py runserver
```

## Model Usage

The system uses YOLOv8 for bird detection. Two model options are available:

1. Custom-trained model (Chinese Egret) - Located at `runs/detect/train4/weights/best.pt`
2. Base YOLOv8x model - Located at `models/yolov8x.pt`

The system will automatically use the custom model if available, otherwise fall back to the base model.

### For Model Training (Optional)
If you want to train your own model:
1. Install the development requirements: `pip install -r requirements-dev.txt`
2. Prepare your dataset in YOLO format
3. Configure training parameters in `bird_detection/train.py`
4. Run the training script:
```bash
python bird_detection/train.py
```

## Project Structure

```
Web-Development/
├── admindashboard/     # Main application
├── bird_detection/     # Model training and inference
├── models/            # Pre-trained models
├── runs/             # Training outputs
├── static/           # Static files
├── templates/        # HTML templates
└── manage.py         # Django management script
```

## Database Management

- Migration files are included in the repository
- Each user should run migrations locally
- Database files are gitignored to prevent conflicts

## Troubleshooting

If you encounter any issues:

1. Database Issues:
   - Verify MariaDB is running
   - Check database connection settings
   - Ensure database `avicast` exists
   - Verify root password is set to `root`
   - Confirm port is set to `3306`

2. Model Loading Issues:
   - Ensure PyTorch and CUDA are properly installed
   - Check if model files exist in correct locations
   - Verify model file permissions
   - https://drive.google.com/drive/folders/1xgaO4Ntb0zNHbXZdZwKgza9AL0xpnjVq?usp=drive_link

3. General Issues:
   - Check if all required packages are installed
   - Verify Python version (3.11.6 recommended)
   - Check Django logs for detailed error messages

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
