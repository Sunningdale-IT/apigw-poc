# Generated initial migration for free-parking parking app

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ParkingSpot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('spot_number', models.CharField(max_length=50, unique=True)),
                ('location', models.CharField(max_length=255)),
                ('address', models.CharField(max_length=255)),
                ('spot_type', models.CharField(choices=[('street', 'Street Parking'), ('garage', 'Parking Garage'), ('lot', 'Parking Lot'), ('disabled', 'Disabled Parking'), ('ev', 'EV Charging')], default='street', max_length=20)),
                ('available', models.BooleanField(default=True)),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('hourly_rate', models.DecimalField(decimal_places=2, default=0.0, help_text='Rate per hour in currency', max_digits=5)),
                ('max_duration_hours', models.IntegerField(default=24, help_text='Maximum parking duration in hours')),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['location', 'spot_number'],
            },
        ),
    ]
