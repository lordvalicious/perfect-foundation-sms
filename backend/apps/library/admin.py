from django.contrib import admin

from .models import Book, BookCopy, BookIssue


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "isbn", "category", "total_copies"]
    list_filter = ["category"]


@admin.register(BookCopy)
class BookCopyAdmin(admin.ModelAdmin):
    list_display = ["barcode", "book", "status"]
    list_filter = ["status"]


@admin.register(BookIssue)
class BookIssueAdmin(admin.ModelAdmin):
    list_display = ["book_copy", "borrower", "issue_date", "due_date", "status"]
    list_filter = ["status"]
