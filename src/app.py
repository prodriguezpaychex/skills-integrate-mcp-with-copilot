"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import time
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=current_dir / "static"), name="static")

TEACHERS_FILE = Path(os.environ.get("TEACHERS_FILE", current_dir / "teachers.json"))
configured_session_secret = os.environ.get("SESSION_SECRET")
if configured_session_secret and len(configured_session_secret.encode()) < 32:
    raise RuntimeError("SESSION_SECRET must be at least 32 bytes")
SESSION_SECRET = (configured_session_secret or secrets.token_urlsafe(32)).encode()
SESSION_COOKIE = "teacher_session"
SESSION_DURATION_SECONDS = 8 * 60 * 60
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
PASSWORD_HASH_PATTERN = re.compile(
    r"^pbkdf2_sha256\$(\d+)\$([0-9a-f]{32})\$([0-9a-f]{64})$"
)
logger = logging.getLogger(__name__)


class TeacherCredentials(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=1024)


def load_teacher_accounts() -> dict[str, str]:
    try:
        data = json.loads(TEACHERS_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=503,
            detail="Teacher accounts are not configured. See the setup instructions.",
        ) from error
    except (OSError, json.JSONDecodeError) as error:
        logger.exception("Unable to read teacher account configuration")
        raise HTTPException(
            status_code=503,
            detail="Teacher account configuration could not be loaded.",
        ) from error

    try:
        if not isinstance(data, dict) or not isinstance(data.get("teachers"), list):
            raise ValueError("Expected a teachers list")

        accounts: dict[str, str] = {}
        for account in data["teachers"]:
            if not isinstance(account, dict):
                raise ValueError("Each teacher entry must be an object")
            username = account.get("username")
            password_hash = account.get("password_hash")
            if (
                not isinstance(username, str)
                or not USERNAME_PATTERN.fullmatch(username)
                or username in accounts
                or not isinstance(password_hash, str)
            ):
                raise ValueError("Invalid or duplicate teacher account")

            match = PASSWORD_HASH_PATTERN.fullmatch(password_hash)
            if not match or not 100_000 <= int(match.group(1)) <= 2_000_000:
                raise ValueError("Invalid teacher password hash")
            accounts[username] = password_hash
        return accounts
    except (TypeError, ValueError) as error:
        logger.exception("Invalid teacher account configuration")
        raise HTTPException(
            status_code=503,
            detail="Teacher account configuration is invalid.",
        ) from error


def verify_password(password: str, password_hash: str) -> bool:
    match = PASSWORD_HASH_PATTERN.fullmatch(password_hash)
    if not match:
        return False
    iterations, salt, expected = match.groups()
    actual = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), int(iterations)
    ).hex()
    return hmac.compare_digest(actual, expected)


def create_session_token(username: str) -> str:
    expires_at = int(time.time()) + SESSION_DURATION_SECONDS
    payload = f"{username}.{expires_at}"
    signature = hmac.new(SESSION_SECRET, payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def session_username(request: Request) -> str | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    try:
        username, expires_at, signature = token.split(".")
        payload = f"{username}.{expires_at}"
        expected = hmac.new(
            SESSION_SECRET, payload.encode(), hashlib.sha256
        ).hexdigest()
        if (
            not USERNAME_PATTERN.fullmatch(username)
            or int(expires_at) <= int(time.time())
            or not hmac.compare_digest(signature, expected)
        ):
            return None
    except (ValueError, TypeError):
        return None
    return username


def require_teacher(
    request: Request,
    teacher_accounts: dict[str, str] = Depends(load_teacher_accounts),
) -> str:
    username = session_username(request)
    if username is None or username not in teacher_accounts:
        raise HTTPException(status_code=401, detail="Teacher login required")
    return username

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/auth/login")
def login(
    credentials: TeacherCredentials,
    request: Request,
    response: Response,
    teacher_accounts: dict[str, str] = Depends(load_teacher_accounts),
):
    password_hash = teacher_accounts.get(credentials.username)
    if password_hash is None or not verify_password(credentials.password, password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    response.set_cookie(
        key=SESSION_COOKIE,
        value=create_session_token(credentials.username),
        httponly=True,
        secure=(
            os.environ.get("SESSION_COOKIE_SECURE", "").lower() == "true"
            or request.url.scheme == "https"
        ),
        samesite="lax",
        max_age=SESSION_DURATION_SECONDS,
        path="/",
    )
    return {"message": "Signed in as teacher"}


@app.get("/auth/me")
def current_teacher(request: Request):
    username = session_username(request)
    if username is None:
        return {"authenticated": False}
    teacher_accounts = load_teacher_accounts()
    if username not in teacher_accounts:
        return {"authenticated": False}
    return {"authenticated": True, "username": username}


@app.post("/auth/logout")
def logout(request: Request, response: Response):
    response.delete_cookie(
        key=SESSION_COOKIE,
        path="/",
        httponly=True,
        secure=(
            os.environ.get("SESSION_COOKIE_SECURE", "").lower() == "true"
            or request.url.scheme == "https"
        ),
        samesite="lax",
    )
    return {"message": "Signed out"}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str,
    email: str,
    _teacher: str = Depends(require_teacher),
):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str,
    email: str,
    _teacher: str = Depends(require_teacher),
):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
