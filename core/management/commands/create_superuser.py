from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings

class Command(BaseCommand):
    help = 'Creates a superuser with predefined credentials'

    def handle(self, *args, **options):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123456'
            )
            self.stdout.write(self.style.SUCCESS('Superuser created successfully'))
        else:
            self.stdout.write(self.style.WARNING('Superuser already exists')) 