# Generated initial migration for good-behaviour records app

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Citizen',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('citizen_id', models.CharField(help_text='Unique citizen identifier', max_length=50, unique=True)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('date_of_birth', models.DateField()),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('address', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': 'Citizens',
                'ordering': ['last_name', 'first_name'],
            },
        ),
        migrations.CreateModel(
            name='CriminalRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('offense_type', models.CharField(choices=[('traffic', 'Traffic Violation'), ('theft', 'Theft'), ('assault', 'Assault'), ('fraud', 'Fraud'), ('vandalism', 'Vandalism'), ('drug', 'Drug Offense'), ('disorderly', 'Disorderly Conduct'), ('other', 'Other')], max_length=50)),
                ('description', models.TextField()),
                ('offense_date', models.DateField()),
                ('severity', models.CharField(choices=[('minor', 'Minor Offense'), ('moderate', 'Moderate Offense'), ('serious', 'Serious Offense'), ('felony', 'Felony')], max_length=20)),
                ('status', models.CharField(choices=[('active', 'Active'), ('closed', 'Closed'), ('expunged', 'Expunged'), ('pending', 'Pending Trial')], default='active', max_length=20)),
                ('sentence', models.CharField(blank=True, help_text='Sentence or penalty', max_length=255)),
                ('fine_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('citizen', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='criminal_records', to='records.citizen')),
            ],
            options={
                'ordering': ['-offense_date'],
            },
        ),
    ]
