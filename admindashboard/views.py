import os
import tempfile
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import logout
from ultralytics import YOLO

# Load the YOLO model pretrained (or fine-tuned) for migratory birds.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_path = os.path.join(BASE_DIR, "models", "yolov8x.pt")

model = YOLO(model_path)

def dashboard_view(request):
    return render(request, "admindashboard/dashboard.html")

def logout_view(request):
    logout(request)
    return redirect('superadminloginapp:login')

def bird_identification_view(request):
    # Renders the bird identification page.
    return render(request, "admindashboard/bird_identification.html")

@csrf_exempt
def process_bird_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        # Get image file from request
        image_file = request.FILES['image']
        
        # Create a temporary file to store the uploaded image
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_path = temp_file.name
            for chunk in image_file.chunks():
                temp_file.write(chunk)
        
        # Run inference with YOLO v8 on the temporary image file.
        results = model(temp_path)
        
        # Process results
        detections = []
        for result in results:
            for box in result.boxes:
                detections.append({
                    'class': result.names[int(box.cls[0])],  # Class name (species)
                    'confidence': float(box.conf[0]),  # Confidence score
                    'coordinates': box.xyxy[0].tolist()  # Bounding box coordinates
                })
        
        # Clean up temporary file
        os.remove(temp_path)

        # Return JSON response with detections
        return JsonResponse({'detections': detections})

    return JsonResponse({'error': 'Invalid request'}, status=400)
