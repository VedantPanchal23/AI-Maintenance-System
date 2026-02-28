"""
Comprehensive API Test Script
Tests all endpoints end-to-end against a running server.

Set these environment variables before running:
    TEST_ADMIN_EMAIL       — Admin user email
    TEST_ADMIN_PASSWORD    — Admin user password
    TEST_ENGINEER_EMAIL    — (optional) Engineer user email
    TEST_ENGINEER_PASSWORD — (optional) Engineer user password
    TEST_API_BASE          — (optional) API base URL, default http://localhost:8000
"""

import json
import os
import random
import sys
import time
import requests

BASE = os.environ.get("TEST_API_BASE", "http://localhost:8000")
API = f"{BASE}/api/v1"

ADMIN_EMAIL = os.environ.get("TEST_ADMIN_EMAIL", "")
ADMIN_PASSWORD = os.environ.get("TEST_ADMIN_PASSWORD", "")
ENGINEER_EMAIL = os.environ.get("TEST_ENGINEER_EMAIL", "")
ENGINEER_PASSWORD = os.environ.get("TEST_ENGINEER_PASSWORD", "")

passed = 0
failed = 0
errors = []


def test(name, response, expected_status=200):
    global passed, failed
    ok = response.status_code == expected_status
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {name} -- {response.status_code} (expected {expected_status})")
    if ok:
        passed += 1
    else:
        failed += 1
        try:
            detail = response.json()
        except Exception:
            detail = response.text[:300]
        errors.append(f"{name}: got {response.status_code}, expected {expected_status} -- {detail}")
    return ok


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


print("=" * 60)
print("API Integration Test Suite")
print("=" * 60)

if not ADMIN_EMAIL or not ADMIN_PASSWORD:
    print("\n✗ Set TEST_ADMIN_EMAIL and TEST_ADMIN_PASSWORD env vars to run tests.")
    sys.exit(1)

# ── 1. Health Check ──────────────────────────────────────────
print("\n1. Health Check")
r = requests.get(f"{BASE}/health")
test("GET /health", r)

# ── 2. Auth ──────────────────────────────────────────────────
print("\n2. Authentication")

# Login with admin
r = requests.post(f"{API}/auth/login", json={
    "email": ADMIN_EMAIL,
    "password": ADMIN_PASSWORD
})
test("POST /auth/login (admin)", r)
admin_token = None
refresh_tok = None
if r.status_code == 200:
    tokens = r.json()
    admin_token = tokens["access_token"]
    refresh_tok = tokens["refresh_token"]
    print(f"    Token type: {tokens['token_type']}, expires_in: {tokens['expires_in']}s")

# Login with engineer (if configured)
engineer_token = None
if ENGINEER_EMAIL and ENGINEER_PASSWORD:
    r = requests.post(f"{API}/auth/login", json={
        "email": ENGINEER_EMAIL,
        "password": ENGINEER_PASSWORD
    })
    test("POST /auth/login (engineer)", r)
    engineer_token = r.json()["access_token"] if r.status_code == 200 else None

# Bad credentials
r = requests.post(f"{API}/auth/login", json={
    "email": ADMIN_EMAIL,
    "password": "wrongpassword"
})
test("POST /auth/login (bad creds) -> 401", r, 401)

if admin_token:
    # Get me
    r = requests.get(f"{API}/auth/me", headers=auth_header(admin_token))
    test("GET /auth/me", r)
    if r.status_code == 200:
        me = r.json()
        print(f"    User: {me['full_name']} ({me['email']}), role={me['role']}")
        org_id = str(me["organization_id"])

    # Refresh token
    r = requests.post(f"{API}/auth/refresh", json={"refresh_token": refresh_tok})
    test("POST /auth/refresh", r)

    # Register new user
    rand_email = f"test-{random.randint(10000,99999)}@test.com"
    r = requests.post(f"{API}/auth/register", json={
        "email": rand_email,
        "password": "testpass123",
        "full_name": "Test User",
        "organization_name": "Test Org",
        "role": "viewer"
    })
    test("POST /auth/register", r, 201)

    # Duplicate registration
    r = requests.post(f"{API}/auth/register", json={
        "email": rand_email,
        "password": "testpass123",
        "full_name": "Test User",
        "organization_name": "Test Org",
        "role": "viewer"
    })
    test("POST /auth/register (duplicate) -> 409", r, 409)


# ── 3. Equipment ─────────────────────────────────────────────
print("\n3. Equipment")

