from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Event, Reservation


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class EventSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    reserved_slots = serializers.IntegerField(read_only=True)
    available_slots = serializers.IntegerField(read_only=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "creator",
            "title",
            "description",
            "start_time",
            "end_time",
            "capacity",
            "reserved_slots",
            "available_slots",
            "created_at",
        ]


class ReservationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    event = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Reservation
        fields = ["id", "user", "event", "created_at"]
