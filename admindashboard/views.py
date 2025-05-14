import os
import tempfile
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import logout
from ultralytics import YOLO
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .models import Family, Species
from .forms import FamilyForm, SpeciesForm
from django.http import JsonResponse

# Load the YOLO model pretrained (or fine-tuned) for migratory birds.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Update the model path to use the latest trained weights
model_path = os.path.join(BASE_DIR, "runs", "detect", "train4", "weights", "best.pt")

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
        results = model(temp_path, conf=0.5, iou=0.8)
        
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