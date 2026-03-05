# Generated initial migration for moviezzz movies app

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Cinema',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('address', models.CharField(max_length=255)),
                ('phone', models.CharField(blank=True, max_length=50)),
                ('screens', models.IntegerField(default=1)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Movie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('plot', models.TextField()),
                ('director', models.CharField(default='Unknown', max_length=255)),
                ('runtime_minutes', models.IntegerField(default=90)),
                ('rating', models.CharField(default='R', max_length=10)),
                ('year', models.IntegerField(default=2024)),
                ('genre', models.CharField(default='Action', max_length=100)),
                ('showtimes', models.JSONField(default=list, help_text='List of showtime strings')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('cinemas', models.ManyToManyField(related_name='movies', to='movies.cinema')),
            ],
            options={
                'ordering': ['title'],
            },
        ),
    ]
