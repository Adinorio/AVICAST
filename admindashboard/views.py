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
from .forms import FamilyForm, SpeciesForm, SiteForm, ImportDataForm
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
from django.conf import settings
import pandas as pd
from datetime import datetime
from .decorators import permission_required # Import the custom decorator
from src.apps.user_management.models import SystemLog  # Updated import path

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
    user = request.user if request.user.is_authenticated else None
    if user:
        SystemLog.objects.create(
            level='INFO',
            source='system.auth',
            message=f"User '{user.username}' logged out.",
            user=user,
            action='logout'
        )
    logout(request)
    return redirect('authentication:login')

@permission_required('view_image_processing')
def bird_identification_view(request):
    """Bird identification view (legacy name)"""
    return render(request, 'admindashboard/bird_identification.html', {"model_in_use": model_in_use, "model_load_error": model_load_error})

def identify_bird(request):
    """Bird identification view (new name)"""
    return render(request, 'admindashboard/bird_identification.html')

@permission_required('generate_data')
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

@permission_required('view_species_management')
def bird_list(request):
    """Main view for displaying bird families and species"""
    # Ensure specified bird families exist
    family_names = [
        "Ardeidae", "Anatidae", "Rallidae", "Recurvirostridae",
        "Charadriidae", "Scolopacidae", "Laridae", "Accipitridae",
        "Alcedinidae", "Hirundinidae", "Pandionidae", "Podicipedidae",
        "Rostratulidae"
    ]

    for family_name in family_names:
        Family.objects.get_or_create(name=family_name)

    families = Family.objects.filter(is_archived=False).order_by('name')
    
    # For now, let's just pass some example species if none exist for testing purposes
    example_species = Species.objects.filter(is_archived=False).order_by('common_name')


    context = {
        'families': families,
        'species': example_species, # Pass the species objects to the template
    }
    return render(request, 'admindashboard/bird_list.html', context)

@permission_required('modify_data')
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

@permission_required('modify_data')
@require_POST
@csrf_exempt
def add_species_view(request):
    """API to add a new bird species."""
    if request.method == 'POST':
        print(f"add_species_view: Received POST request. request.FILES: {request.FILES}") # Debug log
        form = SpeciesForm(request.POST, request.FILES)
        if form.is_valid():
            print("add_species_view: Form is valid.") # Debug log
            try:
                species = form.save()
                print(f"add_species_view: Species saved. Image path: {species.image.url if species.image else 'None'}") # Debug log
                return JsonResponse({'success': True, 'message': f'Bird species "{species.common_name}" added successfully!'})
            except Exception as e:
                print(f"add_species_view: Error saving species: {str(e)}") # Debug log
                return JsonResponse({'success': False, 'message': f'Error saving species: {str(e)}'}, status=500)
        else:
            print(f"add_species_view: Validation failed. Form errors: {form.errors}") # Debug log
            return JsonResponse({'success': False, 'message': 'Validation failed: ' + str(form.errors)}, status=400)
    print("add_species_view: Invalid request method.") # Debug log
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

@permission_required('modify_data')
@require_POST
@csrf_exempt
def edit_species_view(request, species_id):
    """API to edit an existing bird species."""
    species = get_object_or_404(Species, pk=species_id)
    if request.method == 'POST':
        print(f"edit_species_view: Received POST request for ID {species_id}. request.FILES: {request.FILES}") # Debug log
        form = SpeciesForm(request.POST, request.FILES, instance=species)
        if form.is_valid():
            print("edit_species_view: Form is valid.") # Debug log
            try:
                species = form.save()
                print(f"edit_species_view: Species updated. Image path: {species.image.url if species.image else 'None'}") # Debug log
                return JsonResponse({'success': True, 'message': f'Bird species "{species.common_name}" updated successfully!'})
            except Exception as e:
                print(f"edit_species_view: Error updating species: {str(e)}") # Debug log
                return JsonResponse({'success': False, 'message': f'Error updating species: {str(e)}'}, status=500)
        else:
            print(f"edit_species_view: Validation failed. Form errors: {form.errors}") # Debug log
            return JsonResponse({'success': False, 'message': 'Validation failed: ' + str(form.errors)}, status=400)
    print("edit_species_view: Invalid request method.") # Debug log
    return JsonResponse({'success': False, 'message': 'GET request not supported for this endpoint.'}, status=405)

