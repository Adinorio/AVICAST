from pathlib import Path
import os
import sys
import tempfile
import models
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import logout
from django.views.decorators.http import require_POST
from .models import Family, Species, Site, BirdDetection
from .forms import FamilyForm, SpeciesForm, SiteForm
from django.contrib import messages
import json
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
from django.db.models import Count, Avg, Max, Min
from django.db.models.functions import TruncMonth, TruncYear
from django.utils import timezone
from datetime import timedelta

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
print("Checking for model files...")  # Debug log
if custom_model_path.exists():
    print(f"Found custom model at: {custom_model_path}")  # Debug log
    model_path = str(custom_model_path)
    model_in_use = "Custom-trained model (Chinese Egret)"
elif default_model_path.exists():
    print(f"Found default model at: {default_model_path}")  # Debug log
    model_path = str(default_model_path)
    model_in_use = "Base YOLOv8x model (generic)"
else:
    print("No model files found!")  # Debug log
    model_path = None
    model_load_error = (
        f"No model file found. Please provide either a custom-trained model at '{custom_model_path}' "
        f"or a base model at '{default_model_path}'. See the README for instructions."
    )

if model_path and not model_load_error:
    try:
        print("Attempting to import YOLO...")  # Debug log
        from ultralytics import YOLO
        
        # Setup model loading with safe globals
        print("Setting up model loading...")  # Debug log
        use_safe_globals = setup_model_loading()
        
        # Load model with appropriate settings
        print(f"Loading model from: {model_path}")  # Debug log
        if use_safe_globals:
            model = YOLO(model_path, task='detect')
        else:
            # Fallback method for older PyTorch versions
            model = YOLO(model_path, task='detect', weights_only=False)
        print("Model loaded successfully!")  # Debug log
            
    except ImportError as e:
        print(f"Import error: {str(e)}")  # Debug log
        model_load_error = (
            "The 'ultralytics' package is not installed. If you only want to run inference, make sure you installed only the required packages. "
            "If you want to train or update the model, install training dependencies with: pip install -r requirements-dev.txt"
        )
    except Exception as e:
        print(f"Error loading model: {str(e)}")  # Debug log
        model_load_error = f"Error loading YOLO model: {str(e)}"

def dashboard_view(request):
    """Main dashboard view"""
    return render(request, 'admindashboard/dashboard.html')

def logout_view(request):
    """Logout view"""
    logout(request)
    return redirect('superadminloginapp:login')

def bird_identification_view(request):
    """Bird identification view (legacy name)"""
    return render(request, 'admindashboard/bird_identification.html', {"model_in_use": model_in_use, "model_load_error": model_load_error})

def identify_bird(request):
    """Bird identification view (new name)"""
    return render(request, 'admindashboard/bird_identification.html')

@csrf_exempt
def process_bird_image(request):
    print("Starting image processing...")  # Debug log
    if model_load_error:
        print(f"Model load error: {model_load_error}")  # Debug log
        return JsonResponse({'error': model_load_error}, status=500)
    
    if request.method == 'POST' and request.FILES.get('image'):
        print("Received POST request with image")  # Debug log
        # Get image file and selected model from request
        image_file = request.FILES['image']
        selected_model = request.POST.get('model', 'chinese_egret')
        print(f"Selected model: {selected_model}")  # Debug log
        
        # Create a temporary file to store the uploaded image
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_path = temp_file.name
            for chunk in image_file.chunks():
                temp_file.write(chunk)
        print(f"Saved image to temporary file: {temp_path}")  # Debug log
        
        try:
            print("Starting model inference...")  # Debug log
            # Run inference with YOLO v8 on the temporary image file
            results = model(temp_path, conf=0.25, iou=0.4)
            print(f"Model inference complete. Results: {results}")  # Debug log
            
            # Map model values to class names
            model_to_class = {
                'chinese_egret': 'chinese_egret',
                'whiskered_tern': 'Whiskered Tern',
                'great_knot': 'Great Knot'
            }
            
            # Process results and filter by selected species
            detections = []
            for result in results:
                print(f"Processing result: {result}")  # Debug log
                for box in result.boxes:
                    class_name = result.names[int(box.cls[0])]
                    print(f"Detected class: {class_name}")  # Debug log
                    # Only include detections for the selected species
                    if class_name == model_to_class[selected_model]:
                        detections.append({
                            'class': class_name,
                            'confidence': float(box.conf[0]),
                            'coordinates': box.xyxy[0].tolist()
                        })
            
            print(f"Final detections: {detections}")  # Debug log
            
        except Exception as e:
            print(f"Error during processing: {str(e)}")  # Debug log
            os.remove(temp_path)
            return JsonResponse({'error': f'Error during model inference: {str(e)}'}, status=500)
            
        # Clean up temporary file
        os.remove(temp_path)
        # Return JSON response with detections
        return JsonResponse({'detections': detections})
    
    print("Invalid request received")  # Debug log
    return JsonResponse({'error': 'Invalid request'}, status=400)

