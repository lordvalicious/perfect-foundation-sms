from rest_framework import serializers

from .models import IdCard


class IdCardSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(source="campus.name", read_only=True)
    student_name = serializers.SerializerMethodField()
    teacher_name = serializers.SerializerMethodField()
    staff_name = serializers.SerializerMethodField()
    creator_name = serializers.SerializerMethodField()

    class Meta:
        model = IdCard
        fields = [
            "id",
            "holder_type",
            "student",
            "student_name",
            "teacher",
            "teacher_name",
            "staff",
            "staff_name",
            "campus",
            "campus_name",
            "card_number",
            "barcode_data",
            "issue_date",
            "expiry_date",
            "status",
            "photo",
            "creator_name",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "card_number",
            "barcode_data",
            "issue_date",
            "expiry_date",
            "status",
            "created_by",
            "created_at",
        ]

    def get_student_name(self, obj):
        return self._person_name(obj.student)

    def get_teacher_name(self, obj):
        return self._person_name(obj.teacher)

    def get_staff_name(self, obj):
        return self._person_name(obj.staff)

    def get_creator_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return "—"

    @staticmethod
    def _person_name(person):
        if person is None:
            return None
        full = person.full_name or ""
        return full or str(person)

    def validate(self, attrs):
        holder_type = attrs.get("holder_type")
        if holder_type == "student" and not attrs.get("student"):
            raise serializers.ValidationError({"student": "Student is required."})
        if holder_type == "teacher" and not attrs.get("teacher"):
            raise serializers.ValidationError({"teacher": "Teacher is required."})
        if holder_type == "staff" and not attrs.get("staff"):
            raise serializers.ValidationError({"staff": "Staff is required."})
        return attrs