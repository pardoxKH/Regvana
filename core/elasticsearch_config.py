from elasticsearch import Elasticsearch
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

try:
    # Elasticsearch client configuration
    es = Elasticsearch(
        [settings.ELASTICSEARCH_HOST],
        basic_auth=(settings.ELASTICSEARCH_USERNAME, settings.ELASTICSEARCH_PASSWORD) if settings.ELASTICSEARCH_USERNAME else None
    )
except (ImportError, ImproperlyConfigured):
    es = None

# Index name for regulations
REGULATION_INDEX = 'regulations'

# Mapping for regulations index
REGULATION_MAPPING = {
    'mappings': {
        'properties': {
            'id': {'type': 'integer'},
            'reference': {'type': 'text', 'analyzer': 'standard'},
            'name': {'type': 'text', 'analyzer': 'standard'},
            'description': {'type': 'text', 'analyzer': 'standard'},
            'status': {'type': 'keyword'},
            'type': {'type': 'keyword'},
            'created_by': {'type': 'text', 'analyzer': 'standard'},
            'date_created': {'type': 'date'},
            'last_updated': {'type': 'date'},
            'assigned_departments': {'type': 'text', 'analyzer': 'standard'}
        }
    }
}

def create_regulation_index():
    """Create the regulations index if it doesn't exist."""
    if es is None:
        return
    if not es.indices.exists(index=REGULATION_INDEX):
        es.indices.create(index=REGULATION_INDEX, body=REGULATION_MAPPING)

def index_regulation(regulation):
    """Index a regulation document."""
    if es is None:
        return
    doc = {
        'id': regulation.id,
        'reference': regulation.reference,
        'name': regulation.name,
        'description': regulation.description,
        'status': regulation.status,
        'created_by': regulation.created_by.username if regulation.created_by else None,
        'date_created': regulation.date_created,
        'last_updated': regulation.last_updated,
        'assigned_departments': [dept.name for dept in regulation.assigned_departments.all()]
    }
    es.index(index=REGULATION_INDEX, id=regulation.id, body=doc)

def delete_regulation_index(regulation_id):
    """Delete a regulation document from the index."""
    if es is None:
        return
    es.delete(index=REGULATION_INDEX, id=regulation_id)

def search_regulations(query, filters=None):
    """Search regulations with optional filters."""
    if es is None:
        from .models import Regulation
        # Return all regulations if Elasticsearch is not available
        regulations = Regulation.objects.all()
        return [{'id': reg.id, 
                'reference': reg.reference,
                'name': reg.name,
                'description': reg.description,
                'status': reg.status,
                'created_by': reg.created_by.username if reg.created_by else None,
                'date_created': reg.date_created,
                'last_updated': reg.last_updated,
                'assigned_departments': [dept.name for dept in reg.assigned_departments.all()]
                } for reg in regulations]
    
    search_query = {
        'query': {
            'bool': {
                'must': [],
                'filter': []
            }
        }
    }

    # Add full-text search if query is provided
    if query:
        search_query['query']['bool']['must'].append({
            'multi_match': {
                'query': query,
                'fields': ['reference^3', 'name^2', 'description', 'created_by', 'assigned_departments'],
                'fuzziness': 'AUTO'
            }
        })

    # Add filters if provided
    if filters:
        for field, value in filters.items():
            if value:
                search_query['query']['bool']['filter'].append({
                    'term': {field: value}
                })

    # If no query or filters, match all
    if not search_query['query']['bool']['must'] and not search_query['query']['bool']['filter']:
        search_query['query'] = {'match_all': {}}

    try:
        response = es.search(index=REGULATION_INDEX, body=search_query)
        return [hit['_source'] for hit in response['hits']['hits']]
    except Exception as e:
        # If there's any error with Elasticsearch, fall back to database
        from .models import Regulation
        regulations = Regulation.objects.all()
        return [{'id': reg.id, 
                'reference': reg.reference,
                'name': reg.name,
                'description': reg.description,
                'status': reg.status,
                'created_by': reg.created_by.username if reg.created_by else None,
                'date_created': reg.date_created,
                'last_updated': reg.last_updated,
                'assigned_departments': [dept.name for dept in reg.assigned_departments.all()]
                } for reg in regulations] 