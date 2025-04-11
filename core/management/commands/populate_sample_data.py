from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import User, Department, Regulation, Article
import random
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Populates the database with sample regulations and articles'

    def handle(self, *args, **kwargs):
        # Clear existing regulations and articles
        self.stdout.write('Clearing existing regulations and articles...')
        Article.objects.all().delete()
        Regulation.objects.all().delete()

        # Create a compliance maker user if not exists
        maker, created = User.objects.get_or_create(
            username='compliance_maker',
            defaults={
                'email': 'maker@example.com',
                'first_name': 'Compliance',
                'last_name': 'Maker',
                'role': 'compliance_maker',
                'is_staff': True
            }
        )

        # Create some departments if they don't exist
        departments = []
        department_names = [
            'Finance', 'HR', 'IT', 'Legal', 'Operations',
            'Marketing', 'Sales', 'R&D', 'Compliance', 'Risk Management'
        ]
        
        for name in department_names:
            dept, created = Department.objects.get_or_create(name=name)
            departments.append(dept)

        # Sample regulation data
        regulations_data = [
            {
                'name': 'Data Protection Regulation',
                'reference': 'REG-2024-001',
                'description': 'Regulation for handling and protecting sensitive data',
                'status': 'approved',
                'articles': [
                    {'title': 'Data Collection', 'content': 'Guidelines for collecting user data', 'type': 'regulation', 'reference': '1'},
                    {'title': 'Data Storage', 'content': 'Requirements for secure data storage', 'type': 'regulation', 'reference': '2'},
                    {'title': 'Data Access', 'content': 'Rules for accessing sensitive data', 'type': 'regulation', 'reference': '3'},
                ]
            },
            {
                'name': 'Workplace Safety Standards',
                'reference': 'REG-2024-002',
                'description': 'Standards for maintaining a safe working environment',
                'status': 'in_progress',
                'articles': [
                    {'title': 'Emergency Procedures', 'content': 'Protocols for emergency situations', 'type': 'rule', 'reference': '1'},
                    {'title': 'Equipment Safety', 'content': 'Guidelines for safe equipment usage', 'type': 'rule', 'reference': '2'},
                ]
            },
            {
                'name': 'Financial Compliance Guidelines',
                'reference': 'REG-2024-003',
                'description': 'Guidelines for financial reporting and compliance',
                'status': 'pending',
                'articles': [
                    {'title': 'Financial Reporting', 'content': 'Requirements for financial reports', 'type': 'guideline', 'reference': '1'},
                    {'title': 'Audit Procedures', 'content': 'Process for financial audits', 'type': 'guideline', 'reference': '2'},
                    {'title': 'Record Keeping', 'content': 'Standards for financial record keeping', 'type': 'guideline', 'reference': '3'},
                ]
            },
            {
                'name': 'IT Security Policy',
                'reference': 'REG-2024-004',
                'description': 'Policies for maintaining IT security',
                'status': 'draft',
                'articles': [
                    {'title': 'Password Policy', 'content': 'Requirements for password creation and management', 'type': 'regulation', 'reference': '1'},
                    {'title': 'Network Security', 'content': 'Guidelines for network security', 'type': 'regulation', 'reference': '2'},
                ]
            },
            {
                'name': 'Environmental Compliance',
                'reference': 'REG-2024-005',
                'description': 'Regulations for environmental protection',
                'status': 'rejected',
                'articles': [
                    {'title': 'Waste Management', 'content': 'Procedures for waste disposal', 'type': 'regulation', 'reference': '1'},
                    {'title': 'Energy Usage', 'content': 'Guidelines for energy conservation', 'type': 'regulation', 'reference': '2'},
                ]
            }
        ]

        # Create regulations and articles
        for reg_data in regulations_data:
            # Create regulation
            regulation = Regulation.objects.create(
                name=reg_data['name'],
                reference=reg_data['reference'],
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
                    type=article_data['type'],
                    reference=article_data['reference']
                )
            
            self.stdout.write(self.style.SUCCESS(f'Created regulation: {regulation.name}'))

        self.stdout.write(self.style.SUCCESS('Successfully populated the database with sample data')) 