def bird_list(request):
    """Main view for displaying bird families and species"""
    families = Family.objects.filter(is_archived=False).order_by('name')
    family_form = FamilyForm()
    species_form = SpeciesForm()
    
    context = {
        'families': families,
        'family_form': family_form,
        'species_form': species_form,
    }
    return render(request, 'admindashboard/bird_list.html', context)

@require_POST
def add_family(request):
    """Add a new bird family"""
    form = FamilyForm(request.POST)
    if form.is_valid():
        family = form.save(commit=False)
        family.is_archived = False
        family.save()
        messages.success(request, 'Family added successfully!')
    else:
        messages.error(request, 'Error adding family. Please check the form.')
    return redirect('admindashboard:bird_list')

@require_POST
def add_species(request, family_id):
    """Add a new species to a family"""
    family = get_object_or_404(Family, id=family_id)
    form = SpeciesForm(request.POST)
    
    if form.is_valid():
        species = form.save(commit=False)
        species.family = family
        species.is_archived = False
        species.save()
        messages.success(request, 'Species added successfully!')
    else:
        messages.error(request, 'Error adding species. Please check the form.')
    
    return redirect('admindashboard:bird_list')

def edit_family(request, family_id):
    """Edit an existing bird family"""
    family = get_object_or_404(Family, id=family_id)
    
    if request.method == 'POST':
        form = FamilyForm(request.POST, instance=family)
        if form.is_valid():
            form.save()
            messages.success(request, 'Family updated successfully!')
            return redirect('admindashboard:bird_list')
    else:
        form = FamilyForm(instance=family)
    
    return render(request, 'admindashboard/edit_family.html', {
        'form': form,
        'family': family
    })

def edit_species(request, species_id):
    """Edit an existing species"""
    species = get_object_or_404(Species, id=species_id)
    
    if request.method == 'POST':
        form = SpeciesForm(request.POST, instance=species)
        if form.is_valid():
            form.save()
            messages.success(request, 'Species updated successfully!')
            return redirect('admindashboard:bird_list')
    else:
        form = SpeciesForm(instance=species)
    
    return render(request, 'admindashboard/edit_species.html', {
        'form': form,
        'species': species
    })

@require_POST
def archive_family(request, family_id):
    """Archive a bird family"""
    family = get_object_or_404(Family, id=family_id)
    family.is_archived = True
    family.save()
    messages.success(request, 'Family archived successfully!')
    return redirect('admindashboard:bird_list')

@require_POST
def archive_species(request, species_id):
    """Archive a species"""
    species = get_object_or_404(Species, id=species_id)
    species.is_archived = True
    species.save()
    messages.success(request, 'Species archived successfully!')
    return redirect('admindashboard:bird_list')

@require_POST
def restore_family(request, family_id):
    """Restore an archived family"""
    family = get_object_or_404(Family, id=family_id)
    family.is_archived = False
    family.save()
    messages.success(request, 'Family restored successfully!')
    return redirect('admindashboard:bird_list')

@require_POST
def restore_species(request, species_id):
    """Restore an archived species"""
    species = get_object_or_404(Species, id=species_id)
    species.is_archived = False
    species.save()
    messages.success(request, 'Species restored successfully!')
    return redirect('admindashboard:bird_list')

