import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

# Create a test client
@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)

@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to a clean state before each test"""
    # Store original state
    original = {
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
        "Basketball": {
            "description": "Team sports and fitness",
            "schedule": "Mondays, 4:00 PM - 5:00 PM",
            "max_participants": 15,
            "participants": []
        },
        "Painting": {
            "description": "Creative arts and expression",
            "schedule": "Wednesdays, 3:00 PM - 4:30 PM",
            "max_participants": 10,
            "participants": []
        },
        "Debate Club": {
            "description": "Intellectual discussion and logic",
            "schedule": "Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": []
        }
    }
    
    # Clear and rebuild activities
    activities.clear()
    activities.update(original)
    yield
    # Cleanup (reset after test)
    activities.clear()
    activities.update(original)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_success(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        assert "Chess Club" in response.json()
        assert "Programming Class" in response.json()
        assert "Gym Class" in response.json()
    
    def test_get_activities_contains_required_fields(self, client):
        """Test that activities contain all required fields"""
        response = client.get("/activities")
        activities_data = response.json()
        
        for activity_name, activity_info in activities_data.items():
            assert "description" in activity_info
            assert "schedule" in activity_info
            assert "max_participants" in activity_info
            assert "participants" in activity_info
            assert isinstance(activity_info["participants"], list)


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert "test@mergington.edu" in activities["Basketball"]["participants"]
    
    def test_signup_activity_not_found(self, client):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_duplicate_registration(self, client):
        """Test that students can't register twice for same activity"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            "/activities/Basketball/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            "/activities/Basketball/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]
    
    def test_signup_existing_participant(self, client):
        """Test that existing participants can't register again"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]


class TestRemoveParticipant:
    """Tests for POST /activities/{activity_name}/remove-participant endpoint"""
    
    def test_remove_participant_success(self, client):
        """Test successfully removing a participant"""
        email = "michael@mergington.edu"
        
        # Verify participant exists before removal
        assert email in activities["Chess Club"]["participants"]
        
        response = client.post(
            "/activities/Chess Club/remove-participant",
            params={"email": email}
        )
        assert response.status_code == 200
        assert "Removed" in response.json()["message"]
        assert email not in activities["Chess Club"]["participants"]
    
    def test_remove_participant_activity_not_found(self, client):
        """Test removing participant from non-existent activity"""
        response = client.post(
            "/activities/Nonexistent/remove-participant",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_remove_participant_not_found(self, client):
        """Test removing a participant who isn't registered"""
        response = client.post(
            "/activities/Basketball/remove-participant",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]
    
    def test_remove_allows_re_signup(self, client):
        """Test that removing a participant allows them to sign up again"""
        email = "test@mergington.edu"
        
        # Sign up
        response1 = client.post(
            "/activities/Basketball/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Remove
        response2 = client.post(
            "/activities/Basketball/remove-participant",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Sign up again - should succeed
        response3 = client.post(
            "/activities/Basketball/signup",
            params={"email": email}
        )
        assert response3.status_code == 200
