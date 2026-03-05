"""
Models for Good Behaviour - Criminal record checks
"""
from django.db import models


class Citizen(models.Model):
    """Citizen with potential criminal records."""
    citizen_id = models.CharField(max_length=50, unique=True, help_text='Unique citizen identifier')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name_plural = 'Citizens'
    
    def __str__(self):
        return f"{self.citizen_id} - {self.first_name} {self.last_name}"
    
    @property
    def has_criminal_record(self):
        return self.criminal_records.exists()


class CriminalRecord(models.Model):
    """Criminal offense record for a citizen."""
    SEVERITY_CHOICES = [
        ('minor', 'Minor Offense'),
        ('moderate', 'Moderate Offense'),
        ('serious', 'Serious Offense'),
        ('felony', 'Felony'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('expunged', 'Expunged'),
        ('pending', 'Pending Trial'),
    ]
    
    OFFENSE_TYPES = [
        ('traffic', 'Traffic Violation'),
        ('theft', 'Theft'),
        ('assault', 'Assault'),
        ('fraud', 'Fraud'),
        ('vandalism', 'Vandalism'),
        ('drug', 'Drug Offense'),
        ('disorderly', 'Disorderly Conduct'),
        ('other', 'Other'),
    ]
    
    citizen = models.ForeignKey(Citizen, on_delete=models.CASCADE, related_name='criminal_records')
    offense_type = models.CharField(max_length=50, choices=OFFENSE_TYPES)
    description = models.TextField()
    offense_date = models.DateField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    sentence = models.CharField(max_length=255, blank=True, help_text='Sentence or penalty')
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-offense_date']
    
    def __str__(self):
        return f"{self.citizen.citizen_id} - {self.get_offense_type_display()} ({self.offense_date})"
