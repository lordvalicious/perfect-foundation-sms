from rest_framework import serializers

from .models import Book, BookCopy, BookIssue


class BookCopySerializer(serializers.ModelSerializer):
    class Meta:
        model = BookCopy
        fields = ["id", "barcode", "status"]


class BookSerializer(serializers.ModelSerializer):
    available_copies = serializers.IntegerField(read_only=True)
    issued_copies = serializers.IntegerField(read_only=True)
    copies = BookCopySerializer(many=True, read_only=True)
    category_display = serializers.CharField(
        source="get_category_display",
        read_only=True,
    )

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "author",
            "isbn",
            "publisher",
            "publication_year",
            "category",
            "category_display",
            "description",
            "total_copies",
            "available_copies",
            "issued_copies",
            "copies",
        ]

    def create(self, validated_data):
        total_copies = validated_data.pop("total_copies", 1)
        book = Book.objects.create(total_copies=total_copies, **validated_data)

        for _ in range(total_copies):
            BookCopy.objects.create(book=book)

        return book

    def update(self, instance, validated_data):
        total_copies = validated_data.pop("total_copies", None)

        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()

        if total_copies is not None:
            existing = instance.copies.count()

            if total_copies > existing:
                for _ in range(total_copies - existing):
                    BookCopy.objects.create(book=instance)
            elif total_copies < existing:
                instance.copies.filter(status="available")[:existing - total_copies].delete()

        return instance


class BookIssueSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(
        source="book_copy.book.title",
        read_only=True,
    )
    barcode = serializers.CharField(
        source="book_copy.barcode",
        read_only=True,
    )
    student_name = serializers.CharField(
        source="student.full_name",
        read_only=True,
        default="",
    )
    teacher_name = serializers.CharField(
        source="teacher.full_name",
        read_only=True,
        default="",
    )
    borrower = serializers.CharField(read_only=True)

    class Meta:
        model = BookIssue
        fields = [
            "id",
            "book_copy",
            "book_title",
            "barcode",
            "student",
            "student_name",
            "teacher",
            "teacher_name",
            "borrower",
            "issue_date",
            "due_date",
            "return_date",
            "fine",
            "status",
        ]
        read_only_fields = ["issue_date", "status"]
