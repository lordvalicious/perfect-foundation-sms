import sys
import os

# Add the backend directory to Python path at the very start
sys.path.insert(0, r'C:\Users\Ryuk\Documents\perfect-foundation-sms\backend')

# Set the Django settings module BEFORE django.setup()
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.test'

# Now do django.setup
import django
django.setup()

# Now import the models
from accounts.models import User, InstitutionMembership, Role, RoleAssignment

# Get all users with basic info
users = User.objects.all().values(
    'username', 
    'email', 
    'is_active', 
    'is_superuser', 
    'primary_role'
)

# Get institution memberships with roles
memberships = InstitutionMembership.objects.select_related(
    'user', 'institution'
).values(
    'user__username', 
    'user__email', 
    'institution__name', 
    'status',
    'role_assignments__role'
)

# Build user data
user_data = {}
for user in users:
    username = user['username']
    user_data[username] = {
        'email': user.get('email'),
        'is_active': user['is_active'],
        'is_superuser': user['is_superuser'],
        'primary_role': user.get('primary_role'),
        'memberships': [],
        'role_assignments': []
    }

# Build membership data
for mem in memberships:
    username = mem['user__username']
    if username in user_data:
        user_data[username]['memberships'].append({
            'institution': mem['institution__name'],
            'status': mem['status']
        })

# Build role assignment data  
role_assignments = RoleAssignment.objects.select_related(
    'membership__user', 'membership__institution', 'role'
).values(
    'membership__user__username',
    'membership__user__email',
    'membership__institution__name',
    'role__name',
    'membership__status'
)

for ra in role_assignments:
    username = ra['membership__user__username']
    if username in user_data:
        user_data[username]['role_assignments'].append({
            'role': ra['role__name'],
            'institution': ra['membership__institution__name'],
            'membership_status': ra['membership__status']
        })

# Print report
print("=" * 80)
print("USER ACCOUNT AUDIT REPORT")
print("=" * 80)
print()

# Print header
header_fmt = "{:<20} {:<30} {:<8} {:<10} {:<15} {:<25} {:<30}"
print(header_fmt.format(
    "Username", "Email", "Active", "Superuser", "Primary Role", 
    "Memberships", "Role Assignments"
))
print("-" * 160)

# Print each user
for username, data in sorted(user_data.items()):
    memberships_str = "; ".join([f"{m['institution']}({m['status']})" for m in data['memberships']]) or "None"
    roles_str = "; ".join([f"{r['role']}({r['institution']})" for r in data['role_assignments']]) or "None"
    print(header_fmt.format(
        username, 
        str(data['email'])[:30] if data['email'] else "",
        str(data['is_active']),
        str(data['is_superuser']),
        str(data['primary_role'])[:15] if data['primary_role'] else "",
        memberships_str,
        roles_str
    ))

print()
print("=" * 80)
print("ROLE SUMMARY")
print("=" * 80)

# Group by primary_role
role_groups = {}
for username, data in user_data.items():
    role = data['primary_role']
    if role not in role_groups:
        role_groups[role] = []
    role_groups[role].append(username)

for role, usernames in sorted(role_groups.items()):
    active_count = sum(1 for u in usernames if user_data[u]['is_active'])
    superuser_count = sum(1 for u in usernames if user_data[u]['is_superuser'])
    print(f"Role: {role:<20} Active accounts: {active_count}/{len(usernames)} Superuser accounts: {superuser_count}")
    for u in usernames:
        if user_data[u]['is_superuser'] or user_data[u]['primary_role'] != role:
            print(f"  - {u}: is_superuser={user_data[u]['is_superuser']}, primary_role={user_data[u]['primary_role']}")

# Check for accounts with multiple role assignments
print()
print("Accounts with multiple role assignments:")
for username, data in user_data.items():
    if len(data['role_assignments']) > 1:
        roles_list = "; ".join([r['role'] for r in data['role_assignments']])
        print(f"  {username}: {roles_list}")

# Check for accounts with unexpectedly elevated role combinations
print()
print("Accounts with elevated role combinations (superuser + other roles):")
for username, data in user_data.items():
    if data['is_superuser'] and data['primary_role'] and data['primary_role'] != 'super_admin':
        print(f"  {username}: is_superuser=True, primary_role={data['primary_role']}")

# Check for accounts with no primary role
print()
print("Accounts with no primary role:")
for username, data in user_data.items():
    if not data['primary_role']:
        print(f"  {username}: primary_role is None/empty")

# Check for inactive accounts
print()
print("Inactive accounts:")
for username, data in user_data.items():
    if not data['is_active']:
        print(f"  {username}: is_active=False, primary_role={data['primary_role']}")

print()
print("=" * 80)