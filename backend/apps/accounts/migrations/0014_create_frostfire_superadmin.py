# Generated migration to create FrostFire superadmin
from django.db import migrations

def create_frostfire_superadmin(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    Role = apps.get_model('accounts', 'Role')
    RoleAssignment = apps.get_model('accounts', 'RoleAssignment')
    InstitutionMembership = apps.get_model('accounts', 'InstitutionMembership')
    School = apps.get_model('schools', 'School')

    # Create FrostFire superadmin
    user, created = User.objects.get_or_create(
        username='FrostFire',
        defaults={
            'email': 'lordvalicious@gmail.com',
            'first_name': 'Frost',
            'last_name': 'Fire',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True,
        }
    )
    if created:
        user.set_password('ra2a1s345')
        user.save()
    else:
        user.set_password('ra2a1s345')
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()

    # Assign SUPER_ADMIN role
    role, _ = Role.objects.get_or_create(name='SUPER_ADMIN')

    # Get or create school
    school = School.objects.first()
    if school is None:
        school = School.objects.create(
            name='Perfect Foundation',
            code='PF',
            address='Default Address',
            city='Default City',
            is_active=True
        )

    # Create institution membership
    membership, _ = InstitutionMembership.objects.get_or_create(
        user=user,
        school=School.objects.first(),
        defaults={'status': 'active'}
    )

    # Assign SUPER_ADMIN role
    RoleAssignment.objects.get_or_create(
        membership=membership,
        role=role
    )

def reverse_func(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.filter(username='FrostFire').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_merge_20260829_1001'),
    ]

    operations = [
        migrations.RunPython(create_frostfire_superadmin, reverse_func),
    ]