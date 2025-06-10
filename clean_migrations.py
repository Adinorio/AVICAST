import os
import re

def clean_migrations():
    project_root = os.getcwd()
    for root, dirs, files in os.walk(project_root):
        if 'migrations' in dirs:
            migrations_path = os.path.join(root, 'migrations')
            for file_name in os.listdir(migrations_path):
                if file_name.endswith('.py') and file_name != '__init__.py':
                    file_path = os.path.join(migrations_path, file_name)
                    print(f"Deleting: {file_path}")
                    os.remove(file_path)
    print("Migration files (excluding __init__.py) cleaned up.")

if __name__ == "__main__":
    clean_migrations() 