def get_families_api(request):
    """API to get a list of active bird families."""
    families = Family.objects.filter(is_archived=False).values('id', 'name').order_by('name')
    return JsonResponse({'families': list(families)})

def get_conservation_statuses_api(request):
    """API to get available conservation status choices."""
    # Assuming Conservation Status is a predefined list or from a model field choices
    # For Species model, conservation_status is a CharField, so we define choices here
    STATUS_CHOICES = [
        "Least Concern", "Near Threatened", "Vulnerable", "Endangered",
        "Critically Endangered", "Extinct In The Wild", "Extinct"
    ]
    return JsonResponse({'statuses': STATUS_CHOICES})

def get_species_details_api(request, species_id):
    """API to get details for a specific species."""
    print(f"get_species_details_api: Received request for species_id: {species_id}") # Debug log
    try:
        species = get_object_or_404(Species, pk=species_id)
        print(f"get_species_details_api: Found species: {species.common_name} (ID: {species.id})") # Debug log
        details = {
            'id': species.id,
            'common_name': species.common_name,
            'scientific_name': species.scientific_name,
            'description': species.description,
            'family_id': species.family.id if species.family else None,
            'conservation_status': species.conservation_status,
            'image_url': species.image.url if species.image else None,
        }
        return JsonResponse({'details': details})
    except Exception as e:
        print(f"get_species_details_api: Error fetching species details for ID {species_id}: {str(e)}") # Debug log
        # Re-raise the exception or return a more specific error if needed
        raise # Re-raise to ensure 404 is still triggered by get_object_or_404 if not found

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

@permission_required('view_site_management')
def site_list(request):
    """View for displaying all sites and their details."""
    sites = Site.objects.all().order_by('name')
    print(f"Fetched {len(sites)} sites for site_list view.") # Debugging log
    context = {
        'sites': sites,
    }
    return render(request, 'admindashboard/site.html', context)

@permission_required('view_site_management')
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

@permission_required('add_sites')
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
            print(f"Site saved: {site.name}") # Debugging log
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
            print(f"Site updated: {site.name}") # Debugging log
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

