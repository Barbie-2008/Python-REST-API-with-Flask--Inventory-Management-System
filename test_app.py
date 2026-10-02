from copy import deepcopy
import builtins
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import requests
import app as inventory_app
import cli
from app import app, inventory


@pytest.fixture
def client():
    app.config["TESTING"] = True
    saved_inventory = deepcopy(inventory)
    with app.test_client() as test_client:
        yield test_client
    inventory[:] = saved_inventory


@pytest.fixture
def cli_client(monkeypatch, client):
    def send(method, url, **kwargs):
        response = getattr(client, method)(url.removeprefix(cli.BASE_URL), **kwargs)
        return SimpleNamespace(status_code=response.status_code, json=response.get_json)

    for method in ("get", "post", "patch", "delete"):
        monkeypatch.setattr(cli.requests, method,
                            lambda url, _method=method, **kw: send(_method, url, **kw))
    return client


def enter(monkeypatch, *answers):
    answers = iter(answers)
    monkeypatch.setattr(builtins, "input", lambda _prompt="": next(answers))


def test_get_routes(client):
    assert client.get("/inventory").status_code == 200
    assert client.get("/inventory/101").json["product_name"] == "Organic Almond Milk"
    assert client.get("/inventory/999").status_code == 404


def test_post_valid_duplicate_and_missing(client):
    item = {"id": "201", "product_name": "Yogurt", "brands": "Test",
            "ingredients_text": "Milk", "price": 2, "stock": 15}
    assert client.post("/inventory", json=item).status_code == 201
    duplicate = client.post("/inventory", json={"id": "101"})
    assert duplicate.status_code == 400 and "already exists" in duplicate.json["error"]
    assert client.post("/inventory", json={"id": "301"}).status_code == 400


def test_patch_valid_and_missing(client):
    result = client.patch("/inventory/101", json={"price": 4.99, "stock": 50})
    assert result.status_code == 200 and result.json["stock"] == 50
    assert client.patch("/inventory/999", json={"price": 1}).status_code == 404


def test_delete_valid_and_missing(client):
    result = client.delete("/inventory/101")
    assert result.status_code == 200 and "successfully" in result.json["message"]
    assert client.get("/inventory/101").status_code == 404
    assert client.delete("/inventory/999").status_code == 404


def test_cli_views_show_stock(monkeypatch, capsys, cli_client):
    enter(monkeypatch, "101")
    cli.view_all()
    cli.view_one()
    assert "Stock: 50" in capsys.readouterr().out


def test_cli_manual_add(monkeypatch, capsys, cli_client):
    enter(monkeypatch, "203", "Oat Milk", "Oatly", "Oats", "3.25", "18")
    cli.add_manual()
    item = next(item for item in inventory if item["id"] == "203")
    assert item["ingredients_text"] == "Oats" and item["stock_quantity"] == 18
    assert "Added 'Oat Milk'" in capsys.readouterr().out


def test_cli_update_and_delete(monkeypatch, capsys, cli_client):
    enter(monkeypatch, "101", "6.25", "9")
    cli.update_item()
    assert inventory[0]["price"] == 6.25 and inventory[0]["stock_quantity"] == 9
    enter(monkeypatch, "102", "y")
    cli.delete_item()
    assert all(item["id"] != "102" for item in inventory)
    assert "deleted successfully" in capsys.readouterr().out


@patch("app.requests.get")
def test_external_fetch_success(mock_get, client):
    mock_get.return_value.json.return_value = {
        "status": 1, "product": {"product_name": "Bar", "brands": "Test",
                                    "ingredients_text": "Cocoa"}}
    result = client.get("/external/fetch/123")
    assert result.status_code == 200 and result.json["product_name"] == "Bar"
    mock_get.assert_called_once_with(
        "https://world.openfoodfacts.org/api/v0/product/123.json",
        headers={"User-Agent": "InventorySystemLab - Python/Flask"}, timeout=5)


@patch("app.requests.get")
def test_external_fetch_not_found(mock_get, client):
    mock_get.return_value.json.return_value = {"status": 0}
    result = client.get("/external/fetch/000")
    assert result.status_code == 404 and "not found" in result.json["error"]


@patch("app.requests.get", side_effect=requests.Timeout)
def test_external_fetch_unavailable(mock_get, client):
    assert client.get("/external/fetch/123").status_code == 502


def test_cli_barcode_fetch_and_add(monkeypatch, capsys, cli_client):
    enter(monkeypatch, "123", "204", "2.49", "12")
    product = {"product_name": "Bar", "brands": "Test", "ingredients_text": "Cocoa"}
    monkeypatch.setattr(inventory_app, "fetch_product_details", lambda barcode: product)
    cli.add_from_barcode()
    item = next(item for item in inventory if item["id"] == "204")
    assert item["product_name"] == "Bar" and item["stock_quantity"] == 12
    assert "added to inventory" in capsys.readouterr().out


def test_cli_barcode_not_found_does_not_add(monkeypatch, capsys):
    enter(monkeypatch, "000")
    posts = []
    monkeypatch.setattr(cli.requests, "get", lambda url: SimpleNamespace(
        status_code=404, json=lambda: {"error": "Product not found"}))
    monkeypatch.setattr(cli.requests, "post", lambda *args, **kwargs: posts.append(args))
    cli.add_from_barcode()
    assert not posts and "Product not found" in capsys.readouterr().out