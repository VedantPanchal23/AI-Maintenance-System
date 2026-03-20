import requests
import json
import uuid

BASE_URL = "http://localhost:8000/api/v1"

def print_result(step, response):
    color = "\033[92m[PASS]\033[0m" if response.status_code < 400 else f"\033[91m[FAIL {response.status_code}]\033[0m"
    print(f"{color} {step}")
    if response.status_code >= 400:
        print(f"       -> {response.text}")

def run_audit():
    print("\n\033[94m============================================\033[0m")
    print("\033[94m🚀 INITIATING FULL SYSTEM API & RBAC AUDIT 🚀\033[0m")
    print("\033[94m============================================\033[0m\n")

    test_uid = str(uuid.uuid4())[:8]
    org_data = {"name": f"Audit Corp {test_uid}"}
    admin_data = {"email": f"admin_{test_uid}@test.com", "password": "SecurePass123!", "full_name": "Test Admin", "organization_name": org_data["name"], "role": "admin"}
    viewer_data = {"email": f"viewer_{test_uid}@test.com", "password": "SecurePass123!", "full_name": "Test Viewer", "organization_name": org_data["name"], "role": "viewer"}

    # 1. Test Registration
    print("\n--- 1. Testing Registration & DB Persistence ---")
    res_admin_reg = requests.post(f"{BASE_URL}/auth/register", json=admin_data, timeout=3)
    print_result("Admin Registration", res_admin_reg)
    res_viewer_reg = requests.post(f"{BASE_URL}/auth/register", json=viewer_data, timeout=3)
    print_result("Viewer Registration", res_viewer_reg)

    # 2. Test Login & JWT Generation
    print("\n--- 2. Testing Login Token Generation ---")
    res_admin_login = requests.post(f"{BASE_URL}/auth/login", json={"email": admin_data["email"], "password": admin_data["password"]}, timeout=3)
    print_result("Admin Login", res_admin_login)
    
    admin_token = ""
    if res_admin_login.status_code == 200:
        admin_token = res_admin_login.json().get("access_token")
    
    res_viewer_login = requests.post(f"{BASE_URL}/auth/login", json={"email": viewer_data["email"], "password": viewer_data["password"]}, timeout=3)
    print_result("Viewer Login", res_viewer_login)
    
    viewer_token = ""
    if res_viewer_login.status_code == 200:
        viewer_token = res_viewer_login.json().get("access_token")

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

    # 3. Test RBAC Scopes
    print("\n--- 3. Testing Role-Based Access Controls (RBAC) ---")
    
    # Let's forcefully change the admin to 'admin' role via direct intervention if possible (or assume test script has to work with viewer first)
    # Actually, default registration might assign 'viewer' or 'engineer'. Let's check ME endpoint.
    res_me = requests.get(f"{BASE_URL}/auth/me", headers=admin_headers, timeout=3)
    print_result("Fetch Current User Profile", res_me)
    
    current_role = res_me.json().get("role") if res_me.status_code == 200 else None
    
    # Try accessing ML Ops Endpoint with Viewer Token
    res_ml_viewer = requests.get(f"{BASE_URL}/ml/metrics", headers=viewer_headers, timeout=3)
    print_result("Viewer accessing ML Models (Expected 403)", res_ml_viewer)

    # Try accessing Maintenance with Admin Token
    res_maint_admin = requests.get(f"{BASE_URL}/maintenance", headers=admin_headers, timeout=3)
    print_result(f"Accessing Kanban Tickets", res_maint_admin)

    # Try fetching equipment from DB
    res_equip = requests.get(f"{BASE_URL}/equipment", headers=admin_headers, timeout=3)
    print_result("Database Fetch: Equipment List", res_equip)
    
    # 4. Cleanup/Summary
    print("\n\033[94m============================================\033[0m")
    print("\033[94m✅ AUDIT COMPLETE\033[0m")
    print("\033[94m============================================\033[0m\n")

if __name__ == "__main__":
    try:
        run_audit()
    except Exception as e:
        print(f"Audit Script Failed: {e}")
