"""
Management command to populate parking spots
"""
from django.core.management.base import BaseCommand
from parking.models import ParkingSpot
import random


class Command(BaseCommand):
    help = 'Populate database with parking spot data'

    def handle(self, *args, **options):
        # Clear existing data
        ParkingSpot.objects.all().delete()
        
        locations = [
            ('Downtown', '100-200 Main Street'),
            ('Downtown', '300-400 Main Street'),
            ('City Center', '50-150 Commerce Boulevard'),
            ('City Center', '200-300 Commerce Boulevard'),
            ('Waterfront', '10-50 Harbor Drive'),
            ('Waterfront', '100-200 Marina Way'),
            ('Old Town', '500-600 Historic Avenue'),
            ('Old Town', '700-800 Heritage Street'),
            ('Shopping District', '1-100 Retail Road'),
            ('Shopping District', '200-300 Market Plaza'),
            ('University Area', '400-500 College Avenue'),
            ('Business Park', '1000-1100 Corporate Drive'),
        ]
        
        spot_types = ['street', 'garage', 'lot', 'disabled', 'ev']
        
        self.stdout.write('Creating parking spots...')
        
        created_count = 0
        for location, address in locations:
            # Create 3-5 spots per location
            num_spots = random.randint(3, 5)
            for i in range(num_spots):
                spot_type = random.choice(spot_types)
                
                # Generate spot number
                if spot_type == 'street':
                    spot_number = f"{location[:3].upper()}-ST-{created_count + 1:03d}"
                elif spot_type == 'garage':
                    spot_number = f"{location[:3].upper()}-GR-L{random.randint(1,5)}-{random.randint(1,99):02d}"
                elif spot_type == 'lot':
                    spot_number = f"{location[:3].upper()}-LOT-{random.randint(1,150):03d}"
                elif spot_type == 'disabled':
                    spot_number = f"{location[:3].upper()}-DIS-{random.randint(1,20):02d}"
                else:  # ev
                    spot_number = f"{location[:3].upper()}-EV-{random.randint(1,30):02d}"
                
                # Random availability (70% available)
                available = random.random() < 0.70
                
                # Hourly rates based on type
                if spot_type == 'street':
                    hourly_rate = round(random.uniform(1.0, 3.0), 2)
                elif spot_type == 'garage':
                    hourly_rate = round(random.uniform(2.0, 5.0), 2)
                elif spot_type == 'lot':
                    hourly_rate = round(random.uniform(1.5, 4.0), 2)
                elif spot_type == 'disabled':
                    hourly_rate = 0.00  # Free
                else:  # ev
                    hourly_rate = round(random.uniform(3.0, 6.0), 2)
                
                # Max duration
                if spot_type == 'street':
                    max_duration = random.choice([2, 4, 8])
                else:
                    max_duration = 24
                
                # Generate coordinates (fake city coordinates)
                base_lat = 52.0907  # Amsterdam-ish
                base_lon = 5.1214
                latitude = base_lat + random.uniform(-0.05, 0.05)
                longitude = base_lon + random.uniform(-0.05, 0.05)
                
                ParkingSpot.objects.create(
                    spot_number=spot_number,
                    location=location,
                    address=address,
                    spot_type=spot_type,
                    available=available,
                    latitude=round(latitude, 6),
                    longitude=round(longitude, 6),
                    hourly_rate=hourly_rate,
                    max_duration_hours=max_duration,
                )
                
                status = "✓ Available" if available else "✗ Occupied"
                self.stdout.write(f"  {status}: {spot_number} - {location} (${hourly_rate}/hr)")
                created_count += 1
        
        available_count = ParkingSpot.objects.filter(available=True).count()
        self.stdout.write(self.style.SUCCESS(
            f'\n🅿️ Free Parking initialized successfully!\n'
            f'Created {created_count} parking spots, {available_count} currently available!'
        ))
