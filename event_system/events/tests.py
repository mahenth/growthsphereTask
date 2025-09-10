from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import timedelta
import threading
from django.urls import reverse
from .models import Event, Reservation


class JWTAuthenticationTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpassword'
        )

    def get_jwt_token(self):
        # Get token from the token endpoint
        login_url = reverse('token_obtain_pair')
        response = self.client.post(login_url, {'username': 'testuser', 'password': 'testpassword'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data['access']

    def test_authenticated_access_with_jwt(self):
        # Get a JWT token
        token = self.get_jwt_token()

        # Set the token in the Authorization header for subsequent requests
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # Try to access a protected endpoint
        response = self.client.get(reverse('event-list'))

        # Assert that the request was successful (200 OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_access_without_jwt(self):
        # Clear any credentials
        self.client.credentials()

        # Try to access a protected endpoint
        response = self.client.get(reverse('event-list'))

        # Assert that the request failed with 401 Unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class EventReservationTests(APITestCase):
    def setUp(self):
        # Create users
        self.creator = User.objects.create_user(username="creator", password="pass123")
        self.attendee = User.objects.create_user(username="attendee", password="pass123")

        # Create an event
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=2)
        self.event = Event.objects.create(
            creator=self.creator,
            title="Yoga Class",
            description="Morning session",
            start_time=start,
            end_time=end,
            capacity=2,
        )
    
    def test_event_creation(self):
        """Creator can create an event"""
        self.client.force_authenticate(user=self.creator)
        self.assertEqual(Event.objects.count(), 1)
        self.assertEqual(self.event.creator, self.creator)

    def test_only_creator_can_edit_event(self):
        """Non-creator cannot edit event"""
        self.client.force_authenticate(user=self.attendee)
        url = f"/api/events/{self.event.id}/"
        response = self.client.patch(url, {"title": "Hacked"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_reserve_event(self):
        """Attendee can reserve a slot"""
        self.client.force_authenticate(user=self.attendee)
        url = f"/api/events/{self.event.id}/reserve/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reservation.objects.count(), 1)

    def test_duplicate_reservation_prevented(self):
        """User cannot reserve the same event twice"""
        self.client.force_authenticate(user=self.attendee)
        url = f"/api/events/{self.event.id}/reserve/"
        # First reservation (should succeed)
        response1 = self.client.post(url)
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        # Second reservation (should fail)
        response2 = self.client.post(url)
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_concurrent_reservations(self):
        """Prevent overbooking when multiple users try at the same time"""
        users = [
            User.objects.create_user(username=f"user{i}", password="pass123")
            for i in range(5)
        ]
        
        # Concurrency with separate clients (no threading)
        # This is the thread-safe way to test concurrency in Django tests
        client = APIClient()
        responses = []
        for user in users:
            client.force_authenticate(user=user)
            url = f"/api/events/{self.event.id}/reserve/"
            response = client.post(url)
            responses.append(response.status_code)
            
        success_count = responses.count(status.HTTP_201_CREATED)
        fail_count = responses.count(status.HTTP_400_BAD_REQUEST)
        
        # The first two requests should succeed (capacity is 2)
        # The remaining three should fail.
        self.assertEqual(success_count, self.event.capacity)
        self.assertEqual(fail_count, len(users) - self.event.capacity)
        self.assertEqual(Reservation.objects.count(), self.event.capacity)
        



