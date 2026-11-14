from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    original_activities = deepcopy(activities)
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        activities.clear()
        activities.update(original_activities)


def test_get_activities_returns_data_without_caching(client):
    # Arrange
    activity_name = "Basketball Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert activity_name in response.json()


def test_signup_adds_participant_and_updates_activity_list(client):
    # Arrange
    activity_name = "Basketball Club"
    email = "new-student@mergington.edu"
    signup_url = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    signup_response = client.post(signup_url, params={"email": email})
    activities_response = client.get("/activities")

    # Assert
    assert signup_response.status_code == 200
    assert email in activities_response.json()[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]
    signup_url = f"/activities/{quote(activity_name, safe='')}/signup"
    original_participant_count = len(activities[activity_name]["participants"])

    # Act
    response = client.post(signup_url, params={"email": email})

    # Assert
    assert response.status_code == 400
    assert len(activities[activity_name]["participants"]) == original_participant_count


def test_signup_returns_404_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"
    signup_url = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.post(signup_url, params={"email": "student@mergington.edu"})

    # Assert
    assert response.status_code == 404


def test_unregister_removes_participant(client):
    # Arrange
    activity_name = "Basketball Club"
    email = "registered-student@mergington.edu"
    activities[activity_name]["participants"].append(email)
    unregister_url = f"/activities/{quote(activity_name, safe='')}/participants"

    # Act
    unregister_response = client.delete(unregister_url, params={"email": email})
    activities_response = client.get("/activities")

    # Assert
    assert unregister_response.status_code == 200
    assert email not in activities_response.json()[activity_name]["participants"]


def test_unregister_returns_404_when_student_is_not_signed_up(client):
    # Arrange
    activity_name = "Basketball Club"
    email = "not-registered@mergington.edu"
    unregister_url = f"/activities/{quote(activity_name, safe='')}/participants"

    # Act
    response = client.delete(unregister_url, params={"email": email})

    # Assert
    assert response.status_code == 404


def test_unregister_returns_404_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"
    unregister_url = f"/activities/{quote(activity_name, safe='')}/participants"

    # Act
    response = client.delete(unregister_url, params={"email": "student@mergington.edu"})

    # Assert
    assert response.status_code == 404