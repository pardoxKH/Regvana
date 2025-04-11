from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Department, Regulation, Article
from datetime import datetime, timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Populates the database with sample regulations and articles'

    def handle(self, *args, **options):
        # Create a compliance maker user if not exists
        maker, created = User.objects.get_or_create(
            username='compliance_maker',
            defaults={
                'email': 'maker@example.com',
                'role': 'compliance_maker',
                'is_staff': True
            }
        )
        if created:
            maker.set_password('testpass123')
            maker.save()

        # Create some departments if not exists
        departments = []
        department_names = ['HR', 'Finance', 'IT', 'Operations', 'Legal']
        for name in department_names:
            dept, created = Department.objects.get_or_create(
                name=name,
                defaults={'description': f'{name} Department'}
            )
            departments.append(dept)

        # Sample regulation data
        regulations_data = [
            {
                'name': 'Data Protection Regulation',
                'description': 'Regulation for handling and protecting sensitive data',
                'status': 'approved',
                'articles': [
                    {'title': 'Data Collection', 'content': 'Guidelines for collecting user data', 'order': 1},
                    {'title': 'Data Storage', 'content': 'Requirements for secure data storage', 'order': 2},
                    {'title': 'Data Access', 'content': 'Rules for accessing sensitive data', 'order': 3},
                ]
            },
            {
                'name': 'Workplace Safety Standards',
                'description': 'Standards for maintaining a safe working environment',
                'status': 'in_progress',
                'articles': [
                    {'title': 'Emergency Procedures', 'content': 'Protocols for emergency situations', 'order': 1},
                    {'title': 'Equipment Safety', 'content': 'Guidelines for safe equipment usage', 'order': 2},
                ]
            },
            {
                'name': 'Financial Compliance Guidelines',
                'description': 'Guidelines for financial reporting and compliance',
                'status': 'pending',
                'articles': [
                    {'title': 'Financial Reporting', 'content': 'Requirements for financial reports', 'order': 1},
                    {'title': 'Audit Procedures', 'content': 'Process for financial audits', 'order': 2},
                    {'title': 'Record Keeping', 'content': 'Standards for financial record keeping', 'order': 3},
                ]
            },
            {
                'name': 'IT Security Policy',
                'description': 'Policies for maintaining IT security',
                'status': 'draft',
                'articles': [
                    {'title': 'Password Policy', 'content': 'Requirements for password creation and management', 'order': 1},
                    {'title': 'Network Security', 'content': 'Guidelines for network security', 'order': 2},
                ]
            },
            {
                'name': 'Environmental Compliance',
                'description': 'Regulations for environmental protection',
                'status': 'rejected',
                'articles': [
                    {'title': 'Waste Management', 'content': 'Procedures for waste disposal', 'order': 1},
                    {'title': 'Energy Usage', 'content': 'Guidelines for energy conservation', 'order': 2},
                ]
            }
        ]

        # Create regulations and articles
        for reg_data in regulations_data:
            # Create regulation
            regulation = Regulation.objects.create(
                name=reg_data['name'],
                description=reg_data['description'],
                status=reg_data['status'],
                created_by=maker,
                date_created=datetime.now() - timedelta(days=random.randint(1, 30))
            )
            
            # Assign random departments
            num_depts = random.randint(1, len(departments))
            regulation.assigned_departments.add(*random.sample(departments, num_depts))
            
            # Create articles
            for article_data in reg_data['articles']:
                Article.objects.create(
                    regulation=regulation,
                    title=article_data['title'],
                    content=article_data['content'],
                    order=article_data['order']
                )

        self.stdout.write(self.style.SUCCESS('Successfully populated database with sample regulations and articles')) 