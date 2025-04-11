from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Regulation
from .elasticsearch_config import index_regulation, delete_regulation_index

@receiver(post_save, sender=Regulation)
def index_regulation_on_save(sender, instance, **kwargs):
    """Index a regulation when it is created or updated."""
    index_regulation(instance)

@receiver(post_delete, sender=Regulation)
def delete_regulation_on_delete(sender, instance, **kwargs):
    """Delete a regulation from the index when it is deleted from the database."""
    delete_regulation_index(instance.id) 