from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import apply_campus_scope
from apps.accounts.permissions import IsAccountantRole
from apps.hr.models import EmployeeDocument
from apps.students.models import StudentDocument

from .serializers import UnifiedDocumentSerializer

STUDENT_DOC_TYPE_LABELS = dict(StudentDocument.DOCUMENT_TYPE_CHOICES)


class DocumentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        entity_type = request.query_params.get("entity_type", "")
        document_type = request.query_params.get("document_type", "")
        search = request.query_params.get("search", "").strip()

        docs = []

        show_student = entity_type in ("", "student")
        show_employee = entity_type in ("", "employee")

        if show_student:
            qs = StudentDocument.objects.select_related(
                "student", "uploaded_by"
            ).all()

            campus_filter = request.query_params.get("campus")
            if campus_filter:
                qs = qs.filter(student__enrollments__campus_id=campus_filter).distinct()

            if document_type:
                qs = qs.filter(document_type=document_type)

            if search:
                qs = qs.filter(
                    Q(title__icontains=search)
                    | Q(student__first_name__icontains=search)
                    | Q(student__last_name__icontains=search)
                    | Q(student__admission_number__icontains=search)
                )

            for d in qs:
                student_name = f"{d.student.first_name} {d.student.last_name}".strip()
                docs.append({
                    "id": d.id,
                    "entity_type": "student",
                    "entity_id": d.student_id,
                    "entity_label": f"{student_name} ({d.student.admission_number})",
                    "document_type": d.document_type,
                    "document_type_display": STUDENT_DOC_TYPE_LABELS.get(d.document_type, d.document_type),
                    "title": d.title,
                    "file": d.file,
                    "notes": d.notes,
                    "expiry_date": None,
                    "uploaded_by_name": (
                        f"{d.uploaded_by.first_name} {d.uploaded_by.last_name}".strip()
                        if d.uploaded_by else ""
                    ),
                    "created_at": d.created_at,
                })

        if show_employee:
            qs = EmployeeDocument.objects.select_related(
                "employee", "uploaded_by"
            ).all()

            campus_filter = request.query_params.get("campus")
            if campus_filter:
                qs = qs.filter(employee__campus_id=campus_filter).distinct()

            if document_type:
                qs = qs.filter(document_type=document_type)

            if search:
                qs = qs.filter(
                    Q(title__icontains=search)
                    | Q(employee__first_name__icontains=search)
                    | Q(employee__last_name__icontains=search)
                    | Q(employee__employee_id__icontains=search)
                )

            for d in qs:
                emp_name = f"{d.employee.first_name} {d.employee.last_name}".strip()
                docs.append({
                    "id": d.id,
                    "entity_type": "employee",
                    "entity_id": d.employee_id,
                    "entity_label": f"{emp_name} ({d.employee.employee_id})",
                    "document_type": d.document_type,
                    "document_type_display": d.document_type,
                    "title": d.title,
                    "file": d.file,
                    "notes": d.notes,
                    "expiry_date": d.expiry_date,
                    "uploaded_by_name": (
                        f"{d.uploaded_by.first_name} {d.uploaded_by.last_name}".strip()
                        if d.uploaded_by else ""
                    ),
                    "created_at": d.created_at,
                })

        docs.sort(key=lambda x: x["created_at"], reverse=True)

        return Response(UnifiedDocumentSerializer(docs, many=True, context={"request": request}).data)


class DocumentUploadView(APIView):
    permission_classes = [IsAuthenticated, IsAccountantRole]

    def post(self, request):
        entity_type = request.data.get("entity_type")
        file = request.data.get("file")

        if not entity_type or not file:
            return Response(
                {"detail": "entity_type and file are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if entity_type == "student":
            student_id = request.data.get("entity_id")
            if not student_id:
                return Response(
                    {"detail": "entity_id is required for student documents."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            from apps.students.models import Student
            try:
                student = Student.objects.get(pk=student_id)
            except Student.DoesNotExist:
                return Response(
                    {"detail": "Student not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            doc = StudentDocument.objects.create(
                student=student,
                document_type=request.data.get("document_type", "other"),
                title=request.data.get("title", file.name),
                file=file,
                notes=request.data.get("notes", ""),
                uploaded_by=request.user,
            )

        elif entity_type == "employee":
            employee_id = request.data.get("entity_id")
            if not employee_id:
                return Response(
                    {"detail": "entity_id is required for employee documents."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            from apps.hr.models import Employee
            try:
                employee = Employee.objects.get(pk=employee_id)
            except Employee.DoesNotExist:
                return Response(
                    {"detail": "Employee not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            doc = EmployeeDocument.objects.create(
                employee=employee,
                document_type=request.data.get("document_type", "other"),
                title=request.data.get("title", file.name),
                file=file,
                notes=request.data.get("notes", ""),
                expiry_date=request.data.get("expiry_date") or None,
                uploaded_by=request.user,
            )
        else:
            return Response(
                {"detail": "Invalid entity_type. Must be 'student' or 'employee'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"id": doc.id, "detail": "Document uploaded successfully."},
            status=status.HTTP_201_CREATED,
        )
