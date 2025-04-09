import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'compliance_platform.settings')
django.setup()

from core.models import Department, Regulation

def check_departments():
    print("\n=== DEPARTMENTS IN DATABASE ===\n")
    
    departments = Department.objects.all()
    if not departments:
        print("No departments found in database.")
        return
    
    for dept in departments:
        print(f"ID: {dept.id}")
        print(f"Name: {dept.name}")
        print(f"Description: {dept.description}")
        print(f"Created: {dept.created_at}")
        
        # Check users assigned to this department
        users = dept.users.all()
        if users:
            print("Users:")
            for user in users:
                print(f"  - {user.username} ({user.role})")
        else:
            print("Users: None")
        
        # Check regulations assigned to this department
        regulations = dept.assigned_regulations.all()
        if regulations:
            print("Regulations:")
            for reg in regulations:
                print(f"  - {reg.name} (Status: {reg.status})")
        else:
            print("Regulations: None")
        
        print("-" * 30)

if __name__ == '__main__':
    check_departments() 