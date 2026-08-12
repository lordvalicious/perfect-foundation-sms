from rest_framework import serializers

from .models import Announcement, Notification


class AnnouncementSerializer(serializers.ModelSerializer):
    campus_name = serializers.CharField(
        source="campus.name",
        read_only=True,
        default="",
    )
    class_name = serializers.CharField(
        source="class_obj.name",
        read_only=True,
        default="",
    )
    section_name = serializers.CharField(
        source="section.name",
        read_only=True,
        default="",
    )
    category_display = serializers.CharField(
        source="get_category_display",
        read_only=True,
    )
    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    class Meta:
        model = Announcement
        fields = [
            "id",
            "title",
            "message",
            "category",
            "category_display",
            "campus",
            "campus_name",
            "class_obj",
            "class_name",
            "section",
            "section_name",
            "audience_roles",
            "status",
            "status_display",
            "published_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["published_at"]

    def create(self, validated_data):
        from django.core.exceptions import ValidationError as ModelValidationError

        request = self.context.get("request")

        if request and request.user.is_authenticated:
            validated_data["created_by"] = request.user

        try:
            announcement = Announcement.objects.create(**validated_data)
        except ModelValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)

        if announcement.status == "published":
            announcement.notify()

        return announcement

    def update(self, instance, validated_data):
        from django.core.exceptions import ValidationError as ModelValidationError

        was_published = instance.status == "published"

        for key, value in validated_data.items():
            setattr(instance, key, value)

        try:
            instance.save()
        except ModelValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)

        if not was_published and instance.status == "published":
            instance.notify()

        return instance


class NotificationSerializer(serializers.ModelSerializer):
    notification_type_display = serializers.CharField(
        source="get_notification_type_display",
        read_only=True,
    )

    class Meta:
        model = Notification
        fields = [
            "id",
            "title",
            "message",
            "notification_type",
            "notification_type_display",
            "link",
            "is_read",
            "created_at",
        ]
