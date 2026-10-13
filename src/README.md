# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- View current activity participants
- Teacher-only registration and unregistration

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Create a teacher account hash:

   ```
   python create_teacher_account.py teacher1
   ```

   Copy the generated JSON into `teachers.json` in this directory. This local
   file is ignored by Git; never commit teacher passwords or password hashes.
   Add additional teacher entries to the `teachers` array as needed. The app
   reports a configuration error if the file is missing or invalid.

3. Run the application:

   ```
   uvicorn app:app --reload
   ```

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

For deployments, set `SESSION_SECRET` to a long, random secret and serve the
application over HTTPS. HTTPS requests automatically receive secure,
HTTP-only, same-site teacher session cookies; set `SESSION_COOKIE_SECURE=true`
when TLS is terminated by a proxy and the app itself sees HTTP. If
`SESSION_SECRET` is not set, a random key is generated at startup and sessions
are invalidated when the process restarts.

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/auth/login`                                                      | Sign in with a configured teacher account                           |
| GET    | `/auth/me`                                                         | Check the current teacher session                                    |
| POST   | `/auth/logout`                                                     | End the current teacher session                                     |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | (Teacher only) Sign up a student                                     |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | (Teacher only) Unregister a student                              |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