equip_id = None
if admin_token:
    # List equipment (paginated response: {items, total, page, page_size})
    r = requests.get(f"{API}/equipment", headers=auth_header(admin_token))
    test("GET /equipment", r)
    if r.status_code == 200:
        data = r.json()
        items = data.get("items", [])
        print(f"    Equipment count: {data['total']}, page items: {len(items)}")
        if items:
            equip_id = str(items[0]["id"])
            print(f"    First equipment: {items[0]['name']} ({items[0]['equipment_type']})")

    if equip_id:
        # Get single equipment
        r = requests.get(f"{API}/equipment/{equip_id}", headers=auth_header(admin_token))
        test("GET /equipment/{id}", r)

    # Create equipment
    r = requests.post(f"{API}/equipment", headers=auth_header(admin_token), json={
        "name": "Test Pump TP-999",
        "equipment_type": "pump",
        "location": "Test Lab",
        "manufacturer": "TestMfg",
        "model_number": "T-100",
        "serial_number": f"TST-{random.randint(100,999)}",
        "rated_power_kw": 15.0,
        "max_rpm": 3000
    })
    test("POST /equipment (create)", r, 201)
    new_equip_id = None
    if r.status_code == 201:
        new_equip_id = str(r.json()["id"])
        print(f"    Created: {r.json()['name']} (id={new_equip_id[:8]}...)")

    # Update equipment
    if equip_id:
        r = requests.put(f"{API}/equipment/{equip_id}", headers=auth_header(admin_token), json={
            "location": "Updated Location - Building E"
        })
        test("PUT /equipment/{id} (update)", r)

    # Delete equipment (soft delete - 204)
    if new_equip_id:
        r = requests.delete(f"{API}/equipment/{new_equip_id}", headers=auth_header(admin_token))
        test("DELETE /equipment/{id} (soft delete)", r, 204)

    # Unauthorized access
    r = requests.get(f"{API}/equipment", headers={"Authorization": "Bearer invalid-token"})
    test("GET /equipment (bad token) -> 401", r, 401)


# ── 4. Sensors ───────────────────────────────────────────────
print("\n4. Sensors")

if admin_token and equip_id:
    # Submit sensor reading
    r = requests.post(f"{API}/sensors/readings", headers=auth_header(admin_token), json={
        "equipment_id": equip_id,
        "air_temperature": 298.5,
        "process_temperature": 308.2,
        "rotational_speed": 1500,
        "torque": 42.5,
        "tool_wear": 100,
        "vibration": 5.2
    })
    test("POST /sensors/readings", r, 201)

    # Batch sensor readings
    r = requests.post(f"{API}/sensors/readings/batch", headers=auth_header(admin_token), json={
        "readings": [
            {
                "equipment_id": equip_id,
                "air_temperature": 299.0,
                "process_temperature": 309.0,
                "rotational_speed": 1520,
                "torque": 43.0,
                "tool_wear": 105,
                "vibration": 5.5
            },
            {
                "equipment_id": equip_id,
                "air_temperature": 300.0,
                "process_temperature": 310.0,
                "rotational_speed": 1480,
                "torque": 44.0,
                "tool_wear": 110,
                "vibration": 6.0
            }
        ]
    })
    test("POST /sensors/readings/batch", r, 201)
    if r.status_code == 201:
        print(f"    Batch result: {r.json()}")

    # Get sensor readings (query param equipment_id)
    r = requests.get(f"{API}/sensors/readings", headers=auth_header(admin_token),
                     params={"equipment_id": equip_id, "limit": 10})
    test("GET /sensors/readings?equipment_id=...", r)
    if r.status_code == 200:
        readings = r.json()
        print(f"    Readings count: {len(readings)}")

    # Get latest reading
    r = requests.get(f"{API}/sensors/latest/{equip_id}", headers=auth_header(admin_token))
    test("GET /sensors/latest/{equip_id}", r)


# ── 5. Predictions ───────────────────────────────────────────
print("\n5. Predictions")

if admin_token and equip_id:
    # Predict for equipment
    r = requests.post(f"{API}/predictions/predict", headers=auth_header(admin_token), json={
        "equipment_id": equip_id,
        "air_temperature": 301.5,
        "process_temperature": 311.8,
        "rotational_speed": 1400,
        "torque": 48.0,
        "tool_wear": 180,
        "vibration": 7.8
    })
    test("POST /predictions/predict", r)
    if r.status_code == 200:
        pred = r.json()
        print(f"    Failure probability: {pred.get('failure_probability', 'N/A')}")
        print(f"    Risk level: {pred.get('risk_level', 'N/A')}")
        print(f"    Predicted failure: {pred.get('predicted_failure', 'N/A')}")

    # Predict high-risk scenario
    r = requests.post(f"{API}/predictions/predict", headers=auth_header(admin_token), json={
        "equipment_id": equip_id,
        "air_temperature": 310.0,
        "process_temperature": 330.0,
        "rotational_speed": 2500,
        "torque": 70.0,
        "tool_wear": 400,
        "vibration": 15.0
    })
    test("POST /predictions/predict (high risk)", r)
    if r.status_code == 200:
        pred = r.json()
        print(f"    Failure probability: {pred.get('failure_probability', 'N/A')}")
        print(f"    Risk level: {pred.get('risk_level', 'N/A')}")

    # Get prediction history (returns {items, total, equipment_id})
    r = requests.get(f"{API}/predictions/history/{equip_id}", headers=auth_header(admin_token))
    test("GET /predictions/history/{equip_id}", r)
    if r.status_code == 200:
        hist = r.json()
        print(f"    Prediction history: {hist.get('total', 0)} records")

    # Get latest prediction
    r = requests.get(f"{API}/predictions/latest/{equip_id}", headers=auth_header(admin_token))
    test("GET /predictions/latest/{equip_id}", r)


