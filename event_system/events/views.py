from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import Event, Reservation
from events.serializers import EventSerializer, ReservationSerializer


class EventViewSet(viewsets.ModelViewSet):
    """
    Handles Event CRUD and reservation logic.
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Attach event creator
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        event = self.get_object()
        if event.creator != self.request.user:
            raise PermissionDenied("You can only update your own events.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.creator != self.request.user:
            raise PermissionDenied("You can only delete your own events.")
        instance.delete()

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def reserve(self, request, pk=None):
        """
        Reserve a slot for an event (concurrency-safe).
        """
        user = request.user
        try:
            with transaction.atomic():
                event = Event.objects.select_for_update().get(pk=pk)

                # Prevent duplicate reservation
                if Reservation.objects.filter(user=user, event=event).exists():
                    raise ValidationError("You already reserved this event.")

                # Check capacity
                if event.reservations.count() >= event.capacity:
                    raise ValidationError("Event is already full.")

                reservation = Reservation.objects.create(user=user, event=event)

            return Response(
                ReservationSerializer(reservation).data,
                status=status.HTTP_201_CREATED
            )
        except Event.DoesNotExist:
            return Response({"detail": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def reservations(self, request, pk=None):
        """
        List reservations for an event (only creator can see).
        """
        event = self.get_object()
        if event.creator != request.user:
            raise PermissionDenied("Only the event creator can see reservations.")

        qs = event.reservations.all()
        return Response(ReservationSerializer(qs, many=True).data)


class ReservationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Handles listing & cancelling reservations.
    """
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user)

    @action(detail=True, methods=["delete"], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        """
        Cancel a reservation (only if it belongs to the user).
        """
        try:
            reservation = Reservation.objects.get(pk=pk, user=request.user)
        except Reservation.DoesNotExist:
            return Response({"detail": "Reservation not found."}, status=status.HTTP_404_NOT_FOUND)

        reservation.delete()
        return Response({"detail": "Reservation cancelled."}, status=status.HTTP_204_NO_CONTENT)