@permission_required('view_report_management')
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
        'active_page': 'reports',
        'access_denied': getattr(request, 'access_denied', False),
        'denied_feature_name': getattr(request, 'denied_feature_name', ''),
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
    try:
        print(f"DEBUG: get_monthly_detections called for Site ID: {site_id}, Year: {year}")
        site = Site.objects.get(id=site_id)
        detections = BirdDetection.objects.filter(
            site=site,
            detection_date__year=year
        ).select_related('species', 'species__family').order_by('detection_date')

        print(f"DEBUG: Found {detections.count()} detections for Site {site_id} in {year}")

        monthly_data = []
        # Use a dictionary to store detections per month, then convert to list
        months_dict = {}

        for detection in detections:
            print(f"DEBUG: Processing detection ID: {detection.id}, Species: {detection.species.common_name}, Count: {detection.count}, Date: {detection.detection_date}")
            month_number = detection.detection_date.month
            month_name = datetime(year, month_number, 1).strftime('%B')

            if month_number not in months_dict:
                months_dict[month_number] = {
                    'month_number': month_number,
                    'month_name': month_name,
                    'total_detections': 0,
                    'unique_species': set(),
                    'species_data': {}
                }
            
            months_dict[month_number]['total_detections'] += detection.count
            months_dict[month_number]['unique_species'].add(detection.species.common_name)
            
            family_name = detection.species.family.name if detection.species.family else 'Uncategorized'
            print(f"DEBUG:   Family Name for {detection.species.common_name}: {family_name}")
            
            if family_name not in months_dict[month_number]['species_data']:
                months_dict[month_number]['species_data'][family_name] = []
            
            months_dict[month_number]['species_data'][family_name].append({
                'species_name': detection.species.common_name,
                'count': detection.count
            })
        
        # Convert set to list for JSON serialization and sort unique species
        for month_num in months_dict:
            months_dict[month_num]['unique_species'] = sorted(list(months_dict[month_num]['unique_species']))
            # Sort species within each family for consistent display
            for family in months_dict[month_num]['species_data']:
                months_dict[month_num]['species_data'][family].sort(key=lambda x: x['species_name'])

        # Convert dictionary to list and sort by month number
        monthly_data = sorted(list(months_dict.values()), key=lambda x: x['month_number'])

        return JsonResponse({'monthly_data': monthly_data})

    except Site.DoesNotExist:
        return JsonResponse({'error': 'Site not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def check_species_dependencies(request, species_id):
    """API to check if a species is being used in other features."""
    species = get_object_or_404(Species, pk=species_id)
    dependencies = []
    
    # Check if species is used in any bird detections
    detections = BirdDetection.objects.filter(species=species)
    if detections.exists():
        dependencies.append(f"Bird Detections ({detections.count()} records)")
    
    return JsonResponse({
        'dependencies': dependencies,
        'can_delete': len(dependencies) == 0
    })

@permission_required('modify_data')
@csrf_exempt
@require_POST
def delete_species(request, species_id):
    """API to delete a bird species and its associated image."""
    species = get_object_or_404(Species, pk=species_id)
    
    # Check dependencies first
    detections = BirdDetection.objects.filter(species=species)
    if detections.exists():
        return JsonResponse({
            'success': False,
            'message': 'Cannot delete species as it is being used in bird detections.'
        }, status=400)
    
    try:
        # Delete the image file if it exists
        if species.image:
            # Get the full path to the image file
            image_path = os.path.join(settings.MEDIA_ROOT, str(species.image))
            # Delete the file if it exists
            if os.path.isfile(image_path):
                os.remove(image_path)
        
        # Delete the species from the database
        species.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Bird species "{species.common_name}" deleted successfully!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting species: {str(e)}'
        }, status=500)