# ── 6. Alerts ────────────────────────────────────────────────
print("\n6. Alerts")

if admin_token:
    # List alerts (paginated: {items, total, page, page_size})
    r = requests.get(f"{API}/alerts", headers=auth_header(admin_token))
    test("GET /alerts", r)
    if r.status_code == 200:
        alert_data = r.json()
        alert_items = alert_data.get("items", [])
        print(f"    Total alerts: {alert_data.get('total', len(alert_items))}")

    # Get active alerts
    r = requests.get(f"{API}/alerts/active", headers=auth_header(admin_token))
    test("GET /alerts/active", r)
    if r.status_code == 200:
        active_alerts = r.json()
        print(f"    Active alerts: {len(active_alerts)}")

        # If there are active alerts, test acknowledge
        if active_alerts:
            alert_id = str(active_alerts[0]["id"])
            r = requests.put(f"{API}/alerts/{alert_id}", headers=auth_header(admin_token), json={
                "status": "acknowledged"
            })
            test("PUT /alerts/{id} (acknowledge)", r)


# ── 7. Analytics ─────────────────────────────────────────────
print("\n7. Analytics")

if admin_token:
    # Dashboard overview
    r = requests.get(f"{API}/analytics/dashboard", headers=auth_header(admin_token))
    test("GET /analytics/dashboard", r)
    if r.status_code == 200:
        dash = r.json()
        print(f"    Total equipment: {dash.get('total_equipment')}")
        print(f"    Operational: {dash.get('operational_count')}, Warning: {dash.get('warning_count')}, Critical: {dash.get('critical_count')}")
        print(f"    Active alerts: {dash.get('active_alerts')}")
        print(f"    Avg risk: {dash.get('avg_risk_score')}")

    # Equipment health
    r = requests.get(f"{API}/analytics/equipment-health", headers=auth_header(admin_token))
    test("GET /analytics/equipment-health", r)

    # Trends
    r = requests.get(f"{API}/analytics/trends", headers=auth_header(admin_token),
                     params={"hours": 24})
    test("GET /analytics/trends", r)
    if r.status_code == 200:
        trends = r.json()
        print(f"    Trend data points: {trends.get('count', 0)}")


# ── 8. ML Admin ──────────────────────────────────────────────
print("\n8. ML Administration")

if admin_token:
    # List models
    r = requests.get(f"{API}/ml/models", headers=auth_header(admin_token))
    test("GET /ml/models", r)
    model_path = None
    if r.status_code == 200:
        models = r.json()
        print(f"    Available models: {len(models)}")
        if models:
            for m in models[:3]:
                algo = m.get("algorithm", m.get("name", "??"))
                print(f"      - {algo}")
            model_path = models[0].get("model_path")

    # Load a model
    if model_path:
        r = requests.post(f"{API}/ml/models/load", headers=auth_header(admin_token), json={
            "model_path": model_path
        })
        test("POST /ml/models/load", r)
        if r.status_code == 200:
            print(f"    Load result: {r.json()}")

    # Get active model
    r = requests.get(f"{API}/ml/models/active", headers=auth_header(admin_token))
    test("GET /ml/models/active", r)

    # Train a model via API
    r = requests.post(f"{API}/ml/train", headers=auth_header(admin_token), json={
        "algorithm": "random_forest",
        "data_filepath": "data/raw/ai4i2020.csv"
    })
    test("POST /ml/train", r)
    if r.status_code == 200:
        tr = r.json()
        print(f"    Trained: {tr.get('algorithm')} v{tr.get('version')}")
        if "metrics" in tr:
            m = tr["metrics"]
            print(f"    F1={m.get('f1', 'N/A')}, AUC={m.get('auc_roc', 'N/A')}")

    # Engineer should NOT be able to train (admin-only)
    if engineer_token:
        r = requests.post(f"{API}/ml/train", headers=auth_header(engineer_token), json={
            "algorithm": "random_forest"
        })
        test("POST /ml/train (engineer -> 403)", r, 403)


# ── Summary ──────────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed out of {passed + failed} tests")
print("=" * 60)

if errors:
    print("\nFailed tests:")
    for e in errors:
        print(f"  X {e}")

sys.exit(0 if failed == 0 else 1)
