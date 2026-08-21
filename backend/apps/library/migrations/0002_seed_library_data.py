from django.db import migrations


def seed_library(apps, schema_editor):
    Book = apps.get_model("library", "Book")
    BookCopy = apps.get_model("library", "BookCopy")

    if Book.objects.exists():
        return

    books_data = [
        {"title": " Mathematics for Class 10", "author": "Punjab Curriculum Board", "isbn": "978-969-494-810-1", "publisher": "Punjab Textbook Board", "publication_year": 2023, "category": "textbook", "total_copies": 8},
        {"title": "English Grammar in Use", "author": "Raymond Murphy", "isbn": "978-0-521-18906-4", "publisher": "Cambridge University Press", "publication_year": 2019, "category": "textbook", "total_copies": 6},
        {"title": "Physics Class 12", "author": "Punjab Curriculum Board", "isbn": "978-969-494-820-0", "publisher": "Punjab Textbook Board", "publication_year": 2023, "category": "textbook", "total_copies": 7},
        {"title": "Pakistan Studies", "author": "Ikram Rabbani", "isbn": "978-969-532-100-3", "publisher": "Caravan Book House", "publication_year": 2022, "category": "textbook", "total_copies": 10},
        {"title": "The Urdu Novel: A Critical Study", "author": "Dr. Saeed Khan", "isbn": "978-969-496-305-0", "publisher": "Sang-e-Meel Publications", "publication_year": 2020, "category": "literature", "total_copies": 4},
        {"title": "Diary of a Wimpy Kid", "author": "Jeff Kinney", "isbn": "978-0-14-377455-3", "publisher": "Puffin Books", "publication_year": 2021, "category": "fiction", "total_copies": 5},
        {"title": "Charlie and the Chocolate Factory", "author": "Roald Dahl", "isbn": "978-0-14-137144-1", "publisher": "Puffin Books", "publication_year": 2016, "category": "fiction", "total_copies": 5},
        {"title": "The Alchemist", "author": "Paulo Coelho", "isbn": "978-0-06-251140-9", "publisher": "HarperOne", "publication_year": 2014, "category": "fiction", "total_copies": 4},
        {"title": "A Brief History of Time", "author": "Stephen Hawking", "isbn": "978-0-553-38016-3", "publisher": "Bantam Books", "publication_year": 2011, "category": "science", "total_copies": 3},
        {"title": "Organic Chemistry", "author": "M. Nasirullah", "isbn": "978-969-532-200-1", "publisher": "Caravan Book House", "publication_year": 2021, "category": "science", "total_copies": 6},
        {"title": "Oxford Dictionary of English", "author": "Oxford University Press", "isbn": "978-0-19-957112-3", "publisher": "Oxford University Press", "publication_year": 2018, "category": "reference", "total_copies": 4},
        {"title": "Hamlet", "author": "William Shakespeare", "isbn": "978-0-14-143951-8", "publisher": "Penguin Classics", "publication_year": 2015, "category": "literature", "total_copies": 3},
        {"title": "The Wealth of Nations", "author": "Adam Smith", "isbn": "978-0-14-043601-6", "publisher": "Penguin Classics", "publication_year": 2003, "category": "non_fiction", "total_copies": 2},
        {"title": "World History: A Global Perspective", "author": "J.M. Roberts", "isbn": "978-1-4088-1034-5", "publisher": "Bloomsbury", "publication_year": 2018, "category": "history", "total_copies": 5},
        {"title": "Geography of Pakistan", "author": "Dr. Qazi Saeed Ahmad", "isbn": "978-969-496-401-2", "publisher": "Sang-e-Meel Publications", "publication_year": 2019, "category": "geography", "total_copies": 4},
    ]

    for b in books_data:
        book = Book.objects.create(**b)
        for i in range(1, book.total_copies + 1):
            BookCopy.objects.create(
                book=book,
                barcode=f"LIB-{book.pk:04d}-{i:02d}",
                status="available",
            )


class Migration(migrations.Migration):
    dependencies = [
        ("library", "0001_initial"),
    ]
    operations = [
        migrations.RunPython(seed_library, migrations.RunPython.noop),
    ]
