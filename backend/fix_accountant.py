import os
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_cJi4s5TXWZUP@ep-delicate-cloud-az3ascqk-pooler.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'
import django
django.setup()

from apps.accounts.models import User, InstitutionMembership, RoleAssignment, Role

print("=" * 60)
print("FIXING ACCOUNTANT ROLE")
print("=" * 60)

accountant = User.objects.filter(username="DEG-EMP-00031").first()
if accountant:
    print("User: " + accountant.username + ", ID: " + str(accountant.id))
    print("primary_role: " + str(accountant.primary_role))
    print("institution_id: " + str(accountant.institution_id))
    
    memberships = accountant.get_active_memberships()
    print("Active memberships: " + str(memberships.count()))
    for m in accountant.get_active_memberships():
        roles = list(m.role_assignments.values_list('role', flat=True))
        print("  Membership: inst=" + m.institution.name + " (ID: " + str(m.institution.id) + "), roles=" + str(roles))
    
    # Fix role assignment for institution 2 (Demo Education Group)
    membership = InstitutionMembership.objects.filter(user=accountant, institution_id=2).first()
    if membership:
        role_assignment = RoleAssignment.objects.filter(membership=membership).first()
        if role_assignment:
            print("Current role for inst 2: " + role_assignment.role)
            if role_assignment.role != 'accountant':
                role_assignment.role = 'accountant'
                role_assignment.save()
                print("Fixed: role = accountant")
            else:
                print("Already correct: role = accountant")
        else:
            from apps.accounts.models import RoleAssignment
            RoleAssignment.objects.create(membership=membership, role='accountant')
            print("Created RoleAssignment with role=accountant")
    else:
        print("No membership found for institution 2")
    
    accountant.refresh_from_db()
    print("After: primary_role = " + str(accountant.primary_role))

    # Verify
    membership = InstitutionMembership.objects.filter(user=accountant, institution_id=2).first()
    if membership:
        roles = list(membership.role_assignments.values_list('role', flat=True))
        print("Roles for inst 2: " + str(roles))

print("\nDone!")