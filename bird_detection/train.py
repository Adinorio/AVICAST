from ultralytics import YOLO
import os
print('Current working directory:', os.getcwd())
print('Contents of dataset directory:', os.listdir('dataset'))
from roboflow import Roboflow
import torch
os.environ['ULTRALYTICS_DATASET_DIR'] = os.path.abspath('dataset')

def train_model():
    # Initialize YOLO model with YOLOv8x
    model = YOLO('yolov8x.pt')  # Load YOLOv8x model for better accuracy
    
    # Training parameters optimized for YOLOv8x
    training_args = {
        'data': 'dataset/data.yaml',  # Path to data config file
        'epochs': 100,  # Number of training epochs
        'imgsz': 640,  # Image size
        'batch': 8,  # Reduced batch size for YOLOv8x (larger model)
        'patience': 50,  # Early stopping patience
        'device': '0' if torch.cuda.is_available() else 'cpu',  # Use GPU if available
        'workers': 8,  # Number of worker threads
        'project': 'chinese_egret_detection',  # Project name
        'name': 'train',  # Experiment name
        'exist_ok': True,  # Overwrite existing experiment
        'pretrained': True,  # Use pretrained weights
        'optimizer': 'auto',  # Optimizer (SGD, Adam, etc.)
        'verbose': True,  # Print verbose output
        'seed': 42,  # Random seed
        'deterministic': True,  # Deterministic training
        'amp': True,  # Automatic Mixed Precision for better performance
        'lr0': 0.001,  # Initial learning rate
        'lrf': 0.01,  # Final learning rate
        'momentum': 0.937,  # SGD momentum
        'weight_decay': 0.0005,  # Optimizer weight decay
        'warmup_epochs': 3.0,  # Warmup epochs
        'warmup_momentum': 0.8,  # Warmup momentum
        'warmup_bias_lr': 0.1,  # Warmup bias learning rate
        'box': 7.5,  # Box loss gain
        'cls': 0.5,  # Class loss gain
        'dfl': 1.5,  # Distribution Focal Loss gain
    }
    
    # Start training
    results = model.train(**training_args)
    
    # Save the trained model
    model.save('chinese_egret_model.pt')
    
    return results

def deploy_to_roboflow(api_key, workspace_name, project_ids, model_name="chinese_egret_model"):
    """
    Deploy the trained model to Roboflow.
    
    Args:
        api_key (str): Your Roboflow API key
        workspace_name (str): Your Roboflow workspace name
        project_ids (list): List of project IDs to deploy to
        model_name (str): Name for the model in Roboflow
    """
    try:
        # Initialize Roboflow
        rf = Roboflow(api_key=api_key)
        workspace = rf.workspace(workspace_name)
        
        # Deploy the model
        workspace.deploy_model(
            model_type="yolov8",
            model_path="./runs/train/weights",
            project_ids=project_ids,
            model_name=model_name,
            filename="best.pt"  # Use the best weights from training
        )
        print(f"Model successfully deployed to Roboflow as '{model_name}'")
    except Exception as e:
        print(f"Error deploying model to Roboflow: {str(e)}")

if __name__ == '__main__':
    # Train the model
    results = train_model()
    
    # Deploy to Roboflow (uncomment and fill in your details)
    # deploy_to_roboflow(
    #     api_key="YOUR_API_KEY",
    #     workspace_name="YOUR_WORKSPACE",
    #     project_ids=["YOUR_PROJECT_ID"],
    #     model_name="chinese_egret_model"
    # ) 