def import_data(request):
    if request.method == 'POST':
        form = ImportDataForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            sheet_name = form.cleaned_data.get('sheet_name')
            
            try:
                xls = pd.ExcelFile(excel_file)
                if sheet_name:
                    df_raw = xls.parse(sheet_name, header=None)
                else:
                    df_raw = xls.parse(xls.sheet_names[0], header=None)
                
                # Ensure a default family exists for species without explicit family data
                unknown_family, _ = Family.objects.get_or_create(name='Unknown Family', defaults={'description': 'For species without a specified family.'})

                # --- Step 1: Find Site Name and Year --- #
                site_year_cell = None
                site_name = 'Unknown Site' # Default if not found
                year = datetime.now().year # Default to current year if not found

                for r_idx, row in df_raw.iterrows():
                    for c_idx, cell_value in enumerate(row):
                        if pd.notna(cell_value) and isinstance(cell_value, str) and "DAGA" in cell_value.upper():
                            site_year_cell = cell_value.strip()
                            parts = site_year_cell.split()
                            if len(parts) >= 2 and parts[-1].isdigit():
                                year = int(parts[-1])
                                site_name = " ".join(parts[:-1])
                            else:
                                site_name = site_year_cell
                            print(f"DEBUG: Found Site/Year cell: '{site_year_cell}', Parsed Site: '{site_name}', Year: {year}")
                            break
                    if site_year_cell: break
                
                if not site_year_cell:
                    print("DEBUG: Site name and year (e.g., DAGA 2021) not found, using defaults.")

                # --- Step 2: Find Month Headers --- #
                header_row_idx = -1
                month_columns_info = {}
                for r_idx, row in df_raw.iterrows():
                    row_values = [str(v).upper().strip() if pd.notna(v) and isinstance(v, str) else v for v in row.tolist()]
                    print(f"DEBUG: Checking row {r_idx + 1} for month headers: {row_values}")
                    # Check for *full* month names as per user's latest image
                    if 'SEPTEMBER' in row_values and 'OCTOBER' in row_values and 'NOVEMBER' in row_values:
                        header_row_idx = r_idx
                        print(f"DEBUG: Found month header row at index: {header_row_idx + 1}")
                        for c_idx, val in enumerate(row_values):
                            if val == 'SEPTEMBER': month_columns_info[c_idx] = 9 # September
                            elif val == 'OCTOBER': month_columns_info[c_idx] = 10
                            elif val == 'NOVEMBER': month_columns_info[c_idx] = 11 # November
                        break
                
                if header_row_idx == -1 or not month_columns_info:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Could not find month headers (SEPTEMBE, OCTOBER, NOVEMBE) in the Excel file. Please ensure they are spelled correctly and without extra spaces.'
                    })

                # --- Step 3: Find SPECIES Column --- #
                species_col_idx = -1
                for r_idx_species_search, row_species_search in df_raw.head(10).iterrows():
                    row_values_species_search = [str(v).upper().strip() if pd.notna(v) and isinstance(v, str) else v for v in row_species_search.tolist()]
                    print(f"DEBUG: Checking row {r_idx_species_search + 1} for SPECIES header: {row_values_species_search}")
                    for c_idx, val in enumerate(row_values_species_search):
                        if isinstance(val, str) and val == 'SPECIES':
                            species_col_idx = c_idx
                            print(f"DEBUG: Found SPECIES column at index: {species_col_idx} in row {r_idx_species_search + 1}")
                            break
                    if species_col_idx != -1: break
                
                if species_col_idx == -1:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Could not find the SPECIES column in the Excel file. Please ensure a column is titled "SPECIES" (case-insensitive, no extra spaces).'
                    })

                if species_col_idx in month_columns_info:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Internal error: SPECIES column index overlaps with a month column index. Please check your Excel structure.'
                    })

                processed_data = []
                current_family_obj = None # Initialize current family

                # Define a mapping for common family names to scientific family names
                family_name_mapping = {
                    'HERONS AND EGRETS': 'Ardeidae',
                    # Add other mappings here as needed, e.g.:
                    # 'DUCKS AND GEESE': 'Anatidae',
                }

                for r_idx_actual in range(header_row_idx + 1, len(df_raw)):
                    row = df_raw.iloc[r_idx_actual]

                    if species_col_idx >= len(row):
                        print(f"DEBUG: Skipping row {r_idx_actual + 1}: SPECIES column index {species_col_idx} out of bounds for row with {len(row)} columns.")
                        continue

                    species_name_raw = row.iloc[species_col_idx]

                    # Check if this row is a family header
                    is_potential_family_header = False
                    if pd.notna(species_name_raw) and isinstance(species_name_raw, str) and species_name_raw.strip().isupper():
                        # Check if all month count cells in this row are empty or non-numeric
                        all_counts_empty = True
                        for col_idx_month in month_columns_info.keys():
                            if col_idx_month < len(row):
                                val = row.iloc[col_idx_month]
                                if pd.notna(val) and isinstance(val, (int, float)) and val > 0:
                                    all_counts_empty = False
                                    break
                        if all_counts_empty:
                            is_potential_family_header = True

                    if is_potential_family_header:
                        excel_family_name = species_name_raw.strip()
                        # Use the mapping to get the scientific family name
                        scientific_family_name = family_name_mapping.get(excel_family_name, excel_family_name)
                        
                        current_family_obj, created = Family.objects.get_or_create(name=scientific_family_name)
                        if created:
                            print(f"DEBUG: Created new family: {scientific_family_name} from Excel header '{excel_family_name}' at Excel row {r_idx_actual + 1}.")
                        else:
                            print(f"DEBUG: Identified existing family: {scientific_family_name} from Excel header '{excel_family_name}' at Excel row {r_idx_actual + 1}.")
                        
                        continue # Skip to next row, as this is a family header, not a species entry

                    if pd.isna(species_name_raw) or not isinstance(species_name_raw, str) or species_name_raw.strip() == '':
                        continue

                    species_name = species_name_raw.strip()
                    
                    for col_idx, month_number in month_columns_info.items():
                        if col_idx >= len(row):
                            print(f"DEBUG: Skipping column {col_idx} in row {r_idx_actual + 1}: Out of bounds.")
                            continue

                        count_value_candidate = row.iloc[col_idx]
                        
                        print(f"DEBUG: Processing Site: '{site_name}', Year: {year}, Row Index: {r_idx_actual + 1}")
                        print(f"DEBUG:   Species Name Raw: '{species_name_raw}'")
                        print(f"DEBUG:   Checking Month: {month_number} ({datetime(year, month_number, 1).strftime('%B')}), Column Index: {col_idx}, Value Candidate: '{count_value_candidate}', Type: {type(count_value_candidate)}")

                        count = 0
                        if pd.notna(count_value_candidate):
                            try:
                                count = int(count_value_candidate)
                            except ValueError:
                                error_msg = f"Data conversion error: Expected a number for count, but found non-numeric value '{count_value_candidate}' for species '{species_name}' in month {datetime(year, month_number, 1).strftime('%B')} of year {year} at Excel row {r_idx_actual + 1}. Please correct your Excel file." 
                                print(f"ERROR: {error_msg}")
                                return JsonResponse({'status': 'error', 'message': error_msg})
                            except TypeError:
                                error_msg = f"Data type error: Expected a number for count, but found incompatible type for '{count_value_candidate}' for species '{species_name}' in month {datetime(year, month_number, 1).strftime('%B')} of year {year} at Excel row {r_idx_actual + 1}. Please correct your Excel file." 
                                print(f"ERROR: {error_msg}")
                                return JsonResponse({'status': 'error', 'message': error_msg})

                        if count > 0:
                            try:
                                site, _ = Site.objects.get_or_create(
                                    name=site_name,
                                    defaults={'location': 'Unknown', 'status': 'Active'}
                                )

                                # Use current_family_obj if available, otherwise fallback to unknown_family
                                species_family = current_family_obj if current_family_obj else unknown_family
                                species, _ = Species.objects.get_or_create(
                                    common_name=species_name,
                                    defaults={'family': species_family, 'description': ''}
                                )
                                
                                BirdDetection.objects.create(
                                    site=site,
                                    species=species,
                                    detection_date=datetime(year, month_number, 1),
                                    count=count
                                )

                                processed_data.append({
                                    'site': site.name,
                                    'year': year,
                                    'month': month_number,
                                    'species': species.common_name,
                                    'count': count
                                })
                            except Exception as e:
                                error_msg = f'Database operation error: {str(e)} while processing {species_name} for {site_name} (Year: {year}, Month: {month_number}) at Excel row {r_idx_actual + 1}.'
                                print(f"ERROR: {error_msg}")
                                return JsonResponse({'status': 'error', 'message': error_msg})

                if not processed_data:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No valid bird detection data found in the Excel file after processing. Please check format and ensure counts are present.'
                    })

                return JsonResponse({
                    'status': 'success',
                    'data': processed_data
                })
                
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error reading or processing Excel file: {str(e)}'
                })
    else:
        form = ImportDataForm()
    
    return render(request, 'admindashboard/import_data.html', {'form': form})

