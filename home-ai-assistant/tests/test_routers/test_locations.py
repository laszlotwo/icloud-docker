def test_create_and_find_location(client):
    r = client.post("/api/v1/locations", json={
        "item_name": "护照",
        "location": "主卧衣柜上层",
        "room": "主卧",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["item_name"] == "护照"

    r = client.get("/api/v1/locations/search?q=护照")
    assert r.status_code == 200
    assert any(i["item_name"] == "护照" for i in r.json())


def test_confirm_location(client):
    r = client.post("/api/v1/locations", json={"item_name": "钥匙", "location": "门口挂钩"})
    loc_id = r.json()["id"]
    r = client.post(f"/api/v1/locations/{loc_id}/confirm")
    assert r.status_code == 200
    assert r.json()["last_confirmed_at"] is not None


def test_filter_by_room(client):
    client.post("/api/v1/locations", json={"item_name": "书", "location": "书架", "room": "书房"})
    r = client.get("/api/v1/locations?room=书房")
    assert r.status_code == 200
    assert all(i["room"] == "书房" for i in r.json())
