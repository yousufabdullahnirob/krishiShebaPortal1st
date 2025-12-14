import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from api.models import Crop, CropRecommendation

# Create sample recommendations using existing crops
recommendations = [
    {'soil_type': 'loam', 'season': 'kharif', 'crop_name': 'Rice', 'yield': 4.5, 'tips': 'Rice grows well in loam soil during kharif season.'},
    {'soil_type': 'loam', 'season': 'rabi', 'crop_name': 'Wheat', 'yield': 3.2, 'tips': 'Wheat is ideal for loam soil in rabi season.'},
    {'soil_type': 'clay', 'season': 'kharif', 'crop_name': 'Rice', 'yield': 4.0, 'tips': 'Clay soil retains water well for rice cultivation.'},
    {'soil_type': 'sandy', 'season': 'kharif', 'crop_name': 'Mung Bean', 'yield': 1.8, 'tips': 'Mung bean tolerates sandy soil and drought conditions.'},
    {'soil_type': 'silt', 'season': 'rabi', 'crop_name': 'Lentil (Masoor)', 'yield': 2.1, 'tips': 'Lentils thrive in silt soil during winter.'},
]

for rec in recommendations:
    try:
        crop = Crop.objects.get(name=rec['crop_name'])
        obj, created = CropRecommendation.objects.get_or_create(
            soil_type=rec['soil_type'],
            season=rec['season'],
            recommended_crop=crop,
            defaults={
                'expected_yield': rec['yield'],
                'tips': rec['tips'],
                'confidence': 0.85
            }
        )
        if created:
            print(f'Created recommendation for {rec["crop_name"]}')
        else:
            print(f'Recommendation for {rec["crop_name"]} already exists')
    except Crop.DoesNotExist:
        print(f'Crop {rec["crop_name"]} not found')

print('Final CropRecommendation count:', CropRecommendation.objects.count())
