import os
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_cJi4s5TXWZUP@ep-muddy-bar-az3etcoa-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'
import django
django.setup()

from apps.accounts.models import User

print("=" * 60)
print("CHECKING NURSE ACCOUNT (SA-EMP-0002)")
print("=" * 60)

nurse = User.objects.filter(username='SA-EMP-0002').first()
if nurse:
    print(f"User: {nurse.username}")
    print(f"  ID: {nurse.id}")
    print(f"  Email: {nurse.email}")
    print(f"  First Name: {nurse.first_name}")
    print(f"  Last Name: {nurse.last_name}")
    print(f"  Must Change Password: {nurse.must_change_password}")
    print(f"  Is Active: {nurse.is_active}")
    print(f"  Institution: {nurse.institution}")
    print(f"  Primary Role: {nurse.primary_role}")
    
    # Check memberships
    memberships = nurse.get_active_memberships()
    print(f"\nMemberships: {memberships.count()}")
    for m in nurse.get_active_memberships():
        roles = list(m.role_assignments.values_list('role', flat=True))
        print(f"  Institution: {m.institution.name} (ID: {m.institution.id})")
        print(f"  Roles: {list(m.role_assignments.values_list('role', flat=True))}")
        print(f"  Status: {m.status}")
    
    # Check if username exists in multiple institutions
    users_with_same_username = User.objects.filter(username='SA-EMP-0002')
    print(f"\nUsers with username 'SA-EMP-0002': {users_with_same_username.count()}")
    for u in users_with_same_username:
        print(f"  User ID: {u.id}, Username: {u.username}, Institution: {u.institution}, Primary Role: {u.primary_role}")
else:
    print("Nurse account not found!")