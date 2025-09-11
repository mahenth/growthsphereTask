# growthsphereTask

Event Scheduling & Reservation System

Product Overview 
This project is a robust backend system for an event scheduling and reservation platform. Users can create events with a defined capacity, and other users can reserve slots. The system is designed to be reliable and prevent overbooking, even under high traffic from concurrent reservation attempts.

1. Proposed Model Schema
    The system's data is modeled using three primary Django models: User, Event, and Reservation. The User model, provided by Django's built-in authentication system, is used to link events and reservations to specific users.

    Data Model Breakdown:

    User:

    username: CharField (unique)

    password: CharField

    email: EmailField

    (Django's default authentication fields)

    Event:

    creator: ForeignKey to User

    title: CharField

    description: TextField

    start_time: DateTimeField

    end_time: DateTimeField

    capacity: PositiveIntegerField

    reserved_slots: @property (calculated count of reservations)

    available_slots: @property (calculated capacity minus reserved_slots)

    Reservation:

    user: ForeignKey to User

    event: ForeignKey to Event

    created_at: DateTimeField

    **unique_together**: ("user", "event") - A database-level constraint that ensures a user can't reserve the same event more than once.

2. Proposed API Endpoints
All API endpoints are prefixed with /api/.

| Method | URL | Description | Authentication Required |
|--------|-----|-------------|------------------------|
| POST | /api/auth/login/ | Obtain JWT access and refresh tokens. | No |
| POST | /api/auth/refresh/ | Refresh a JWT access token. | No |
| GET | /api/events/ | List all events. | Yes |
| POST | /api/events/ | Create a new event. | Yes |
| GET | /api/events/{id}/ | Retrieve a specific event. | Yes |
| PATCH | /api/events/{id}/ | Update an event (only by creator). | Yes |
| DELETE | /api/events/{id}/ | Delete an event (only by creator). | Yes |
| POST | /api/events/{id}/reserve/ | Reserve a slot for an event. | Yes |
| GET | /api/events/{id}/reservations/ | List all reservations for an event (only by creator). | Yes |
| GET | /api/reservations/ | List all reservations for the current user. | Yes |
| DELETE | /api/reservations/{id}/cancel/ | Cancel a reservation (only by the user who made it). | Yes |


3. Instructions on How to Set Up and Run the Project
    The recommended way to run this project is using Docker Compose, which manages both the web server and the PostgreSQL database.

    Prerequisites
    Docker: Ensure Docker is installed and running on your system.

    Git: Ensure Git is installed to clone the repository.

    Running with Docker Compose
    Clone the Repository:

    git clone <your-repository-url>
    cd <your-repository-name>

    Build and Run Containers:
    This command will build the Docker images and start both the web and db services in the background.

    docker-compose up --build -d

    Apply Database Migrations:
    Apply the database schema changes to the PostgreSQL database inside the container.

    docker-compose exec web python manage.py migrate

    Create a Superuser:
    Create a Django superuser account to access the admin panel and for initial API testing.

    docker-compose exec web python manage.py createsuperuser

    Your application will be accessible at http://localhost:8000, and the interactive API documentation (Swagger UI) will be at http://localhost:8000/swagger/.

4. Instructions on How to Run Tests
    To run the full test suite and ensure all functionalities work as expected, execute the following command inside the web container:

    docker-compose exec web python manage.py test

5. A Detailed Explanation of Design Choices
i. Data Modeling
    The models are designed to be simple and relational. The Event model holds core event data and has a ForeignKey to the User who created it. The Reservation model acts as a junction table, with ForeignKeys to both the Event and the User who made the reservation. The @property decorators in the Event model (reserved_slots, available_slots) provide real-time, calculated fields without needing to be stored in the database.

ii. Strategy for Handling Concurrent Bookings
    To prevent overbooking, the system uses a concurrency-safe approach with a database transaction and select_for_update. The reserve action within views.py wraps the reservation logic in django.db.transaction.atomic(). Inside this transaction, a database lock is acquired on the specific Event row using Event.objects.select_for_update(). This ensures that only one request can modify the event's state at a time, preventing race conditions and guaranteeing that the capacity check is always accurate.

iii. Approach to Error Management
    The system employs robust error management to provide clear feedback to users.

    Permission Checks: The perform_update, perform_destroy, and reservations methods use a direct check (event.creator != request.user) and raise rest_framework.exceptions.PermissionDenied if a user attempts an unauthorized action.

    Data Validation: serializers.py handles most data validation (e.g., date format, required fields).

    Custom Validation: The reserve action includes custom validation logic to check if the event is at full capacity or if the user has already made a reservation, raising a ValidationError with a descriptive message.

    Object Not Found: try...except blocks are used to catch DoesNotExist exceptions for Event and Reservation models, returning a 404 Not Found response to the client.

6. Add swagger for api docs
    The project includes API documentation powered by drf-yasg. The configuration is handled in settings.py for project-wide consistency. The Swagger UI is accessible at http://localhost:8000/swagger/ and provides an interactive interface for exploring and testing all API endpoints.