from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAccountantRole
from apps.accounts.access import apply_campus_scope

from .models import Book, BookIssue
from .serializers import BookIssueSerializer, BookSerializer


class BookListView(generics.ListCreateAPIView):
    serializer_class = BookSerializer
    permission_classes = [IsAccountantRole]

    def get_queryset(self):
        queryset = apply_campus_scope(
            Book.objects.all().prefetch_related("copies"),
            self.request,
            "campus_id",
        )

        search = self.request.query_params.get("q")

        if search:
            queryset = queryset.filter(
                title__icontains=search,
            ) | queryset.filter(
                author__icontains=search,
            ) | queryset.filter(
                isbn__icontains=search,
            )

        category = self.request.query_params.get("category")

        if category:
            queryset = queryset.filter(category=category)

        return queryset

    def perform_create(self, serializer):
        from apps.accounts.access import assert_campus_allowed

        assert_campus_allowed(self.request.user, serializer.validated_data.get("campus"))
        serializer.save()


class BookDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BookSerializer
    permission_classes = [IsAccountantRole]
    def get_queryset(self):
        return apply_campus_scope(Book.objects.all(), self.request, "campus_id")

    def perform_update(self, serializer):
        from apps.accounts.access import assert_campus_allowed

        assert_campus_allowed(self.request.user, serializer.validated_data.get("campus", serializer.instance.campus))
        serializer.save()


class BookIssueListView(generics.ListCreateAPIView):
    serializer_class = BookIssueSerializer
    permission_classes = [IsAccountantRole]

    def get_queryset(self):
        queryset = apply_campus_scope(BookIssue.objects.select_related(
            "book_copy__book",
            "student",
            "teacher",
        ), self.request, "book_copy__book__campus_id")

        status_filter = self.request.query_params.get("status")

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

    def perform_create(self, serializer):
        if not self.get_queryset().filter(book_copy=serializer.validated_data["book_copy"]).exists():
            raise PermissionDenied("The book is outside your campus scope.")
        serializer.save()


class BookIssueDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BookIssueSerializer
    permission_classes = [IsAccountantRole]

    def get_queryset(self):
        return apply_campus_scope(
            BookIssue.objects.all(),
            self.request,
            "book_copy__book__campus_id",
        )

    def perform_update(self, serializer):
        if not self.get_queryset().filter(
            book_copy=serializer.validated_data.get(
                "book_copy",
                serializer.instance.book_copy,
            ),
        ).exists():
            raise PermissionDenied("The book is outside your campus scope.")
        serializer.save()


class BookReturnView(APIView):
    permission_classes = [IsAccountantRole]

    def post(self, request, pk):
        issue = apply_campus_scope(
            BookIssue.objects.filter(pk=pk),
            request,
            "book_copy__book__campus_id",
        ).first()

        if issue is None:
            return Response(
                {"detail": "Issue record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if issue.status == "returned":
            return Response(
                {"detail": "This copy has already been returned."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        fine = request.data.get("fine", 0)

        issue.fine = fine
        issue.return_copy()

        return Response(
            BookIssueSerializer(issue).data
        )