def get_species(request, family_id):
    """Get all species for a family (AJAX endpoint)"""
    family = get_object_or_404(Family, id=family_id)
    species = Species.objects.filter(family=family, is_archived=False).order_by('name')
    data = [{
        'id': s.id,
        'name': s.name,
        'scientific_name': s.scientific_name,
        'iucn_status': s.iucn_status
    } for s in species]
    return JsonResponse(data, safe=False)

def help_view(request):
    """Help page view"""
    return render(request, "admindashboard/help.html")

def image_processing_view(request):
    return render(request, 'admindashboard/image_processing.html')

def image_processing_next_view(request):
    return render(request, 'admindashboard/image_processing_next.html')

def review_dashboard_view(request):
    return render(request, 'admindashboard/review_dashboard.html')

def site_list(request):
    """View for displaying all sites and their details."""
    sites = Site.objects.all().order_by('name')
    print(f"Fetched {len(sites)} sites for site_list view.") # Debugging log
    context = {
        'sites': sites,
    }
    return render(request, 'admindashboard/site.html', context)

def site_detail(request, site_id):
    """View for displaying detailed bird census data for a specific site and year."""
    site = get_object_or_404(Site, id=site_id)
    
    # Get all species to display all 96 birds, even if no detections
    all_species = Species.objects.filter(is_archived=False).order_by('common_name')

    # Get the current year or a selected year (for now, let's use the current year)
    current_year = timezone.now().year

    # Aggregate bird detections for the selected site and year
    bird_data = []
    for species in all_species:
        count = BirdDetection.objects.filter(
            site=site,
            species=species,
            detection_date__year=current_year
        ).count()
        bird_data.append({
            'species_name': species.common_name,
            'count': count
        })

    context = {
        'site': site,
        'year': current_year,
        'bird_data': bird_data,
    }
    return render(request, 'admindashboard/site_detail.html', context)

def add_site(request):
    """Add a new site"""
    print("Received request to add site.") # Debugging log
    if request.method == 'POST':
        form = SiteForm(request.POST, request.FILES)
        print(f"Form received: {request.POST}") # Debugging log
        if form.is_valid():
            print("Form is valid.") # Debugging log
            site = form.save(commit=False)
            site.save()
            print(f"Site saved: {site.name} ({site.code})") # Debugging log
            messages.success(request, 'Site added successfully!')
            return JsonResponse({'success': True, 'message': 'Site added successfully!'})
        else:
            errors = form.errors.as_json()
            print(f"Form is NOT valid. Errors: {form.errors}") # Debugging log
            messages.error(request, 'Error adding site. Please check the form.')
            return JsonResponse({'success': False, 'message': 'Error adding site. Please check the form.', 'errors': errors}, status=400)
    print("Invalid request method for add site.") # Debugging log
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

def edit_site(request, site_id):
    """Edit an existing site"""
    site = get_object_or_404(Site, id=site_id)
    
    print(f"Received request to edit site ID: {site_id}") # Debugging log
    if request.method == 'POST':
        form = SiteForm(request.POST, request.FILES, instance=site)
        print(f"Form received for edit: {request.POST}") # Debugging log
        if form.is_valid():
            print("Edit form is valid.") # Debugging log
            form.save()
            print(f"Site updated: {site.name} ({site.code})") # Debugging log
            messages.success(request, 'Site updated successfully!')
            return JsonResponse({'success': True, 'message': 'Site updated successfully!'})
        else:
            errors = form.errors.as_json()
            print(f"Edit form is NOT valid. Errors: {form.errors}") # Debugging log
            messages.error(request, 'Error updating site. Please check the form.')
            return JsonResponse({'success': False, 'message': 'Error updating site. Please check the form.', 'errors': errors}, status=400)
    else:
        print("Received GET request for edit_site view - usually not intended for direct access.")
        return JsonResponse({'success': False, 'message': 'GET request not supported for this endpoint.'}, status=405)

@require_POST
def delete_site(request, site_id):
    """Delete a site"""
    site = get_object_or_404(Site, id=site_id)
    site.delete()
    messages.success(request, 'Site deleted successfully!')
    return redirect('admindashboard:site_list')

