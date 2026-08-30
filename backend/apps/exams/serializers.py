from rest_framework import serializers

from .models import (
    Exam,
    ExamSchedule,
    ExamSeating,
    ExamSubject,
    PracticalResult,
    StudentResult,
)


class ExamWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = [
            "id",
            "name",
            "exam_type",
            "academic_year",
            "term",
            "campus",
            "class_obj",
            "start_date",
            "end_date",
            "status",
        ]

    def create(self, validated_data):
        from django.core.exceptions import ValidationError as ModelValidationError

        try:
            return Exam.objects.create(**validated_data)
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


class ExamSerializer(serializers.ModelSerializer):
    exam_type_display = serializers.CharField(
        source="get_exam_type_display",
        read_only=True,
    )
    academic_year_name = serializers.CharField(
        source="academic_year.name",
        read_only=True,
    )
    term_name = serializers.CharField(
        source="term.name",
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
            "term",
            "term_name",
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

    def create(self, validated_data):
        from django.core.exceptions import ValidationError as ModelValidationError

        try:
            return ExamSubject.objects.create(**validated_data)
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


class ExamScheduleSerializer(serializers.ModelSerializer):
    exam_name = serializers.CharField(
        source="exam.name",
        read_only=True,
    )
    section_name = serializers.CharField(
        source="section.name",
        read_only=True,
    )
    class_name = serializers.CharField(
        source="section.class_obj.name",
        read_only=True,
    )
    subject = serializers.SerializerMethodField()
    subject_name = serializers.SerializerMethodField()
    invigilator_name = serializers.CharField(
        source="invigilator.full_name",
        read_only=True,
    )

    class Meta:
        model = ExamSchedule
        fields = [
            "id",
            "exam",
            "exam_name",
            "section",
            "section_name",
            "class_name",
            "exam_subject",
            "subject",
            "subject_name",
            "date",
            "start_time",
            "end_time",
            "room",
            "invigilator",
            "invigilator_name",
            "notes",
            "created_at",
            "updated_at",
        ]

    def get_subject(self, obj):
        if obj.exam_subject is None:
            return None
        return obj.exam_subject.subject_id

    def get_subject_name(self, obj):
        if obj.exam_subject is None:
            return ""
        return obj.exam_subject.subject.name

    def create(self, validated_data):
        from django.core.exceptions import ValidationError as ModelValidationError

        try:
            return ExamSchedule.objects.create(**validated_data)
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


class ExamSeatingSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="student.full_name",
        read_only=True,
    )
    admission_number = serializers.CharField(
        source="student.admission_number",
        read_only=True,
    )
    section_name = serializers.CharField(
        source="section.name",
        read_only=True,
    )

    class Meta:
        model = ExamSeating
        fields = [
            "id",
            "exam",
            "section",
            "section_name",
            "student",
            "student_name",
            "admission_number",
            "seat_number",
            "room",
            "notes",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        from django.core.exceptions import ValidationError as ModelValidationError

        try:
            return ExamSeating.objects.create(**validated_data)
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


class ExamSeatingBulkSerializer(serializers.Serializer):
    """Assign a whole section roster in one call.

    Each item maps a student to a seat. Validation errors are collected
    so a single bad seat does not block the remaining assignments.
    """

    exam = serializers.IntegerField()
    section = serializers.IntegerField()
    items = serializers.ListField(child=serializers.DictField())

    def create(self, validated_data):
        from django.core.exceptions import ValidationError as ModelValidationError

        from .models import ExamSeating

        exam_id = validated_data["exam"]
        section_id = validated_data["section"]
        items = validated_data["items"]

        created = []
        errors = []
        seen_seats = set()
        seen_students = set()

        for raw in items:
            seat_number = raw.get("seat_number")
            student_id = raw.get("student")

            if student_id is None or seat_number in (None, ""):
                errors.append(
                    {
                        "student": student_id,
                        "errors": {
                            "seat_number": "Seat number and student are required."
                        },
                    }
                )
                continue

            try:
                seat_number = int(seat_number)
                if seat_number <= 0:
                    raise ValueError
            except ValueError:
                errors.append(
                    {
                        "student": student_id,
                        "errors": {
                            "seat_number": "Seat number must be a positive integer."
                        },
                    }
                )
                continue

            if (section_id, seat_number) in seen_seats:
                errors.append(
                    {
                        "student": student_id,
                        "errors": {
                            "seat_number": (
                                f"Seat number {seat_number} is already used "
                                "for this section."
                            )
                        },
                    }
                )
                continue

            if student_id in seen_students:
                errors.append(
                    {
                        "student": student_id,
                        "errors": {
                            "student": "Student already has a seat in this batch."
                        },
                    }
                )
                continue

            seen_seats.add((section_id, seat_number))
            seen_students.add(student_id)

            try:
                instance = ExamSeating(
                    exam_id=exam_id,
                    section_id=section_id,
                    student_id=student_id,
                    seat_number=seat_number,
                    room=raw.get("room", ""),
                    notes=raw.get("notes", ""),
                )
                instance.full_clean()
                created.append(instance)
            except ModelValidationError as exc:
                errors.append(
                    {
                        "student": student_id,
                        "errors": exc.message_dict,
                    }
                )

        if errors:
            raise serializers.ValidationError(
                {"items": [f"Student {e.get('student')}: {e['errors']}" for e in errors]}
            )

        return ExamSeating.objects.bulk_create(created)
