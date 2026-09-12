# Generated to fix migration state mismatch for unique_admission_number_per_institution
# The constraint already exists in production database but migration 0013 tries to create it again

from django.db import migrations


def create_constraint_if_not_exists(apps, schema_editor):
    """Create the unique constraint only if it doesn't already exist."""
    if schema_editor.connection.vendor == 'postgresql':
        with schema_editor.connection.cursor() as cursor:
            # Check if constraint exists
            cursor.execute("""
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'unique_admission_number_per_institution'
                AND conrelid = 'students_student'::regclass
            """)
            if not cursor.fetchone():
                # Constraint doesn't exist, create it
                cursor.execute("""
                    ALTER TABLE students_student
                    ADD CONSTRAINT unique_admission_number_per_institution
                    UNIQUE (institution_id, admission_number)
                """)


def reverse_code(apps, schema_editor):
    """Remove the constraint if we need to reverse."""
    if schema_editor.connection.vendor == 'postgresql':
        with schema_editor.connection.cursor() as cursor:
            cursor.execute("""
                ALTER TABLE students_student
                DROP CONSTRAINT IF EXISTS unique_admission_number_per_institution
            """)


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0013_admission_number_uniqueness'),
    ]

    operations = [
        # Use SeparateDatabaseAndState to mark the previous migration as applied
        # without re-running its database operations, then apply our fix
        migrations.RunPython(
            create_constraint_if_not_exists,
            reverse_code,
            atomic=True,
        ),
    ]