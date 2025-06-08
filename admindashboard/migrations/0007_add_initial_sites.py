from django.db import migrations

def add_initial_sites(apps, schema_editor):
    Site = apps.get_model('admindashboard', 'Site')
    
    sites_data = [
        {
            'name': 'Tinampa-an',
            'image': 'site_images/tinampa-an-ponds.jpg',
            'location': 'Brgy. Tinampa-an, Cadiz City',
            'status': 'active'
        },
        {
            'name': 'Banquerohan',
            'image': 'site_images/banquerohan-mudflats.jpg',
            'location': 'Brgy. Banquerohan, Cadiz City',
            'status': 'active'
        },
        {
            'name': 'Cadiz Viejo',
            'image': 'site_images/cadiz-viejo-ponds.jpg',
            'location': 'Brgy. Cadiz Viejo, Cadiz City',
            'status': 'active'
        },
        {
            'name': 'Kabilang-Bilangan',
            'image': 'site_images/kabilang-bilangan-island.jpg',
            'location': 'Brgy. Daga, Cadiz City',
            'status': 'active'
        },
        {
            'name': 'Zone 2-3',
            'image': 'site_images/zone-2-3-ponds.jpg',
            'location': 'Brgy. Zone 2 & 3, Cadiz City',
            'status': 'active'
        },
        {
            'name': 'Lakawon',
            'image': 'site_images/lakawon-island.jpg',
            'location': 'Brgy. Cadiz Viejo, Cadiz City',
            'status': 'active'
        },
        {
            'name': 'Sicaba-Luna',
            'image': 'site_images/sicaba-luna-ponds.jpg',
            'location': 'Brgy. Sicaba & Luna, Cadiz City',
            'status': 'active'
        },
        {
            'name': 'Daga',
            'image': 'site_images/daga-mudflats.jpg',
            'location': 'Brgy. Daga, Cadiz City',
            'status': 'active'
        }
    ]
    
    for site_data in sites_data:
        Site.objects.get_or_create(
            name=site_data['name'],
            defaults={
                'image': site_data['image'],
                'location': site_data['location'],
                'status': site_data['status']
            }
        )

def remove_initial_sites(apps, schema_editor):
    Site = apps.get_model('admindashboard', 'Site')
    Site.objects.filter(name__in=[
        'Tinampa-an', 'Banquerohan', 'Cadiz Viejo', 'Kabilang-Bilangan',
        'Zone 2-3', 'Lakawon', 'Sicaba-Luna', 'Daga'
    ]).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('admindashboard', '0006_remove_site_code'),
    ]

    operations = [
        migrations.RunPython(add_initial_sites, remove_initial_sites),
    ] 