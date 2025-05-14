import os
os.environ['ULTRALYTICS_DATASET_DIR'] = os.path.abspath('dataset')
import zipfile
from ultralytics.data.utils import check_det_dataset

def extract_roboflow_dataset(zip_path, extract_to='dataset'):
    """
    Extract and organize Roboflow dataset export.
    """
    if not os.path.exists(extract_to):
        os.makedirs(extract_to)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print(f"Dataset extracted to {extract_to}")
    return extract_to

def fix_roboflow_structure():
    import yaml
    # Rename 'valid' to 'val' if it exists
    valid_dir = os.path.join('dataset', 'valid')
    val_dir = os.path.join('dataset', 'val')
    if os.path.exists(valid_dir):
        os.rename(valid_dir, val_dir)
    # Fix data.yaml paths
    yaml_path = os.path.join('dataset', 'data.yaml')
    if os.path.exists(yaml_path):
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        # Update paths
        if 'val' in data and 'valid' in data['val']:
            data['val'] = data['val'].replace('valid', 'val')
        if 'train' in data and '../' in data['train']:
            data['train'] = data['train'].replace('../', '')
        if 'test' in data and '../' in data['test']:
            data['test'] = data['test'].replace('../', '')
        with open(yaml_path, 'w') as f:
            yaml.dump(data, f)
        print("Fixed data.yaml paths and renamed 'valid' to 'val'.")

def prepare_dataset():
    """
    Verifies the dataset structure and checks the data.yaml file.
    """
    base_dir = 'dataset'
    yaml_path = os.path.join(base_dir, 'data.yaml')
    check_det_dataset(yaml_path)
    print(f"Dataset structure and data.yaml verified!")

def verify_annotations():
    """
    Verify that all images have corresponding annotation files
    and that annotations are in the correct format.
    """
    import glob
    for split in ['train', 'val', 'test']:
        img_dir = os.path.join('dataset', split, 'images')
        label_dir = os.path.join('dataset', split, 'labels')
        if not os.path.exists(img_dir) or not os.path.exists(label_dir):
            print(f"Warning: {img_dir} or {label_dir} does not exist.")
            continue
        for img_path in glob.glob(os.path.join(img_dir, '*')):
            if os.path.splitext(img_path)[1].lower() in ['.jpg', '.jpeg', '.png']:
                label_path = os.path.join(label_dir, os.path.splitext(os.path.basename(img_path))[0] + '.txt')
                if not os.path.exists(label_path):
                    print(f"Warning: No label file found for {img_path}")
                    continue
                with open(label_path, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        try:
                            class_id, *coords = line.strip().split()
                            if len(coords) != 4:
                                print(f"Warning: Invalid number of coordinates in {label_path}, line {line_num}")
                            if not all(0 <= float(x) <= 1 for x in coords):
                                print(f"Warning: Coordinates out of range in {label_path}, line {line_num}")
                        except ValueError:
                            print(f"Warning: Invalid label format in {label_path}, line {line_num}")

if __name__ == '__main__':
    roboflow_zip = 'bird_detection/chinese_egret_dataset.zip'  # Your Roboflow export file
    if os.path.exists(roboflow_zip):
        extract_roboflow_dataset(roboflow_zip)
        fix_roboflow_structure()
        prepare_dataset()
        verify_annotations()
    else:
        print(f"Please place your Roboflow export file as '{roboflow_zip}' in the current directory") 