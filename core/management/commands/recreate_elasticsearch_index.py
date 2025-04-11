from django.core.management.base import BaseCommand
from core.elasticsearch_config import create_regulation_index, delete_regulation_index, index_regulation
from core.models import Regulation

class Command(BaseCommand):
    help = 'Recreates the Elasticsearch index and reindexes all regulations'

    def handle(self, *args, **options):
        # Delete existing index
        try:
            delete_regulation_index()
            self.stdout.write(self.style.SUCCESS('Successfully deleted existing index'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not delete existing index: {e}'))

        # Create new index with updated mapping
        try:
            create_regulation_index()
            self.stdout.write(self.style.SUCCESS('Successfully created new index'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Could not create new index: {e}'))
            return

        # Reindex all regulations
        regulations = Regulation.objects.all()
        for regulation in regulations:
            try:
                index_regulation(regulation)
                self.stdout.write(self.style.SUCCESS(f'Successfully indexed regulation: {regulation.reference}'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Could not index regulation {regulation.reference}: {e}'))

        self.stdout.write(self.style.SUCCESS('Successfully reindexed all regulations')) 