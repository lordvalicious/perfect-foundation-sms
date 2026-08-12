from rest_framework import serializers

from .models import Exam, ExamSubject, PracticalResult, StudentResult


class ExamSerializer(serializers.ModelSerializer):
    exam_type_display = serializers.CharField(
        source="get_exam_type_display",
        read_only=True,
    )
    academic_year_name = serializers.CharField(
        source="academic_year.name",
        read_only=True,
    )
    campus_name = serializers.CharField(
        source="campus.name",
        read_only=True,
    )
    class_name = serializers.CharField(
        source="class_obj.name",
        read_only=True,
    )
    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )
    subject_count = serializers.IntegerField(
        source="exam_subjects.count",
        read_only=True,
    )
    result_count = serializers.IntegerField(
        source="results.count",
        read_only=True,
    )

    class Meta:
        model = Exam
        fields = [
            "id",
            "name",
            "exam_type",
            "exam_type_display",
            "academic_year",
            "academic_year_name",
            "campus",
            "campus_name",
            "class_obj",
            "class_name",
            "start_date",
            "end_date",
            "status",
            "status_display",
            "subject_count",
            "result_count",
            "created_at",
            "updated_at",
        ]


class ExamSubjectSerializer(serializers.ModelSerializer):
    exam_name = serializers.CharField(
        source="exam.name",
        read_only=True,
    )
    subject_name = serializers.CharField(
        source="subject.name",
        read_only=True,
    )
    subject_code = serializers.CharField(
        source="subject.code",
        read_only=True,
    )

    class Meta:
        model = ExamSubject
        fields = [
            "id",
            "exam",
            "exam_name",
            "subject",
            "subject_name",
            "subject_code",
            "maximum_marks",
            "passing_marks",
        ]


class StudentResultSerializer(serializers.ModelSerializer):
    exam_name = serializers.CharField(
        source="exam.name",
        read_only=True,
    )
    student_name = serializers.CharField(
        source="student.full_name",
        read_only=True,
    )
    admission_number = serializers.CharField(
        source="student.admission_number",
        read_only=True,
    )
    subject_name = serializers.CharField(
        source="exam_subject.subject.name",
        read_only=True,
    )
    maximum_marks = serializers.IntegerField(
        source="exam_subject.maximum_marks",
        read_only=True,
    )
    passing_marks = serializers.IntegerField(
        source="exam_subject.passing_marks",
        read_only=True,
    )
    practical_marks = serializers.SerializerMethodField()
    combined_marks = serializers.SerializerMethodField()

    class Meta:
        model = StudentResult
        fields = [
            "id",
            "exam",
            "exam_name",
            "student",
            "student_name",
            "admission_number",
            "exam_subject",
            "subject_name",
            "obtained_marks",
            "maximum_marks",
            "passing_marks",
            "is_absent",
            "percentage",
            "grade",
            "is_pass",
            "remarks",
            "practical_marks",
            "combined_marks",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "percentage",
            "grade",
            "is_pass",
        ]

    def get_practical_marks(self, obj):
        practical = (
            PracticalResult.objects
            .filter(
                exam=obj.exam,
                student=obj.student,
                exam_subject=obj.exam_subject,
            )
            .first()
        )

        if practical is None:
            return None

        return {
            "obtained_marks": str(practical.obtained_marks),
            "maximum_marks": practical.maximum_marks,
            "percentage": str(practical.percentage),
            "grade": practical.grade,
            "is_pass": practical.is_pass,
            "remarks": practical.remarks,
            "id": practical.pk,
        }

    def get_combined_marks(self, obj):
        practical = (
            PracticalResult.objects
            .filter(
                exam=obj.exam,
                student=obj.student,
                exam_subject=obj.exam_subject,
            )
            .first()
        )

        if practical is None:
            return None

        total = (
            obj.obtained_marks
            + practical.obtained_marks
        )
        maximum = (
            obj.exam_subject.maximum_marks
            + practical.maximum_marks
        )

        if maximum <= 0:
            percentage = "0.00"
        else:
            percentage = str(
                round(
                    (total / maximum) * 100,
                    2,
                )
            )

        return {
            "total_obtained": str(total),
            "total_maximum": maximum,
            "percentage": percentage,
        }


class StudentResultWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentResult
        fields = [
            "id",
            "exam",
            "student",
            "exam_subject",
            "obtained_marks",
            "is_absent",
            "remarks",
        ]

    def create(self, validated_data):
        from django.core.exceptions import ValidationError as ModelValidationError

        try:
            return StudentResult.objects.create(**validated_data)
        except ModelValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)

    def update(self, instance, validated_data):
        from django.core.exceptions import ValidationError as ModelValidationError

        for key, value in validated_data.items():
            setattr(instance, key, value)

        try:
            instance.save()
        except ModelValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)

        return instance


class PracticalResultSerializer(serializers.ModelSerializer):
    exam_name = serializers.CharField(
        source="exam.name",
        read_only=True,
    )
    student_name = serializers.CharField(
        source="student.full_name",
        read_only=True,
    )
    admission_number = serializers.CharField(
        source="student.admission_number",
        read_only=True,
    )
    subject_name = serializers.CharField(
        source="exam_subject.subject.name",
        read_only=True,
    )

    class Meta:
        model = PracticalResult
        fields = [
            "id",
            "exam",
            "exam_name",
            "student",
            "student_name",
            "admission_number",
            "exam_subject",
            "subject_name",
            "obtained_marks",
            "maximum_marks",
            "passing_marks",
            "is_absent",
            "percentage",
            "grade",
            "is_pass",
            "remarks",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "percentage",
            "grade",
            "is_pass",
        ]

    def create(self, validated_data):
        from django.core.exceptions import ValidationError as ModelValidationError

        try:
            return PracticalResult.objects.create(**validated_data)
        except ModelValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)

    def update(self, instance, validated_data):
        from django.core.exceptions import ValidationError as ModelValidationError

        for key, value in validated_data.items():
            setattr(instance, key, value)

        try:
            instance.save()
        except ModelValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)

        return instance
