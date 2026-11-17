from decimal import Decimal
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

def test_another_quote_creation():
    # Arrange
    request_data = {
        "policy_id": "P2",
        "cover_type": "third-party",
        "premium": "150.00",
        "start_date": "01/01/2025",
        "drivers": [{"full_name": "Jane Smith", "age": 28}],
    }

    # Act
    create_response = client.post("/quotes", json=request_data)

    # Retrieve the quote
    assert create_response.status_code == 201
    

def test_create_quote_returns_201_and_quote_id():
    # Arrange
    request_data = {
        "policy_id": "P1",
        "cover_type": "comprehensive",
        "premium": "250.00",
        "start_date": "15/09/2026",
        "drivers": [{"full_name": "John Doe", "age": 30}],
    }

    # Act
    response = client.post("/quotes", json=request_data)

    # Assert
    assert response.status_code == 201
    response_data = response.json()
    assert response_data["quote_id"] == 1
    assert response_data["policy_id"] == request_data["policy_id"]
    assert Decimal(response_data["premium"]) == Decimal(request_data["premium"])
    assert response_data["drivers"] == len(request_data["drivers"])
    
    
def test_get_missing_quote_returns_404():
    # Act
    response = client.get("/quotes/999")  # Assuming quote_id 999 does not exist

    # Assert
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"] == "Quote not found"
        
    