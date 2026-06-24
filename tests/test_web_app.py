from main import app


def test_index_page_loads_successfully():
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"DataScope Analytics" in response.data
