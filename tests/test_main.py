from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# def test_read_main():
#    response = client.get("/")
#    assert response.status_code == 200
#    assert response.json() == ["Researcher Searcher"]


def test_search_full():
    response = client.get("/search/?query=test&method=full")
    assert response.status_code == 200
    assert list(response.json().keys()) == ["query", "method", "res"]
    assert len(response.json()["res"]) > 10


def test_search_vec():
    response = client.get("/search/?query=test&method=vec")
    assert response.status_code == 200
    assert list(response.json().keys()) == ["query", "method", "res"]
    assert len(response.json()["res"]) > 10


def test_search_person():
    response = client.get("/search/?query=test&method=person")
    assert response.status_code == 200
    assert list(response.json().keys()) == ["query", "method", "res"]
    assert len(response.json()["res"]) > 10


def test_search_output():
    response = client.get("/search/?query=test&method=output")
    assert response.status_code == 200
    assert list(response.json().keys()) == ["query", "method", "res"]
    assert len(response.json()["res"]) > 10


def test_person():
    response = client.get("/person/?query=ben.elsworth@bristol.ac.uk")
    assert response.status_code == 200
    assert list(response.json().keys()) == ["query", "res"]
    assert len(response.json()["res"]) > 10


def test_collab():
    response = client.get("/collab/?query=ben.elsworth@bristol.ac.uk&method=no")
    assert response.status_code == 200
    assert list(response.json().keys()) == ["query", "method", "res"]
    assert len(response.json()["res"]) > 2
