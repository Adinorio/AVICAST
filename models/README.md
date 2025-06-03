# Bird Identification Models

This directory contains the pre-trained models for bird identification.

## Available Models

- `trained_model.pt`: The pre-trained model for bird identification
  - This model is included in the repository and should be used by default
  - No additional training is required to use this model

## Model Training (Optional)

If you want to train your own model:

1. Install development requirements:
```bash
pip install -r requirements-dev.txt
```

2. Prepare your dataset:
   - Place your training images in the `dataset/train/` directory
   - Place your validation images in the `dataset/val/` directory
   - Follow the dataset structure guidelines in `dataset/README.md`

3. Train the model:
```bash
python train.py --data dataset/data.yaml --epochs 100 --batch-size 16
```

4. The trained model will be saved in `runs/train/exp/weights/best.pt`

## Model Usage

The system will automatically use the pre-trained model (`trained_model.pt`) for bird identification. No additional setup is required.

If you want to use your own trained model:
1. Copy your trained model to this directory
2. Update the model path in your settings

## Troubleshooting

If you encounter any issues:
1. Ensure the model file exists in this directory
2. Check if you have the required dependencies installed
3. Verify your image format and size match the model's requirements 