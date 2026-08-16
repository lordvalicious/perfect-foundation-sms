from rest_framework import serializers

from apps.accounts.models import User

from .models import Announcement, Message, Notification


def participant_data(user):
    """Lightweight participant object used by message serializers."""
    if user is None:
        return None

    return {
        "id": user.id,
        "name": user.get_full_name() or user.username,
        "role": user.primary_role or "user",
        "photo_url": user.photo.url if user.photo else None,
    }


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


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()
    recipient = serializers.SerializerMethodField()
    recipient_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="recipient",
        write_only=True,
    )
    reply_count = serializers.SerializerMethodField()
    direction = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id",
            "subject",
            "body",
            "parent",
            "sender",
            "recipient",
            "recipient_id",
            "is_read",
            "read_at",
            "sent_at",
            "reply_count",
            "direction",
        ]
        read_only_fields = [
            "sender",
            "is_read",
            "read_at",
            "sent_at",
            "reply_count",
            "direction",
        ]

    def get_sender(self, obj):
        return participant_data(obj.sender)

    def get_recipient(self, obj):
        return participant_data(obj.recipient)

    def get_reply_count(self, obj):
        if not hasattr(obj, "_reply_count"):
            obj._reply_count = obj.replies.count()
        return obj._reply_count

    def get_direction(self, obj):
        request = self.context.get("request")

        if request and request.user.is_authenticated:
            if obj.sender_id == request.user.id:
                return "sent"
            return "inbox"

        return "inbox"

    def validate(self, attrs):
        request = self.context.get("request")

        recipient = attrs.get("recipient")

        if request and recipient is not None:
            if recipient.id == request.user.id:
                raise serializers.ValidationError(
                    {"recipient": "You cannot send a message to yourself."}
                )

        if not (attrs.get("subject") or "").strip():
            raise serializers.ValidationError(
                {"subject": "Subject is required."}
            )

        return attrs

    def create(self, validated_data):
        request = self.context.get("request")

        if request and request.user.is_authenticated:
            validated_data["sender"] = request.user

        return Message.objects.create(**validated_data)


class MessageRecipientSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    role = serializers.CharField()
    photo_url = serializers.CharField(allow_null=True)
