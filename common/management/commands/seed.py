from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Run all seeders'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            help='Seed a specific model: users, accounts, all',
            default='all'
        )

    def handle(self, *args, **options):
        model = options['model']

        if model in ('users', 'all'):
            call_command('seed_users') 
        if model in ('accounts', 'all'):
            # call_command('seed_accounts')
            print('Seeding accounts is currently disabled.')

        self.stdout.write(self.style.SUCCESS('All seeds complete'))