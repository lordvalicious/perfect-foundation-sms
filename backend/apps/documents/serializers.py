from rest_framework import serializers


class UnifiedDocumentSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    entity_type = serializers.CharField()
    entity_id = serializers.IntegerField()
    entity_label = serializers.CharField()
    document_type = serializers.CharField()
    document_type_display = serializers.CharField()
    title = serializers.CharField()
    file_url = serializers.SerializerMethodField()
    notes = serializers.CharField(allow_blank=True)
    expiry_date = serializers.DateField(allow_null=True, required=False)
    uploaded_by_name = serializers.CharField(allow_blank=True)
    created_at = serializers.DateTimeField()

    def get_file_url(self, obj):
        request = self.context.get("request")
        file_val = getattr(obj, "file", None)
        if file_val and hasattr(file_val, "url") and request:
            return request.build_absolute_uri(file_val.url)
        return None
