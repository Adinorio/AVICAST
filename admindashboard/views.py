import os
import tempfile
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import logout
from ultralytics import YOLO
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST, require_GET
from .models import Family, Species
from .forms import FamilyForm, SpeciesForm
from django.http import JsonResponse
import requests
from datetime import datetime, timedelta

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

def statistical_reports_view(request):
    # Negros Occidental coordinates (Bacolod City as example)
    lat, lng = 10.6765, 122.9509
    api_key = 'a1496e94-3090-11f0-b9ca-0242ac130003-a1496f34-3090-11f0-b9ca-0242ac130003'  # Provided API key
    end = datetime.utcnow() + timedelta(days=7)
    params = {
        'lat': lat,
        'lng': lng,
        'params': 'airTemperature,windSpeed,precipitation,waterTemperature,tide',
        'start': int(datetime.utcnow().timestamp()),
        'end': int(end.timestamp())
    }
    headers = {'Authorization': api_key}
    best_days = []
    forecast = []
    try:
        response = requests.get('https://api.stormglass.io/v2/weather/point', params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            for hour in data.get('hours', []):
                # Simple criteria: wind < 5 m/s, precipitation < 1 mm
                wind = hour.get('windSpeed', {}).get('noaa', 100)
                rain = hour.get('precipitation', {}).get('noaa', 100)
                if wind is not None and rain is not None and wind < 5 and rain < 1:
                    best_days.append(hour['time'])
                forecast.append(hour)
        else:
            print('Stormglass API error:', response.text)
    except Exception as e:
        print('Error fetching weather data:', e)
    context = {
        'best_days': best_days,
        'forecast': forecast,
    }
    return render(request, 'admindashboard/statistical_reports.html', context)

@require_GET
def statistical_reports_api(request):
    import time
    lat = float(request.GET.get('lat', 10.6765))
    lng = float(request.GET.get('lng', 122.9509))
    days = int(request.GET.get('days', 7))
    api_key = 'a1496e94-3090-11f0-b9ca-0242ac130003-a1496f34-3090-11f0-b9ca-0242ac130003'
    end_dt = datetime.utcnow() + timedelta(days=days)
    start_ts = int(datetime.utcnow().timestamp())
    end_ts = int(end_dt.timestamp())
    params_weather = {
        'lat': lat,
        'lng': lng,
        'params': 'airTemperature,windSpeed,precipitation,waterTemperature',
        'start': start_ts,
        'end': end_ts
    }
    headers = {'Authorization': api_key}
    best_days = []
    forecast = []
    # Weather data
    try:
        response = requests.get('https://api.stormglass.io/v2/weather/point', params=params_weather, headers=headers)
        if response.status_code == 200:
            data = response.json()
            for hour in data.get('hours', []):
                wind = hour.get('windSpeed', {}).get('noaa', 100)
                rain = hour.get('precipitation', {}).get('noaa', 100)
                temp = hour.get('airTemperature', {}).get('noaa', 0)
                if wind is not None and rain is not None and temp is not None and wind < 5 and rain < 1 and 20 <= temp <= 32:
                    best_days.append(hour['time'])
                forecast.append(hour)
    except Exception as e:
        pass
    # Tide data (extremes)
    tide_data = []
    try:
        response_tide = requests.get(
            'https://api.stormglass.io/v2/tide/extremes/point',
            params={
                'lat': lat,
                'lng': lng,
                'start': start_ts,
                'end': end_ts
            },
            headers=headers
        )
        if response_tide.status_code == 200:
            tide_data = response_tide.json().get('data', [])
    except Exception as e:
        pass
    return JsonResponse({'best_days': best_days, 'forecast': forecast, 'tides': tide_data})