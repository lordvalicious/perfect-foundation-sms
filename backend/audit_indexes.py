import django, os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.test')
sys.path.insert(0, '.')
django.setup()

# Directly import and check more models
models_to_check = [
    ('apps.students.models', 'Student', 'students_student'),
    ('apps.exams.models', 'Exam', 'exams_exam'),
    ('apps.exams.models', 'StudentResult', 'exams_studentresult'),
    ('apps.exams.models', 'PracticalResult', 'exams_practicalresult'),
    ('apps.library.models', 'Book', 'library_book'),
    ('apps.library.models', 'BookCopy', 'library_bookcopy'),
    ('apps.hostel.models', 'Room', 'hostel_room'),
    ('apps.hostel.models', 'Hostel', 'hostel_hostel'),
    ('apps.lms.models', 'Course', 'lms_course'),
    ('apps.lms.models', 'Lesson', 'lms_lesson'),
    ('apps.lms.models', 'Quiz', 'lms_quiz'),
    ('apps.accounts.models', 'StaffProfile', 'accounts_staffprofile'),
    ('apps.accounts.models', 'Teacher', 'accounts_teacher'),
]

print("=== Model Index Audit ===\n")
for module_path, model_name, db_table in models_to_check:
    try:
        # Dynamically import
        parts = module_path.split('.')
        mod = __import__(parts[0])
        for part in parts[1:]:
            mod = getattr(mod, part)
        
        model = getattr(mod, model_name)
        indexes = model._meta.indexes
        
        print(f"{model_name} ({db_table}):")
        print(f"  Total explicit indexes: {len(indexes)}")
        for i, idx in enumerate(indexes):
            idx_name = idx.name or f"unnamed_{i}"
            idx_fields = [str(f) for f in idx.fields]
            print(f"  {i+1}. {idx_name}: {idx_fields}")
        if not indexes:
            print(f"  NO explicit indexes - relying on default PK")
        print()
    except Exception as e:
        print(f"{model_name}: ERROR - {e}")

print("=== Done ===")