@permission_required('view_report_management')
def species_distribution_view(request):
    """View for the species distribution report"""
    context = {
        'page_title': 'Species Distribution Report',
        'active_page': 'reports',
    }
    return render(request, 'admindashboard/reports/species_distribution.html', context)

@permission_required('view_report_management')
def population_trends_view(request):
    """View for the population trends report"""
    context = {
        'page_title': 'Population Trends Report',
        'active_page': 'reports',
    }
    return render(request, 'admindashboard/reports/population_trends.html', context)

@permission_required('view_report_management')
def forecasting_view(request):
    """View for the forecasting report"""
    context = {
        'page_title': 'Forecasting Report',
        'active_page': 'reports',
    }
    return render(request, 'admindashboard/reports/forecasting.html', context)

@permission_required('view_report_management')
def site_analysis_view(request):
    """View for the site analysis report"""
    sites = Site.objects.all().order_by('name')
    context = {
        'page_title': 'Site Analysis Report',
        'active_page': 'reports',
        'sites': sites,
    }
    return render(request, 'admindashboard/reports/site_analysis.html', context)

@permission_required('view_report_management')
def get_site_analysis_data(request, site_id, year):
    """API endpoint for getting site analysis data"""
    site = get_object_or_404(Site, id=site_id)
    
    # Get all detections for the site and year
    detections = BirdDetection.objects.filter(
        site=site,
        detection_date__year=year
    ).select_related('species', 'species__family')

    # Calculate statistics
    total_detections = detections.count()
    unique_species = detections.values('species').distinct().count()
    
    # Get most common species
    most_common = detections.values('species__common_name')\
        .annotate(count=models.Count('id'))\
        .order_by('-count')\
        .first()
    
    # Calculate monthly trends with family information
    monthly_trends = detections.annotate(
        month=models.functions.ExtractMonth('detection_date')
    ).values('month')\
        .annotate(
            count=models.Count('id'),
            avg_confidence=models.Avg('confidence')
        )\
        .order_by('month')

    # Calculate species distribution with family information
    species_distribution = detections.values(
        'species__common_name',
        'species__family__name'
    ).annotate(
        count=models.Count('id'),
        avg_confidence=models.Avg('confidence')
    ).order_by('-count')

    # Calculate family distribution
    family_distribution = detections.values(
        'species__family__name'
    ).annotate(
        count=models.Count('id'),
        species_count=models.Count('species', distinct=True)
    ).order_by('-count')

    # Calculate detailed detection data
    detection_data = []
    for species in species_distribution:
        species_detections = detections.filter(species__common_name=species['species__common_name'])
        
        # Get most active month for this species
        most_active_month = species_detections.annotate(
            month=models.functions.ExtractMonth('detection_date')
        ).values('month')\
            .annotate(count=models.Count('id'))\
            .order_by('-count')\
            .first()
        
        # Calculate detection rate (detections per month)
        detection_rate = species['count'] / 12  # Assuming data for all months
        
        detection_data.append({
            'species': species['species__common_name'],
            'family': species['species__family__name'],
            'total_detections': species['count'],
            'avg_confidence': round(species['avg_confidence'] or 0, 2),
            'most_active_month': most_active_month['month'] if most_active_month else 'N/A',
            'detection_rate': round(detection_rate, 2)
        })

    # Get site status and activity
    site_status = {
        'name': site.name,
        'location': site.location,
        'status': site.status,
        'description': site.description,
        'created_at': site.created_at.strftime('%Y-%m-%d'),
        'last_updated': site.updated_at.strftime('%Y-%m-%d'),
        'total_years_active': BirdDetection.objects.filter(site=site).dates('detection_date', 'year').distinct().count()
    }

    # Prepare response data
    data = {
        'site_info': site_status,
        'statistics': {
            'total_detections': total_detections,
            'unique_species': unique_species,
            'most_common_species': most_common['species__common_name'] if most_common else 'N/A',
            'avg_detections_per_month': round(total_detections / 12, 2),
            'total_families': family_distribution.count(),
            'avg_confidence': round(detections.aggregate(avg=models.Avg('confidence'))['avg'] or 0, 2)
        },
        'monthly_trends': [
            {
                'month': item['month'],
                'count': item['count'],
                'avg_confidence': round(item['avg_confidence'] or 0, 2)
            }
            for item in monthly_trends
        ],
        'species_distribution': [
            {
                'species': item['species__common_name'],
                'family': item['species__family__name'],
                'count': item['count'],
                'avg_confidence': round(item['avg_confidence'] or 0, 2)
            }
            for item in species_distribution
        ],
        'family_distribution': [
            {
                'family': item['species__family__name'],
                'count': item['count'],
                'species_count': item['species_count']
            }
            for item in family_distribution
        ],
        'detection_data': detection_data
    }

    return JsonResponse(data)