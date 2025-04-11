from django.core.management.base import BaseCommand
from core.models import Regulation
from core.elasticsearch_config import index_regulation, create_regulation_index

class Command(BaseCommand):
    help = 'Index all regulations in Elasticsearch'

    def handle(self, *args, **options):
        # Create index if it doesn't exist
        create_regulation_index()
        
        # Index all regulations
        regulations = Regulation.objects.all()
        for regulation in regulations:
            index_regulation(regulation)
            self.stdout.write(f'Indexed regulation: {regulation.reference}')
        
        self.stdout.write(self.style.SUCCESS('Successfully indexed all regulations')) 