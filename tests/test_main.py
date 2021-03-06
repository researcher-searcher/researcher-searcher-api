from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# def test_read_main():
#    response = client.get("/")
#    assert response.status_code == 200
#    assert response.json() == ["Researcher Searcher"]


def test_search_combine():
    response = client.get("/search/?query=test&method=combine")
    assert response.status_code == 200
    assert list(response.json().keys()) == ["query", "method", "year_range", "res"]
    assert len(response.json()["res"]) > 10


def test_search_full():
    response = client.get("/search/?query=test&method=full")
    assert response.status_code == 200
    assert list(response.json().keys()) == ["query", "method", "year_range", "res"]
    assert len(response.json()["res"]) > 10


def test_search_vec():
    response = client.get("/search/?query=test&method=vec")
    assert response.status_code == 200
    assert list(response.json().keys()) == ["query", "method", "year_range", "res"]
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
    response = client.get(
        "/person/?query=https://research-information.bris.ac.uk/en/persons/jean-golding"
    )
    assert response.status_code == 200
    assert list(response.json().keys()) == ["query", "res"]
    assert len(response.json()["res"]) > 1


def test_collab1():
    response = client.get(
        "/collab/?query=https://research-information.bris.ac.uk/en/persons/jean-golding&method=no"
    )
    assert response.status_code == 200
    assert list(response.json().keys()) == ["query", "method", "res"]
    assert len(response.json()["res"]) > 2


def test_collab2():
    response = client.get(
        "/collab/?query=https://research-information.bris.ac.uk/en/persons/jean-golding&method=yes"
    )
    assert response.status_code == 200
    assert list(response.json().keys()) == ["query", "method", "res"]
    assert len(response.json()["res"]) > 2


def test_collab3():
    response = client.get(
        "/collab/?query=https://research-information.bris.ac.uk/en/persons/jean-golding&method=all"
    )
    assert response.status_code == 200
    assert list(response.json().keys()) == ["query", "method", "res"]
    assert len(response.json()["res"]) > 2


def test_vector():
    response = client.get("/vector/?query=test&method=sent")
    assert response.status_code == 200
    assert list(response.json().keys()) == ["query", "method", "res"]
    assert len(response.json()["res"]) == 1


def test_person_aaa():
    response = client.get(
        "/aaa/?query=https://research-information.bris.ac.uk/en/persons/jean-golding&query=https://research-information.bris.ac.uk/en/persons/jie-zheng&query=https://research-information.bris.ac.uk/en/persons/gibran-hemani&query=https://research-information.bris.ac.uk/en/persons/rebecca-richmond"
    )
    assert response.status_code == 200
    assert list(response.json().keys()) == ["query", "res"]
    assert len(response.json()["res"]) == 16
