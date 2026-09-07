with open(r'C:\Users\Ryuk\Documents\perfect-foundation-sms\backend\apps\schools\views.py', 'r') as f:
    content = f.read()

# Replace perform_create method
old_perform_create = '''    def perform_create(self, serializer):
        # Check if admin data is provided in the request
        admin_data = self.request.data.get("admin", {})
        
        serializer.save(school=self._resolve_school())
        
        # If admin data is provided, create the admin user linked to the school
        if admin_data:
            try:
                self._create_admin_user(serializer.validated_data, admin_data)
            except Exception:
                # Log the error but don't fail the campus creation
                # The campus was created successfully even if admin provisioning failed
                pass'''

new_perform_create = '''    def perform_create(self, serializer):
        # Check if admin data is provided in the request
        admin_data = self.request.data.get("admin", {})

        serializer.save(school=self._resolve_school())

        # If admin data is provided, create the admin user linked to the school
        if admin_data:
            admin_user, admin_password = self._create_admin_user(serializer.validated_data, admin_data)
            # Store admin credentials in serializer context for response
            serializer.context["admin_credentials"] = {
                "username": admin_user.username,
                "email": admin_user.email,
                "password": admin_password,
                "position": admin_data.get("position", "").strip().lower(),
            }'''

content = content.replace(old_perform_create, new_perform_create)

# Replace _create_admin_user method
old_create = '''    def _create_admin_user(self, validated_data, admin_data):
        """Create a user account and assign CAMPUS_ADMIN role linked to the school."""
        from django.db import transaction
        from django.db.utils import IntegrityError
        from rest_framework.exceptions import ValidationError
        from apps.accounts.services import create_user_with_username
        from apps.accounts.models import Role, InstitutionMembership, RoleAssignment

        username = admin_data.get("username", "").strip()
        email = admin_data.get("email", "").strip()
        password = admin_data.get("password", "")
        first_name = admin_data.get("first_name", "")
        last_name = admin_data.get("last_name", "")
        phone = admin_data.get("phone", "")

        if not username or not email or not password:
            raise ValidationError(
                {"admin": "Username, email, and password are required for admin creation."}
            )

        try:
            with transaction.atomic():
                school = self._resolve_school()
                user, generated_username, generated_password = create_user_with_username(
                    base=username,
                    institution=school,
                    email=email,
                    password=password,
                    first_name=first_name or "Campus",
                    last_name=last_name or school.name,
                    must_change_password=False,
                )
                if phone:
                    user.phone = phone
                    user.save(update_fields=["phone"])

                membership, _ = InstitutionMembership.objects.get_or_create(
                    user=user,
                    institution=school,
                    defaults={"status": "active"},
                )

                RoleAssignment.objects.get_or_create(
                    membership=membership,
                    role=Role.CAMPUS_ADMIN,
                )

                return user, generated_password
        except IntegrityError:
            raise ValidationError(
                {"admin": "Failed to create admin user - username or email already exists."}
            )'''

new_create = '''    def _create_admin_user(self, validated_data, admin_data):
        """Create a user account and assign Principal/Vice Principal/Campus Admin role linked to the school."""
        from django.db import transaction
        from django.db.utils import IntegrityError
        from rest_framework.exceptions import ValidationError
        from apps.accounts.services import create_user_with_username
        from apps.accounts.models import Role, InstitutionMembership, RoleAssignment

        username = admin_data.get("username", "").strip()
        email = admin_data.get("email", "").strip()
        password = admin_data.get("password", "")
        first_name = admin_data.get("first_name", "")
        last_name = admin_data.get("last_name", "")
        phone = admin_data.get("phone", "")
        position = admin_data.get("position", "").strip().lower()

        if not username or not email or not password:
            raise ValidationError(
                {"admin": "Username, email, and password are required for admin creation."}
            )

        if position not in ("principal", "vice_principal"):
            raise ValidationError(
                {"admin": "Position must be 'principal' or 'vice_principal'."}
            )

        role_map = {
            "principal": Role.PRINCIPAL,
            "vice_principal": Role.VICE_PRINCIPAL,
        }

        try:
            with transaction.atomic():
                school = self._resolve_school()
                user, generated_username, generated_password = create_user_with_username(
                    base=username,
                    institution=school,
                    email=email,
                    password=password,
                    first_name=first_name or "Campus",
                    last_name=last_name or school.name,
                    must_change_password=False,
                )
                if phone:
                    user.phone = phone
                    user.save(update_fields=["phone"])

                membership, _ = InstitutionMembership.objects.get_or_create(
                    user=user,
                    institution=school,
                    defaults={"status": "active"},
                )

                # Check for existing Principal assignment if assigning Principal
                if position == "principal":
                    existing_principal = RoleAssignment.objects.filter(
                        membership__institution=school,
                        role=Role.PRINCIPAL,
                    ).first()
                    if existing_principal:
                        raise ValidationError(
                            {"admin": "A Principal already exists for this school. Only one Principal allowed."}
                        )

                RoleAssignment.objects.get_or_create(
                    membership=membership,
                    role=role_map[position],
                )

                return user, generated_password
        except IntegrityError:
            raise ValidationError(
                {"admin": "Failed to create admin user - username or email already exists."}
            )'''

content = content.replace(old_create, new_create)

with open(r'C:\Users\Ryuk\Documents\perfect-foundation-sms\backend\apps\schools\views.py', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
print('Done')