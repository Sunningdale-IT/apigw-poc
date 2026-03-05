"""
Django management command to populate the database with test dog data.
Usage: python manage.py populate_test_data [--count N] [--force]
"""

import os
import random
import requests
from decimal import Decimal
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from dogs.models import Dog


class Command(BaseCommand):
    help = 'Populate the database with test dog data (50 entries by default)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of test dogs to create (default: 50)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force population even if dogs already exist'
        )

    def handle(self, *args, **options):
        count = options['count']
        force = options['force']
        
        # Check if dogs already exist
        existing_count = Dog.objects.count()
        if existing_count > 0 and not force:
            # Check if photos are missing for existing dogs
            dogs_with_photos = Dog.objects.filter(photo_filename__isnull=False)
            missing_photos = []
            
            for dog in dogs_with_photos:
                photo_path = Path(settings.BASE_DIR) / 'static' / 'uploads' / dog.photo_filename
                if not photo_path.exists():
                    missing_photos.append(dog)
            
            if missing_photos:
                self.stdout.write(
                    self.style.WARNING(
                        f'Database contains {existing_count} dog(s) but {len(missing_photos)} photo(s) are missing. '
                        f'Re-downloading missing photos...'
                    )
                )
                # Re-download missing photos
                self._redownload_photos(missing_photos)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully re-downloaded {len(missing_photos)} missing photo(s)!'
                    )
                )
                return
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Database already contains {existing_count} dog(s) with all photos present. '
                        f'Use --force to repopulate anyway.'
                    )
                )
                return
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Populating database with {count} test dogs...'
            )
        )
        
        # Dog data arrays
        names = [
            "Buddy", "Max", "Charlie", "Cooper", "Rocky",
            "Bear", "Duke", "Tucker", "Jack", "Buster",
            "Luna", "Bella", "Daisy", "Lucy", "Molly",
            "Sadie", "Bailey", "Maggie", "Sophie", "Chloe",
            "Toby", "Zeus", "Oscar", "Leo", "Oliver",
            "Milo", "Finn", "Bentley", "Loki", "Teddy",
            "Murphy", "Jax", "Gus", "Jasper", "Winston",
            "Harley", "Riley", "Henry", "Archie", "Blue",
            "Moose", "Gunner", "Ace", "Apollo", "Dexter",
            "Cash", "Hank", "Bruno", "Atlas", "Maverick"
        ]
        
        breeds = [
            "Labrador Retriever", "Golden Retriever", "Beagle", "Bulldog", "Poodle",
            "German Shepherd", "Siberian Husky", "Boxer", "Dachshund", "Welsh Corgi",
            "Rottweiler", "Doberman", "Border Collie", "Australian Shepherd", "Cocker Spaniel",
            "Shiba Inu", "Akita", "Maltese", "Pomeranian", "Chihuahua",
            "Yorkshire Terrier", "French Bulldog", "Schnauzer", "Shih Tzu", "Boston Terrier",
            "Great Dane", "Mastiff", "Saint Bernard", "Bernese Mountain Dog", "Newfoundland",
            "Pointer", "Setter", "Spaniel", "Retriever", "Terrier",
            "Pug", "Dalmatian", "Greyhound", "Whippet", "Basenji",
            "Samoyed", "Malamute", "Chow Chow", "Shetland Sheepdog", "Australian Cattle Dog",
            "Rhodesian Ridgeback", "Weimaraner", "Vizsla", "Jack Russell Terrier", "Havanese"
        ]
        
        comments_templates = [
            "Very friendly, wearing a {color} collar",
            "Appears well-cared for, microchip pending scan",
            "Found near the park, seems lost",
            "Nervous around strangers, responds to treats",
            "Active and playful, knows basic commands",
            "Senior dog, moves slowly but gentle",
            "Young puppy, approximately {age} months old",
            "No collar, well-groomed coat",
            "Found during {weather}, seeking shelter",
            "Loves belly rubs, good with children",
            "Barks at squirrels, otherwise quiet",
            "Was found near {location}",
            "Responds to whistle, trained dog",
            "Very hungry when found, now eating well",
            "Has distinctive {marking} markings, easy to identify",
            "Found with leash attached, no tag",
            "Appears to be a family pet, well-socialized",
            "Protective but friendly once introduced",
            "Energetic and loves to play fetch",
            "Calm temperament, great companion"
        ]
        
        # Location data (fictional city coordinates)
        locations = [
            (40.7128, -74.0060, "Central Park area"),
            (40.7580, -73.9855, "Times Square vicinity"),
            (40.6892, -74.0445, "Near waterfront"),
            (40.7484, -73.9857, "Midtown district"),
            (40.7061, -73.9969, "Bridge approach"),
            (40.7282, -73.7949, "Residential neighborhood"),
            (40.8448, -73.8648, "Zoo area"),
            (40.7489, -73.9680, "East side"),
            (40.7736, -73.9566, "Upper east"),
            (40.7831, -73.9712, "Upper west"),
            (40.7411, -74.0018, "Market district"),
            (40.7614, -73.9776, "Center plaza"),
            (40.7527, -73.9772, "Station vicinity"),
            (40.7794, -73.9632, "Museum area"),
            (40.6501, -73.9496, "Park grounds"),
            (40.7033, -73.9903, "Riverside"),
            (40.7193, -73.9951, "Lower east"),
            (40.7265, -74.0007, "Shopping district"),
            (40.7243, -73.9927, "East village"),
            (40.7359, -74.0036, "West village")
        ]
        
        colors = ["blue", "red", "green", "black", "brown", "yellow", "pink", "purple"]
        weather_conditions = ["thunderstorm", "heavy rain", "snow", "cold night"]
        landmarks = ["school playground", "library", "community center", "shopping mall", "train station"]
        markings = ["brown", "white", "black", "spotted"]
        
        # Ensure uploads directory exists
        uploads_dir = Path(settings.BASE_DIR) / 'static' / 'uploads'
        uploads_dir.mkdir(parents=True, exist_ok=True)
        
        self.stdout.write('Downloading dog photos from Dog CEO API...')
        
        # Calculate how many border terriers we need (at least 10%)
        border_terrier_count = max(1, int(count * 0.1))
        self.stdout.write(
            f'  Ensuring at least {border_terrier_count} Border Terriers (10% of {count})...'
        )
        
        created_count = 0
        with transaction.atomic():
            for i in range(min(count, len(names))):
                # Randomize data
                name = names[i]
                
                # Ensure at least 10% are Border Terriers
                is_border_terrier = i < border_terrier_count
                if is_border_terrier:
                    breed = "Border Terrier"
                else:
                    breed = random.choice(breeds)
                
                location = random.choice(locations)
                
                # Add randomness to coordinates (within ~500m)
                lat_offset = Decimal(random.uniform(-0.005, 0.005))
                lon_offset = Decimal(random.uniform(-0.005, 0.005))
                latitude = Decimal(str(location[0])) + lat_offset
                longitude = Decimal(str(location[1])) + lon_offset
                
                # Generate comment
                comment_template = random.choice(comments_templates)
                comment = comment_template.format(
                    color=random.choice(colors),
                    age=random.randint(3, 12),
                    weather=random.choice(weather_conditions),
                    location=random.choice(landmarks),
                    marking=random.choice(markings)
                )
                full_comment = f"{comment}. Found near {location[2]}."
                
                # Download a dog photo
                photo_filename = None
                try:
                    # Use Dog CEO API to get breed-specific or random dog image
                    if is_border_terrier:
                        # Get Border Terrier photo
                        api_url = 'https://dog.ceo/api/breed/terrier/border/images/random'
                    else:
                        # Get random dog photo
                        api_url = 'https://dog.ceo/api/breeds/image/random'
                    
                    response = requests.get(api_url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('status') == 'success':
                            image_url = data.get('message')
                            
                            # Download the image
                            img_response = requests.get(image_url, timeout=10)
                            if img_response.status_code == 200:
                                # Generate filename
                                photo_filename = f'dog_{i+1}_{name.lower()}.jpg'
                                photo_path = uploads_dir / photo_filename
                                
                                # Save image
                                with open(photo_path, 'wb') as f:
                                    f.write(img_response.content)
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  Failed to download photo for {name}: {e}'
                        )
                    )
                
                # Create dog entry
                dog = Dog.objects.create(
                    name=name,
                    breed=breed,
                    latitude=latitude,
                    longitude=longitude,
                    comments=full_comment,
                    photo_filename=photo_filename,
                )
                
                created_count += 1
                
                if (created_count % 10) == 0:
                    self.stdout.write(f'  Created {created_count} dogs...')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} test dog entries!'
            )
        )

    def _redownload_photos(self, dogs):
        """Re-download photos for dogs with missing files."""
        uploads_dir = Path(settings.BASE_DIR) / 'static' / 'uploads'
        uploads_dir.mkdir(parents=True, exist_ok=True)
        
        for dog in dogs:
            try:
                # Determine API URL based on breed
                if 'Border Terrier' in dog.breed:
                    api_url = 'https://dog.ceo/api/breed/terrier/border/images/random'
                else:
                    api_url = 'https://dog.ceo/api/breeds/image/random'
                
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'success':
                        image_url = data.get('message')
                        
                        # Download the image
                        img_response = requests.get(image_url, timeout=10)
                        if img_response.status_code == 200:
                            photo_path = uploads_dir / dog.photo_filename
                            
                            # Save image
                            with open(photo_path, 'wb') as f:
                                f.write(img_response.content)
                            
                            self.stdout.write(f'  Downloaded photo for {dog.name} (ID {dog.id})')
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f'  Failed to download photo for {dog.name}: {e}'
                    )
                )
