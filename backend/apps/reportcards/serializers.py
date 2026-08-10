from rest_framework import serializers

from .models import GradeAmendment, GradeBand, GradeScale, ReportCard


class GradeBandSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeBand
        fields = [
            "id",
            "letter_grade",
            "grade_point",
            "minimum_percentage",
            "maximum_percentage",
        ]


class GradeScaleSerializer(serializers.ModelSerializer):
    bands = GradeBandSerializer(many=True, read_only=True)

    class Meta:
        model = GradeScale
        fields = [
            "id",
            "name",
            "is_default",
            "bands",
            "created_at",
            "updated_at",
        ]


class ReportCardSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="student.full_name",
        read_only=True,
    )
    admission_number = serializers.CharField(
        source="student.admission_number",
        read_only=True,
    )
    exam_name = serializers.CharField(
        source="exam.name",
        read_only=True,
    )
    exam_type_display = serializers.CharField(
        source="exam.get_exam_type_display",
        read_only=True,
    )
    campus_name = serializers.CharField(
        source="exam.campus.name",
        read_only=True,
    )
    class_name = serializers.CharField(
        source="exam.class_obj.name",
        read_only=True,
    )
    overall_result = serializers.CharField(
        read_only=True,
    )
    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    class Meta:
        model = ReportCard
        fields = [
            "id",
            "student",
            "student_name",
            "admission_number",
            "exam",
            "exam_name",
            "exam_type_display",
            "campus_name",
            "class_name",
            "position",
            "status",
            "status_display",
            "published_at",
            "can_edit",
            "subject_count",
            "total_marks",
            "maximum_marks",
            "percentage",
            "grade",
            "grade_point",
            "is_pass",
            "overall_result",
            "is_complete",
            "teacher_remarks",
            "principal_remarks",
            "created_at",
            "updated_at",
        ]


class GradeAmendmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="report_card.student.full_name",
        read_only=True,
    )
    exam_name = serializers.CharField(
        source="report_card.exam.name",
        read_only=True,
    )
    subject_name = serializers.CharField(
        source="exam_subject.subject.name",
        read_only=True,
    )
    amended_by_name = serializers.SerializerMethodField()

    class Meta:
        model = GradeAmendment
        fields = [
            "id",
            "report_card",
            "exam_subject",
            "student_result",
            "student_name",
            "exam_name",
            "subject_name",
            "previous_obtained_marks",
            "new_obtained_marks",
            "previous_grade",
            "new_grade",
            "reason",
            "amended_by",
            "amended_by_name",
            "created_at",
        ]

    def get_amended_by_name(self, obj):
        if obj.amended_by is None:
            return None

        return (
            obj.amended_by.get_full_name()
            or obj.amended_by.username
        )


class GradeAmendmentCreateSerializer(serializers.Serializer):
    report_card = serializers.PrimaryKeyRelatedField(
        queryset=ReportCard.objects.all(),
    )

    student_result = serializers.PrimaryKeyRelatedField(
        queryset=GradeAmendment.student_result.field.remote_field.model.objects.all()
    )

    new_obtained_marks = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        min_value=0,
    )

    reason = serializers.CharField(
        min_length=5,
    )

    def validate(self, attrs):
        from decimal import Decimal

        from apps.exams.models import StudentResult

        report_card = attrs["report_card"]
        student_result = attrs["student_result"]

        if report_card.status != "published":
            raise serializers.ValidationError(
                "Only published report cards can be amended."
            )

        result = (
            StudentResult.objects
            .select_related("exam_subject")
            .filter(
                pk=student_result.pk,
                exam=report_card.exam,
                student=report_card.student,
            )
            .first()
        )

        if result is None:
            raise serializers.ValidationError(
                "The result does not belong to this report card."
            )

        new_marks = attrs["new_obtained_marks"]

        if new_marks > Decimal(str(result.exam_subject.maximum_marks)):
            raise serializers.ValidationError(
                "New marks cannot exceed the maximum for the subject."
            )

        attrs["_result"] = result

        return attrs
