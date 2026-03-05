"""
Management command to populate citizens and criminal records
"""
from django.core.management.base import BaseCommand
from records.models import Citizen, CriminalRecord
from datetime import date, timedelta
import random


class Command(BaseCommand):
    help = 'Populate database with citizen and criminal record data'

    def handle(self, *args, **options):
        # Clear existing data
        CriminalRecord.objects.all().delete()
        Citizen.objects.all().delete()
        
        first_names = ['James', 'John', 'Robert', 'Michael', 'William', 'David', 'Richard', 'Joseph', 
                       'Mary', 'Patricia', 'Jennifer', 'Linda', 'Elizabeth', 'Barbara', 'Susan', 'Jessica',
                       'Sarah', 'Karen', 'Nancy', 'Lisa', 'Margaret', 'Betty', 'Sandra', 'Ashley']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
                      'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
                      'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Thompson']
        
        offense_descriptions = {
            'traffic': [
                'Speeding 25 mph over the limit',
                'Running a red light',
                'Driving without a valid license',
                'Reckless driving',
            ],
            'theft': [
                'Shoplifting from retail store',
                'Bicycle theft from public area',
                'Theft from vehicle',
                'Pickpocketing in crowded area',
            ],
            'assault': [
                'Simple assault in bar altercation',
                'Domestic disturbance',
                'Assault and battery',
            ],
            'fraud': [
                'Credit card fraud',
                'Identity theft',
                'Insurance fraud',
            ],
            'vandalism': [
                'Graffiti on public property',
                'Property damage',
                'Defacing public monument',
            ],
            'drug': [
                'Possession of controlled substance',
                'Drug paraphernalia possession',
                'Distribution of illegal substances',
            ],
            'disorderly': [
                'Public intoxication',
                'Disturbing the peace',
                'Disorderly conduct at public event',
            ],
        }
        
        self.stdout.write('Creating citizens...')
        
        citizens_created = 0
        clean_record_count = 0

        # Keep these IDs aligned with citizen-app MOCK_CITIZENS.
        demo_citizens = [
            {
                'citizen_id': 'CIT001',
                'first_name': 'John',
                'last_name': 'Smith',
                'date_of_birth': date(1988, 5, 14),
                'email': 'john.smith@email.com',
                'phone': '555-1001',
                'address': '123 Main Street, Springfield',
                'records': [],
            },
            {
                'citizen_id': 'CIT002',
                'first_name': 'Jane',
                'last_name': 'Doe',
                'date_of_birth': date(1990, 8, 21),
                'email': 'jane.doe@email.com',
                'phone': '555-1002',
                'address': '456 Oak Avenue, Riverside',
                'records': [
                    {
                        'offense_type': 'traffic',
                        'description': 'Speeding 20 mph over the limit',
                        'offense_date': date.today() - timedelta(days=380),
                        'severity': 'minor',
                        'status': 'closed',
                        'sentence': 'Fine only',
                        'fine_amount': 220.00,
                    },
                ],
            },
            {
                'citizen_id': 'CIT003',
                'first_name': 'Bob',
                'last_name': 'Wilson',
                'date_of_birth': date(1985, 2, 3),
                'email': 'bob.wilson@email.com',
                'phone': '555-1003',
                'address': '789 Pine Road, Lakeside',
                'records': [
                    {
                        'offense_type': 'disorderly',
                        'description': 'Disorderly conduct at public event',
                        'offense_date': date.today() - timedelta(days=120),
                        'severity': 'moderate',
                        'status': 'pending',
                        'sentence': 'Pending court appearance',
                        'fine_amount': 750.00,
                    },
                ],
            },
        ]

        for entry in demo_citizens:
            citizen = Citizen.objects.create(
                citizen_id=entry['citizen_id'],
                first_name=entry['first_name'],
                last_name=entry['last_name'],
                date_of_birth=entry['date_of_birth'],
                email=entry['email'],
                phone=entry['phone'],
                address=entry['address'],
            )

            if entry['records']:
                for record in entry['records']:
                    CriminalRecord.objects.create(citizen=citizen, **record)
                record_count = citizen.criminal_records.count()
                self.stdout.write(
                    f"  ⚠️  {entry['citizen_id']} - {entry['first_name']} {entry['last_name']} "
                    f"({record_count} record{'s' if record_count > 1 else ''})"
                )
            else:
                clean_record_count += 1
                self.stdout.write(
                    f"  ✓ {entry['citizen_id']} - {entry['first_name']} {entry['last_name']} (Clean record)"
                )

            citizens_created += 1
        
        for i in range(25):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            citizen_id = f"CIT-{2000 + i:04d}"
            
            # Random birth date (ages 18-75)
            age = random.randint(18, 75)
            dob = date.today() - timedelta(days=age * 365)
            
            citizen = Citizen.objects.create(
                citizen_id=citizen_id,
                first_name=first_name,
                last_name=last_name,
                date_of_birth=dob,
                email=f"{first_name.lower()}.{last_name.lower()}@example.com",
                phone=f"555-{random.randint(1000, 9999)}",
                address=f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Elm', 'Maple', 'Pine'])} Street",
            )
            
            # 60% have clean records, 40% have some history
            has_record = random.random() < 0.40
            
            if has_record:
                # Create 1-4 records for this citizen
                num_records = random.randint(1, 4)
                
                for _ in range(num_records):
                    offense_type = random.choice(list(offense_descriptions.keys()))
                    description = random.choice(offense_descriptions[offense_type])
                    
                    # Random date in past 10 years
                    days_ago = random.randint(30, 3650)
                    offense_date = date.today() - timedelta(days=days_ago)
                    
                    # Severity based on offense type
                    if offense_type in ['traffic', 'disorderly', 'vandalism']:
                        severity = random.choice(['minor', 'moderate'])
                    elif offense_type in ['theft', 'fraud']:
                        severity = random.choice(['moderate', 'serious'])
                    else:
                        severity = random.choice(['serious', 'felony'])
                    
                    # Status - older offenses more likely closed
                    if days_ago > 730:  # > 2 years
                        status = random.choice(['closed', 'closed', 'expunged', 'active'])
                    else:
                        status = random.choice(['active', 'pending', 'closed'])
                    
                    # Fine amount
                    if severity == 'minor':
                        fine = round(random.uniform(100, 500), 2)
                    elif severity == 'moderate':
                        fine = round(random.uniform(500, 2000), 2)
                    elif severity == 'serious':
                        fine = round(random.uniform(2000, 10000), 2)
                    else:
                        fine = round(random.uniform(10000, 50000), 2)
                    
                    # Sentence
                    sentences = {
                        'minor': ['Fine only', 'Community service 20 hours', 'Probation 6 months'],
                        'moderate': ['Fine and probation', 'Community service 100 hours', 'Probation 1 year'],
                        'serious': ['Probation 2 years', 'Suspended sentence', 'Jail time 6 months'],
                        'felony': ['Prison 1-3 years', 'Prison 3-5 years', 'Probation 5 years'],
                    }
                    sentence = random.choice(sentences[severity])
                    
                    CriminalRecord.objects.create(
                        citizen=citizen,
                        offense_type=offense_type,
                        description=description,
                        offense_date=offense_date,
                        severity=severity,
                        status=status,
                        sentence=sentence,
                        fine_amount=fine,
                    )
                
                record_count = citizen.criminal_records.count()
                self.stdout.write(f"  ⚠️  {citizen_id} - {first_name} {last_name} ({record_count} record{'s' if record_count > 1 else ''})")
            else:
                clean_record_count += 1
                self.stdout.write(f"  ✓ {citizen_id} - {first_name} {last_name} (Clean record)")
            
            citizens_created += 1
        
        total_records = CriminalRecord.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Good Behaviour initialized successfully!\n'
            f'Created {citizens_created} citizens:\n'
            f'  - {clean_record_count} with clean records\n'
            f'  - {citizens_created - clean_record_count} with criminal history ({total_records} total records)'
        ))
