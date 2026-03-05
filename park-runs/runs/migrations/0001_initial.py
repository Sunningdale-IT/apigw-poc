# Generated initial migration for park-runs runs app

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ParkRun',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('location', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('distance_km', models.DecimalField(decimal_places=2, help_text='Distance in kilometers', max_digits=4)),
                ('start_time', models.TimeField(help_text='Saturday start time')),
                ('meeting_point', models.CharField(max_length=255)),
                ('difficulty', models.CharField(choices=[('easy', 'Easy'), ('moderate', 'Moderate'), ('challenging', 'Challenging')], default='moderate', max_length=20)),
                ('organizer_name', models.CharField(max_length=255)),
                ('organizer_email', models.EmailField(max_length=254)),
                ('organizer_phone', models.CharField(blank=True, max_length=20)),
                ('avg_participants', models.IntegerField(default=0, help_text='Average weekly participants')),
                ('route_url', models.URLField(blank=True, help_text='Link to route map')),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['start_time', 'name'],
            },
        ),
    ]