def get_species_distribution():
    """Generate species distribution report"""
    # Get species distribution by family
    family_distribution = Family.objects.filter(is_archived=False).annotate(
        species_count=Count('species', filter=models.Q(species__is_archived=False))
    ).values('name', 'species_count')

    # Get species distribution by site
    site_distribution = Site.objects.filter(status='active').annotate(
        detection_count=Count('birddetection')
    ).values('name', 'detection_count')

    return {
        'family_distribution': list(family_distribution),
        'site_distribution': list(site_distribution)
    }

def get_population_trends():
    """Generate population trends report"""
    # Get monthly detection trends
    monthly_trends = BirdDetection.objects.annotate(
        month=TruncMonth('detection_date')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')

    # Get species-wise trends
    species_trends = BirdDetection.objects.values(
        'species__common_name'
    ).annotate(
        total_detections=Count('id'),
        avg_confidence=Avg('confidence')
    ).order_by('-total_detections')

    return {
        'monthly_trends': list(monthly_trends),
        'species_trends': list(species_trends)
    }

def get_forecasting_data():
    """Generate forecasting data for optimal field work timing"""
    # Get historical detection patterns
    last_year = timezone.now() - timedelta(days=365)
    monthly_patterns = BirdDetection.objects.filter(
        detection_date__gte=last_year
    ).annotate(
        month=TruncMonth('detection_date')
    ).values('month').annotate(
        detection_count=Count('id'),
        avg_confidence=Avg('confidence')
    ).order_by('month')

    # Get site-wise patterns
    site_patterns = BirdDetection.objects.filter(
        detection_date__gte=last_year
    ).values(
        'species__family__name'
    ).annotate(
        total_detections=Count('id'),
        avg_confidence=Avg('confidence')
    ).order_by('-total_detections')

    return {
        'monthly_patterns': list(monthly_patterns),
        'site_patterns': list(site_patterns)
    }

def get_site_analysis():
    """Generate site analysis report"""
    # Get site statistics
    site_stats = Site.objects.filter(status='active').annotate(
        total_detections=Count('birddetection'),
        unique_species=Count('birddetection__species', distinct=True),
        avg_confidence=Avg('birddetection__confidence')
    ).values('name', 'total_detections', 'unique_species', 'avg_confidence')

    # Get species distribution per site
    species_per_site = BirdDetection.objects.values(
        'species__common_name', 'site__name'
    ).annotate(
        count=Count('id')
    ).order_by('site__name', '-count')

    return {
        'site_stats': list(site_stats),
        'species_per_site': list(species_per_site)
    }

def report_view(request):
    """View for the statistical reports page"""
    report_type = request.GET.get('type')
    
    if report_type:
        # Handle AJAX request for report data
        if report_type == 'distribution':
            data = get_species_distribution()
        elif report_type == 'trends':
            data = get_population_trends()
        elif report_type == 'forecasting':
            data = get_forecasting_data()
        elif report_type == 'site_analysis':
            data = get_site_analysis()
        else:
            data = None
            
        return JsonResponse(data if data else {'error': 'Invalid report type'})
    
    # Regular page load - render the template
    context = {
        'page_title': 'Statistical Reports',
        'active_page': 'reports'
    }
    return render(request, 'admindashboard/report.html', context)

def get_site_years(request, site_id):
    """API to get available years for a given site with bird detections."""
    site = get_object_or_404(Site, id=site_id)
    years = BirdDetection.objects.filter(site=site).annotate(year=TruncYear('detection_date')).values_list('year', flat=True).distinct().order_by('-year')
    # Convert datetime.date objects to year integers
    year_list = [year.year for year in years if year is not None]
    return JsonResponse({'years': year_list})

def get_monthly_detections(request, site_id, year):
    """API to get monthly bird detection data for a specific site and year."""
    site = get_object_or_404(Site, id=site_id)
    detections = BirdDetection.objects.filter(
        site=site,
        detection_date__year=year
    ).annotate(
        month=TruncMonth('detection_date')
    ).values('month').annotate(
        total_detections=Count('id'),
        unique_species=Count('species', distinct=True)
    ).order_by('month')

    # Format for frontend
    monthly_data = []
    for entry in detections:
        monthly_data.append({
            'month_name': entry['month'].strftime('%B'), # Full month name
            'month_number': entry['month'].month,
            'total_detections': entry['total_detections'],
            'unique_species': entry['unique_species'],
        })
    return JsonResponse({'monthly_data': monthly_data})