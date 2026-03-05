"""
Management command to populate park runs
"""
from django.core.management.base import BaseCommand
from runs.models import ParkRun
from datetime import time
import random


class Command(BaseCommand):
    help = 'Populate database with park run data'

    def handle(self, *args, **options):
        # Clear existing data
        ParkRun.objects.all().delete()
        
        park_runs_data = [
            {
                'name': 'Riverside Park Run',
                'location': 'Riverside Park',
                'description': 'Scenic run along the riverside path with beautiful water views. Mostly flat terrain suitable for all fitness levels.',
                'distance_km': 5.0,
                'start_time': time(8, 0),
                'meeting_point': 'Main Park Entrance, Riverside Drive',
                'difficulty': 'easy',
                'organizer_name': 'Sarah Johnson',
                'organizer_email': 'sarah.johnson@parkrun.com',
                'organizer_phone': '555-0101',
                'avg_participants': 85,
            },
            {
                'name': 'City Center Sprint',
                'location': 'Downtown Plaza',
                'description': 'Urban running route through the historic city center. Includes some stairs and uneven pavement.',
                'distance_km': 3.5,
                'start_time': time(7, 30),
                'meeting_point': 'City Hall Steps',
                'difficulty': 'moderate',
                'organizer_name': 'Michael Chen',
                'organizer_email': 'michael.chen@parkrun.com',
                'organizer_phone': '555-0102',
                'avg_participants': 60,
            },
            {
                'name': 'Forest Trail Challenge',
                'location': 'Woodland Forest Reserve',
                'description': 'Challenging trail run through forest paths with significant elevation changes. Muddy when wet.',
                'distance_km': 8.5,
                'start_time': time(8, 30),
                'meeting_point': 'Forest Reserve Parking Lot',
                'difficulty': 'challenging',
                'organizer_name': 'Emma Rodriguez',
                'organizer_email': 'emma.rodriguez@parkrun.com',
                'organizer_phone': '555-0103',
                'avg_participants': 45,
            },
            {
                'name': 'Lakeside Loop',
                'location': 'Crystal Lake Park',
                'description': 'Beautiful loop around Crystal Lake with stunning views. Gentle hills and paved paths throughout.',
                'distance_km': 6.2,
                'start_time': time(8, 0),
                'meeting_point': 'Lake Pavilion',
                'difficulty': 'moderate',
                'organizer_name': 'David Thompson',
                'organizer_email': 'david.thompson@parkrun.com',
                'organizer_phone': '555-0104',
                'avg_participants': 72,
            },
            {
                'name': 'Botanical Gardens Jog',
                'location': 'City Botanical Gardens',
                'description': 'Leisurely run through the beautiful botanical gardens. Flat, paved paths perfect for beginners.',
                'distance_km': 4.0,
                'start_time': time(9, 0),
                'meeting_point': 'Botanical Gardens Main Gate',
                'difficulty': 'easy',
                'organizer_name': 'Lisa Anderson',
                'organizer_email': 'lisa.anderson@parkrun.com',
                'organizer_phone': '555-0105',
                'avg_participants': 95,
            },
            {
                'name': 'Hill Climb Classic',
                'location': 'Summit Hill Park',
                'description': 'Intense hill running course for experienced runners. Steep gradients and technical sections.',
                'distance_km': 7.0,
                'start_time': time(7, 0),
                'meeting_point': 'Summit Hill Trailhead',
                'difficulty': 'challenging',
                'organizer_name': 'Robert Martinez',
                'organizer_email': 'robert.martinez@parkrun.com',
                'organizer_phone': '555-0106',
                'avg_participants': 35,
            },
            {
                'name': 'Beach Promenade Run',
                'location': 'City Beach',
                'description': 'Flat run along the beach promenade with ocean breeze. Great for speed work and beginners.',
                'distance_km': 5.5,
                'start_time': time(8, 15),
                'meeting_point': 'Beach Boardwalk Pavilion',
                'difficulty': 'easy',
                'organizer_name': 'Jessica Brown',
                'organizer_email': 'jessica.brown@parkrun.com',
                'organizer_phone': '555-0107',
                'avg_participants': 110,
            },
            {
                'name': 'University Campus Circuit',
                'location': 'State University Grounds',
                'description': 'Loop around the university campus with mix of paths and light trails. Some hills included.',
                'distance_km': 6.0,
                'start_time': time(8, 30),
                'meeting_point': 'Student Union Building',
                'difficulty': 'moderate',
                'organizer_name': 'Kevin Williams',
                'organizer_email': 'kevin.williams@parkrun.com',
                'organizer_phone': '555-0108',
                'avg_participants': 68,
            },
            {
                'name': 'Industrial Heritage Trail',
                'location': 'Old Mill District',
                'description': 'Historic run through the restored industrial district along old canal paths.',
                'distance_km': 4.8,
                'start_time': time(9, 0),
                'meeting_point': 'Heritage Museum',
                'difficulty': 'easy',
                'organizer_name': 'Amanda Garcia',
                'organizer_email': 'amanda.garcia@parkrun.com',
                'organizer_phone': '555-0109',
                'avg_participants': 55,
            },
            {
                'name': 'Mountain View Marathon Prep',
                'location': 'Mountain Ridge Trail',
                'description': 'Long distance training run with spectacular mountain views. For experienced runners only.',
                'distance_km': 12.0,
                'start_time': time(7, 0),
                'meeting_point': 'Mountain Base Parking Area',
                'difficulty': 'challenging',
                'organizer_name': 'James Wilson',
                'organizer_email': 'james.wilson@parkrun.com',
                'organizer_phone': '555-0110',
                'avg_participants': 28,
            },
        ]
        
        self.stdout.write('Creating park runs...')
        
        for data in park_runs_data:
            # Generate coordinates (fake city coordinates)
            base_lat = 52.0907
            base_lon = 5.1214
            latitude = base_lat + random.uniform(-0.08, 0.08)
            longitude = base_lon + random.uniform(-0.08, 0.08)
            
            data['latitude'] = round(latitude, 6)
            data['longitude'] = round(longitude, 6)
            data['route_url'] = f"https://maps.example.com/route/{data['name'].lower().replace(' ', '-')}"
            
            ParkRun.objects.create(**data)
            
            difficulty_emoji = {'easy': '🟢', 'moderate': '🟡', 'challenging': '🔴'}[data['difficulty']]
            self.stdout.write(
                f"  {difficulty_emoji} {data['name']} - {data['distance_km']}km at {data['start_time'].strftime('%H:%M')} "
                f"(~{data['avg_participants']} runners)"
            )
        
        total = ParkRun.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'\n🏃 Park Runs initialized successfully!\n'
            f'Created {total} Saturday park runs across the city!'
        ))
