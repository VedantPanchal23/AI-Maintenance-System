import requests

BASE_URL = "http://localhost:8000/api/v1"

org_name = "Global Manufacturing Ltd."

accounts = [
    {"email": "admin@demo.com", "password": "Password123!", "full_name": "Admin Director", "organization_name": org_name, "role": "admin"},
    {"email": "engineer@demo.com", "password": "Password123!", "full_name": "Lead Engineer", "organization_name": org_name, "role": "engineer"},
    {"email": "viewer@demo.com", "password": "Password123!", "full_name": "Plant Viewer", "organization_name": org_name, "role": "viewer"}
]

print("Creating gorgeous demo accounts for the presentation...")
for acct in accounts:
    res = requests.post(f"{BASE_URL}/auth/register", json=acct)
    if res.status_code == 201:
        print(f"✅ Created {acct['role'].capitalize()}: {acct['email']}")
    elif res.status_code == 409:
        print(f"🔹 {acct['role'].capitalize()} already exists: {acct['email']}")
    else:
        print(f"❌ Failed to create {acct['email']}: {res.text}")
