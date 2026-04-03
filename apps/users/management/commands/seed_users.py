from django.core.management.base import BaseCommand
from apps.users.models import User


class Command(BaseCommand):
    help = 'Seed the database with initial users'

    def handle(self, *args, **options):
        users = [
            {
                'username': 'admin2',
                'email': 'admin2@bank.com',
                'password': 'admin123',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'username': 'teller',
                'email': 'teller@bank.com',
                'password': 'teller123',
                'is_staff': False,
            },
        ]

        for user_data in users:
            password = user_data.pop('password')
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created user: {user.username}'))
            else:
                self.stdout.write(f'User already exists: {user.username}')