from django.db.models import Q
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import AlumniProfile
from .serializers import AlumniProfileSerializer


class AlumniListCreateView(generics.ListCreateAPIView):
    serializer_class = AlumniProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = AlumniProfile.objects.select_related("campus")

        search = self.request.query_params.get("search", "").strip()

        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search)
                | Q(organization__icontains=search)
                | Q(city__icontains=search)
            )

        batch_year = self.request.query_params.get("batch_year")

        if batch_year:
            queryset = queryset.filter(batch_year=batch_year)

        campus = self.request.query_params.get("campus")

        if campus:
            queryset = queryset.filter(campus_id=campus)

        return queryset


class AlumniDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AlumniProfileSerializer
    permission_classes = [IsAuthenticated]
    queryset = AlumniProfile.objects.select_related("campus")
