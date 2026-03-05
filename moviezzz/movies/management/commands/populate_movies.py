"""
Django management command to populate cinemas and Jason Statham movies.
"""
import random
from django.core.management.base import BaseCommand
from django.db import transaction
from movies.models import Cinema, Movie


class Command(BaseCommand):
    help = 'Populate cinemas and Jason Statham movies'

    # Cinema data
    CINEMAS = [
        {'name': 'Regal Multiplex', 'address': '123 Main Street', 'phone': '555-1001', 'screens': 12},
        {'name': 'Grand Cinema Palace', 'address': '456 Broadway Avenue', 'phone': '555-1002', 'screens': 8},
        {'name': 'Star Theatre', 'address': '789 Film Road', 'phone': '555-1003', 'screens': 6},
        {'name': 'Metro Cineplex', 'address': '321 Cinema Boulevard', 'phone': '555-1004', 'screens': 10},
        {'name': 'Vista Movie House', 'address': '654 Screen Lane', 'phone': '555-1005', 'screens': 5},
    ]

    # Jason Statham movie titles and plots
    MOVIES = [
        {'title': 'The Redemption Protocol', 'plot': 'A former black ops agent must rescue his kidnapped daughter from an international crime syndicate using his deadly skills.'},
        {'title': 'Collision Course', 'plot': 'An ex-special forces soldier turned getaway driver must pull off one final heist to save his crew from a ruthless mob boss.'},
        {'title': 'Terminal Velocity', 'plot': 'A rogue agent races against time to stop a nuclear terrorist plot while clearing his name from a false accusation.'},
        {'title': 'The Enforcer Returns', 'plot': 'A retired hitman is forced back into action when his past catches up and threatens everyone he loves.'},
        {'title': 'Shadow Operative', 'plot': 'An elite assassin must eliminate a corrupt politician while being hunted by both the CIA and Russian mercenaries.'},
        {'title': 'Breakout Protocol', 'plot': 'A wrongly imprisoned ex-cop must break out of a maximum security prison to prove his innocence and expose the conspiracy.'},
        {'title': 'The Extraction', 'plot': 'A seasoned mercenary leads a dangerous mission to extract a high-value target from a hostile war zone.'},
        {'title': 'Midnight Runner', 'plot': 'A professional thief is blackmailed into stealing a priceless artifact from an impenetrable fortress.'},
        {'title': 'Strike Force Alpha', 'plot': 'The last surviving member of an elite team seeks revenge against the warlord who murdered his brothers in arms.'},
        {'title': 'The Interceptor', 'plot': 'An undercover agent must infiltrate a deadly criminal organization while maintaining his cover at all costs.'},
        {'title': 'Bullet Time', 'plot': 'A disgraced sharpshooter gets one last chance to redeem himself by taking down a terrorist cell single-handedly.'},
        {'title': 'Vendetta Hour', 'plot': 'When his family is killed by corrupt cops, a former detective wages a one-man war against the entire police force.'},
        {'title': 'The Safehouse', 'plot': 'A bodyguard must protect a witness while trapped in a besieged safehouse with unlimited enemies outside.'},
        {'title': 'Recoil', 'plot': 'An explosives expert turned vigilante hunts down the arms dealers who killed his partner.'},
        {'title': 'Maximum Threat', 'plot': 'A counterterrorism specialist must stop his former mentor from unleashing a bioweapon on a major city.'},
        {'title': 'The Reckoning Day', 'plot': 'A debt collector for the mob must choose between loyalty and family when ordered to kill his own brother.'},
        {'title': 'Iron Protocol', 'plot': 'A security consultant discovers a conspiracy within his own company and fights to expose the truth.'},
        {'title': 'Dead Drop', 'plot': 'An intelligence operative must recover stolen military secrets before they fall into enemy hands.'},
        {'title': 'The Specialist', 'plot': 'A demolitions expert is hired to destroy a criminal empire from the inside out.'},
        {'title': 'Crossfire Battalion', 'plot': 'A squad leader must save his captured team from a hostile faction in enemy territory.'},
        {'title': 'The Mechanic Returns', 'plot': 'A master assassin comes out of retirement to train a young protégé and settle an old score.'},
        {'title': 'Hostile Takeover', 'plot': 'A corporate security chief must stop a paramilitary group from taking over a skyscraper full of hostages.'},
        {'title': 'The Courier Protocol', 'plot': 'A package delivery driver discovers his cargo is a witness to a political assassination and must keep her alive.'},
        {'title': 'Elimination Round', 'plot': 'A tournament fighter is forced to compete in an underground death match to save his wife.'},
        {'title': 'The Sentinel', 'plot': 'A lone bodyguard must protect a diplomat through a city crawling with assassins.'},
        {'title': 'Payback Protocol', 'plot': 'A bounty hunter tracks down the men who set him up and left him for dead.'},
        {'title': 'Zero Hour', 'plot': 'A bomb disposal expert must defuse a series of devices planted throughout the city before midnight.'},
        {'title': 'The Contractor', 'plot': 'A private military contractor must rescue POWs from a jungle prison camp.'},
        {'title': 'Velocity Overdrive', 'plot': 'An underground racer must win illegal street races to pay off his debt to a cartel boss.'},
        {'title': 'The Retribution', 'plot': 'After being betrayed by his own government, a spy seeks revenge on those who burned him.'},
        {'title': 'Combat Zone', 'plot': 'A military advisor must lead a ragtag group of civilians through hostile territory to reach safety.'},
        {'title': 'The Infiltrator', 'plot': 'An undercover agent must maintain his cover while taking down a human trafficking ring from within.'},
        {'title': 'Silent Fury', 'plot': 'A mute warrior seeks justice for his murdered family using only his martial arts skills.'},
        {'title': 'The Liquidator', 'plot': 'A cleaner for the mob decides to eliminate his employers instead of cleaning up their messes.'},
        {'title': 'Danger Close', 'plot': 'A sniper must eliminate high-value targets while evading enemy forces in urban warfare.'},
        {'title': 'The Equalizer Protocol', 'plot': 'A vigilante balances the scales of justice by taking down those who prey on the innocent.'},
        {'title': 'Flashpoint Omega', 'plot': 'A hostage negotiator must talk down a suicide bomber while secretly planning a tactical assault.'},
        {'title': 'The Guardian', 'plot': 'A personal protection officer must keep a child witness alive while moving her across the country.'},
        {'title': 'Rapid Assault', 'plot': 'A SWAT team leader must rescue his team from an ambush orchestrated by a crooked chief.'},
        {'title': 'The Negotiator', 'plot': 'A crisis negotiator turned rogue must broker a deal between rival gangs to save innocent lives.'},
        {'title': 'Urban Warfare', 'plot': 'A soldier returns home to find his city controlled by gangs and wages a one-man campaign to take it back.'},
        {'title': 'The Executioner', 'plot': 'A death row inmate is given a chance at freedom if he eliminates a terrorist cell.'},
        {'title': 'Lockdown', 'plot': 'A prison guard must survive a riot orchestrated by inmates seeking revenge against him.'},
        {'title': 'The Scorpion Directive', 'plot': 'An assassin code-named Scorpion must prevent World War III by eliminating rogue generals.'},
        {'title': 'Chain Reaction', 'plot': 'A demolitions expert must stop a chain of explosions threatening to destroy the city.'},
        {'title': 'The Deliverer', 'plot': 'A transporter must deliver sensitive cargo while being hunted by assassins who want it.'},
        {'title': 'Savage Justice', 'plot': 'When the law fails, a former prosecutor takes justice into his own hands.'},
        {'title': 'The Operator', 'plot': 'A drone pilot must go into the field to complete a mission when his technology fails.'},
        {'title': 'Final Protocol', 'plot': 'In his last mission before retirement, an agent must stop his replacement from becoming a traitor.'},
        {'title': 'The Annihilator', 'plot': 'A weapons specialist must destroy a cache of experimental weapons before they reach terrorists.'},
    ]

    SHOWTIMES = ['10:00 AM', '1:00 PM', '4:00 PM', '7:00 PM', '10:00 PM']
    DIRECTORS = ['Guy Ritchie', 'David Leitch', 'John Woo', 'Simon West', 'Louis Leterrier', 'Paul W.S. Anderson']

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force population even if data already exists'
        )

    def handle(self, *args, **options):
        force = options['force']
        
        # Check if data already exists
        existing_movies = Movie.objects.count()
        if existing_movies > 0 and not force:
            self.stdout.write(
                self.style.WARNING(
                    f'Database already contains {existing_movies} movie(s). '
                    f'Use --force to populate anyway.'
                )
            )
            return
        
        with transaction.atomic():
            # Create cinemas
            self.stdout.write('Creating cinemas...')
            cinemas = []
            for cinema_data in self.CINEMAS:
                cinema, created = Cinema.objects.get_or_create(
                    name=cinema_data['name'],
                    defaults=cinema_data
                )
                cinemas.append(cinema)
                status = 'Created' if created else 'Found existing'
                self.stdout.write(f'  {status}: {cinema.name}')
            
            # Create movies
            self.stdout.write('\nCreating Jason Statham movies...')
            for i, movie_data in enumerate(self.MOVIES, 1):
                # Random attributes
                year = random.randint(2020, 2026)
                runtime = random.randint(95, 130)
                director = random.choice(self.DIRECTORS)
                
                # Create movie
                movie = Movie.objects.create(
                    title=movie_data['title'],
                    plot=movie_data['plot'],
                    director=director,
                    runtime_minutes=runtime,
                    rating='R',
                    year=year,
                    genre='Action/Thriller',
                    showtimes=random.sample(self.SHOWTIMES, k=random.randint(3, 5))
                )
                
                # Assign to random cinemas (each movie shows at 2-4 cinemas)
                selected_cinemas = random.sample(cinemas, k=random.randint(2, 4))
                movie.cinemas.set(selected_cinemas)
                
                cinema_names = ', '.join(c.name for c in selected_cinemas)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ Created: {movie.title} ({year}) - Showing at: {cinema_names}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎬 Moviezzz initialized successfully!'
                f'\nCreated {len(self.CINEMAS)} cinemas and {len(self.MOVIES)} Jason Statham action movies!'
            )
        )
