from pathlib import Path
import os
import sys
import tempfile
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import logout
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .models import Family, Species
from .forms import FamilyForm, SpeciesForm
from django.http import JsonResponse
import torch
from ultralytics.nn.tasks import DetectionModel
from ultralytics.nn.modules.conv import Conv, Concat
from ultralytics.nn.modules.block import C2f, SPPF, Bottleneck, DFL
from ultralytics.nn.modules.head import Detect
from torch.nn.modules.container import Sequential, ModuleList
from torch.nn.modules.conv import Conv2d
from torch.nn.modules.batchnorm import BatchNorm2d
from torch.nn.modules.activation import SiLU
from torch.nn.modules.upsampling import Upsample
from torch.nn.modules.pooling import MaxPool2d
from torch.nn.modules.linear import Linear

# Get the base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Update the model paths to use Path objects
custom_model_path = BASE_DIR / "runs" / "detect" / "train4" / "weights" / "best.pt"
default_model_path = BASE_DIR / "models" / "yolov8x.pt"

model = None
model_load_error = None
model_in_use = None

def setup_model_loading():
    """Setup safe globals for model loading based on PyTorch version."""
    try:
        # Get PyTorch version
        torch_version = torch.__version__
        major_version = int(torch_version.split('.')[0])
        minor_version = int(torch_version.split('.')[1])

        # Define all required safe globals
        safe_globals = [
            DetectionModel,
            Conv,
            Concat,
            C2f,
            SPPF,
            Bottleneck,
            DFL,
            Detect,
            Sequential,
            ModuleList,
            Conv2d,
            BatchNorm2d,
            SiLU,
            Upsample,
            MaxPool2d,
            Linear
        ]

        # For PyTorch 2.6 and above
        if major_version >= 2 and minor_version >= 6:
            if hasattr(torch.serialization, 'add_safe_globals'):
                torch.serialization.add_safe_globals(safe_globals)
            else:
                # Fallback for older PyTorch versions
                import warnings
                warnings.warn("PyTorch version doesn't support add_safe_globals. Using alternative loading method.")
                return False
        return True
    except Exception as e:
        print(f"Error setting up model loading: {str(e)}")
        return False

# Check which model file exists and set the path accordingly
if custom_model_path.exists():
    model_path = str(custom_model_path)
    model_in_use = "Custom-trained model (Chinese Egret)"
elif default_model_path.exists():
    model_path = str(default_model_path)
    model_in_use = "Base YOLOv8x model (generic)"
else:
    model_path = None
    model_load_error = (
        f"No model file found. Please provide either a custom-trained model at '{custom_model_path}' "
        f"or a base model at '{default_model_path}'. See the README for instructions."
    )

if model_path and not model_load_error:
    try:
        from ultralytics import YOLO
        
        # Setup model loading with safe globals
        use_safe_globals = setup_model_loading()
        
        # Load model with appropriate settings
        if use_safe_globals:
            model = YOLO(model_path, task='detect')
        else:
            # Fallback method for older PyTorch versions
            model = YOLO(model_path, task='detect', weights_only=False)
            
    except ImportError:
        model_load_error = (
            "The 'ultralytics' package is not installed. If you only want to run inference, make sure you installed only the required packages. "
            "If you want to train or update the model, install training dependencies with: pip install -r requirements-dev.txt"
        )
    except Exception as e:
        model_load_error = f"Error loading YOLO model: {str(e)}"

def dashboard_view(request):
    return render(request, "admindashboard/dashboard.html")

def logout_view(request):
    logout(request)
    return redirect('superadminloginapp:login')

def bird_identification_view(request):
    # Renders the bird identification page, passing model info for frontend display.
    return render(request, "admindashboard/bird_identification.html", {"model_in_use": model_in_use, "model_load_error": model_load_error})

@csrf_exempt
def process_bird_image(request):
    if model_load_error:
        return JsonResponse({'error': model_load_error}, status=500)
    if request.method == 'POST' and request.FILES.get('image'):
        # Get image file and selected model from request
        image_file = request.FILES['image']
        selected_model = request.POST.get('model', 'chinese_egret')
        
        # Create a temporary file to store the uploaded image
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_path = temp_file.name
            for chunk in image_file.chunks():
                temp_file.write(chunk)
        try:
            # Run inference with YOLO v8 on the temporary image file
            # Note: In a production environment, you would load different models based on the selection
            # For now, we'll use the same model but filter results based on the selected species
            results = model(temp_path, conf=0.5, iou=0.8)
            
            # Map model values to class names
            model_to_class = {
                'chinese_egret': 'Chinese Egret',
                'whiskered_tern': 'Whiskered Tern',
                'great_knot': 'Great Knot'
            }
            
            # Process results and filter by selected species
            detections = []
            for result in results:
                for box in result.boxes:
                    class_name = result.names[int(box.cls[0])]
                    # Only include detections for the selected species
                    if class_name == model_to_class[selected_model]:
                        detections.append({
                            'class': class_name,
                            'confidence': float(box.conf[0]),
                            'coordinates': box.xyxy[0].tolist()
                        })
            
        except Exception as e:
            os.remove(temp_path)
            return JsonResponse({'error': f'Error during model inference: {str(e)}'}, status=500)
            
        # Clean up temporary file
        os.remove(temp_path)
        # Return JSON response with detections
        return JsonResponse({'detections': detections})
    return JsonResponse({'error': 'Invalid request'}, status=400)

def bird_list(request):
    families = Family.objects.filter(is_archived=False)
    family_form = FamilyForm()
    species_form = SpeciesForm()
    return render(request, 'admindashboard/bird_list.html', {
        'families': families,
        'family_form': family_form,
        'species_form': species_form,
    })

@require_POST
def add_family(request):
    form = FamilyForm(request.POST)
    if form.is_valid():
        form.save()
    return redirect('birds:bird_list')

@require_POST
def add_species(request, family_id):
    family = get_object_or_404(Family, id=family_id)
    form = SpeciesForm(request.POST)
    if form.is_valid():
        sp = form.save(commit=False)
        sp.family = family
        sp.save()
        data = {'id': sp.id, 'name': sp.name, 'scientific_name': sp.scientific_name}
        return JsonResponse({'success': True, 'species': data})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)

@require_POST
def toggle_family_archive(request, family_id):
    fam = get_object_or_404(Family, id=family_id)
    fam.is_archived = not fam.is_archived
    fam.save()
    return JsonResponse({'success': True, 'archived': fam.is_archived})

@require_POST
def toggle_species_archive(request, species_id):
    sp = get_object_or_404(Species, id=species_id)
    sp.is_archived = not sp.is_archived
    sp.save()
    return JsonResponse({'success': True, 'archived': sp.is_archived})