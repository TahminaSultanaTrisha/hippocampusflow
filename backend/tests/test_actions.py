"""Phase 4 exit criteria: routing to specialists, and the three real actions
storing data + returning running totals. AI mocked throughout."""
import io

from app.core.config import get_settings
from app.services.ai import classifier, router
from app.services.ai import client as ai_client

CREDS = {"email": "act@example.com", "password": "password123"}
TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d4944415478da63fcffff3f0300050201a5f6f5310000000049454e"
    "44ae426082"
)


def _register(client):
    token = client.post("/auth/register", json=CREDS).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _upload(client, headers):
    return client.post("/scans", headers=headers,
                       files={"file": ("p.png", io.BytesIO(TINY_PNG), "image/png")})


def test_router_picks_specialists():
    expected = {
        "receipt": "receipt", "product": "product", "food": "food",
        "ingredients": "cooking", "electronics": "electronics",
        "clothing": "fashion", "furniture": "furniture",
        "appliance": "appliance", "household": "appliance",
        "document": "document", "plant": "plant", "animal": "animal",
        "insect": "insect", "vehicle": "vehicle", "artwork": "artwork",
        "landmark": "travel", "mineral": "mineral", "damage": "repair",
    }
    for category, agent_name in expected.items():
        assert router.route(category).name == agent_name, category
    assert router.route("unknown").name == "general"
    assert router.route("anything-else").name == "general"


def _scan_with(client, monkeypatch, tmp_path, category, details):
    get_settings().upload_dir = str(tmp_path)
    monkeypatch.setattr(classifier, "classify", lambda b, e: {
        "category": category, "confidence": 0.95, "observations": "obs"})
    monkeypatch.setattr(ai_client, "complete_json", lambda **kw: {
        "summary": "s", "details": details, "suggested_actions": [],
        "memory": "m"})
    h = _register(client)
    scan_id = _upload(client, h).json()["id"]
    return h, scan_id


def test_add_expense_running_total(client, tmp_path, monkeypatch):
    h, scan_id = _scan_with(client, monkeypatch, tmp_path, "receipt", {
        "merchant": "Tesco", "date": "2026-07-13", "currency": "£",
        "total": "23.50", "items": [{"name": "Milk", "price": "1.20"}]})

    r = client.post(f"/scans/{scan_id}/actions", headers=h,
                    json={"action_type": "add_expense"})
    assert r.status_code == 200
    assert "23.50" in r.json()["message"]

    scan2 = _upload(client, h).json()["id"]
    r2 = client.post(f"/scans/{scan2}/actions", headers=h,
                     json={"action_type": "add_expense"})
    assert "47.00" in r2.json()["message"]  # monthly total accumulates


def test_wishlist_and_meal(client, tmp_path, monkeypatch):
    h, scan_id = _scan_with(client, monkeypatch, tmp_path, "product", {
        "name": "Dell XPS 13", "brand": "Dell",
        "estimated_price": "£900-1100 (estimate)"})
    r = client.post(f"/scans/{scan_id}/actions", headers=h,
                    json={"action_type": "save_wishlist"})
    assert "Dell XPS 13" in r.json()["message"]
    assert "1 item" in r.json()["message"]

    # meal on another scan (details read from that scan's result)
    monkeypatch.setattr(classifier, "classify", lambda b, e: {
        "category": "food", "confidence": 0.9, "observations": "pizza"})
    monkeypatch.setattr(ai_client, "complete_json", lambda **kw: {
        "summary": "s", "details": {"name": "Margherita pizza",
                                    "calories": "800"},
        "suggested_actions": [], "memory": "m"})
    meal_scan = _upload(client, h).json()["id"]
    r = client.post(f"/scans/{meal_scan}/actions", headers=h,
                    json={"action_type": "log_meal"})
    assert "800" in r.json()["message"]


def test_unknown_action_rejected(client, tmp_path, monkeypatch):
    h, scan_id = _scan_with(client, monkeypatch, tmp_path, "product", {"name": "x"})
    r = client.post(f"/scans/{scan_id}/actions", headers=h,
                    json={"action_type": "launch_rocket"})
    assert r.status_code == 400


def test_action_on_foreign_scan_404(client, tmp_path, monkeypatch):
    h, scan_id = _scan_with(client, monkeypatch, tmp_path, "receipt",
                            {"total": "5", "currency": "£", "merchant": "m"})
    other = {"Authorization": "Bearer " + client.post(
        "/auth/register",
        json={"email": "other@example.com", "password": "password123"}
    ).json()["access_token"]}
    r = client.post(f"/scans/{scan_id}/actions", headers=other,
                    json={"action_type": "add_expense"})
    assert r.status_code == 404
