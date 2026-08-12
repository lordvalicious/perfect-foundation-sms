from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAccountantRole

from .models import Book, BookIssue
from .serializers import BookIssueSerializer, BookSerializer


class BookListView(generics.ListCreateAPIView):
    serializer_class = BookSerializer
    permission_classes = [IsAccountantRole]

    def get_queryset(self):
        queryset = Book.objects.all().prefetch_related("copies")

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


class BookDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BookSerializer
    permission_classes = [IsAccountantRole]
    queryset = Book.objects.all()


class BookIssueListView(generics.ListCreateAPIView):
    serializer_class = BookIssueSerializer
    permission_classes = [IsAccountantRole]

    def get_queryset(self):
        queryset = BookIssue.objects.select_related(
            "book_copy__book",
            "student",
            "teacher",
        )

        status_filter = self.request.query_params.get("status")

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset


class BookIssueDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BookIssueSerializer
    permission_classes = [IsAccountantRole]

    def get_queryset(self):
        return BookIssue.objects.all()


class BookReturnView(APIView):
    permission_classes = [IsAccountantRole]

    def post(self, request, pk):
        issue = BookIssue.objects.filter(pk=pk).first()

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
