import requests
import random
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8000/api/v1"

def seed_data():
    # 1. Login to the Admin account we just created
    login_res = requests.post(f"{BASE_URL}/auth/login", json={"email": "admin@demo.com", "password": "Password123!"})
    if login_res.status_code != 200:
        print("Login failed!", login_res.text)
        return

    print("Authenticated successfully.")
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Add Equipment
    equipments = [
        {"name": "Haas VF-2 CNC Mill", "equipment_type": "cnc_mill", "location": "Sector A"},
        {"name": "Ingersoll Rand Air Compressor", "equipment_type": "air_compressor", "location": "Utility Room"},
        {"name": "Carrier Commerical Chiller", "equipment_type": "hvac_chiller", "location": "Roof Space Vault"},
        {"name": "Main Assembly Conveyor", "equipment_type": "conveyor", "location": "Assembly Line 1"},
        {"name": "Schuler Hydraulic Press", "equipment_type": "hydraulic_press", "location": "Heavy Machinery Bay"},
        {"name": "ABB Extrusion Motor", "equipment_type": "electric_motor", "location": "Sector B"}
    ]

    print("Populating 6 diverse pieces of equipment...")
    eq_ids = []
    for eq in equipments:
        res = requests.post(f"{BASE_URL}/equipment/", json=eq, headers=headers)
        if res.status_code == 201:
            data = res.json()
            eq_ids.append(data["id"])
            print(f"  ✅ Added {eq['name']}")
        else:
            print(f"  ❌ Error adding {eq['name']}: {res.text}")

    if not eq_ids:
        print("No equipment added. Exiting script.")
        return

    # 3. Add Maintenance Logs (Kanban Tickets)
    tickets = [
        {"equipment_id": eq_ids[0], "maintenance_type": "preventive", "description": "Monthly spindle calibration and axis alignment", "status": "todo", "priority": "high"},
        {"equipment_id": eq_ids[1], "maintenance_type": "corrective", "description": "Check filter pressure drops and replace intake", "status": "in_progress", "priority": "medium"},
        {"equipment_id": eq_ids[2], "maintenance_type": "predictive", "description": "Chemical coolant flush before seasonal freeze", "status": "completed", "priority": "low"},
        {"equipment_id": eq_ids[3], "maintenance_type": "corrective", "description": "Lubricate conveyor bearings and inspect drive belt", "status": "todo", "priority": "medium"}
    ]

    print("\nAdding Maintenance Kanban tickets...")
    for t in tickets:
        res = requests.post(f"{BASE_URL}/maintenance/", json=t, headers=headers)
        if res.status_code == 201:
            print(f"  ✅ Kanban Ticket Created: {t['description']}")
        else:
            print(f"  ❌ Failed to create ticket: {res.text}")

    # 4. Generate massive sensor readings
    print("\nInjecting historical sensor telemetry (Warning: this might take a moment)...")
    now = datetime.now()
    readings_batch = []
    
    for eq_id in eq_ids:
        # Generate exactly 24 hours of data (hourly) so the UI charts look active immediately
        for i in range(24): 
            dt = (now - timedelta(hours=i)).isoformat()
            readings_batch.append({
                "equipment_id": eq_id,
                "timestamp": dt,
                "air_temperature": round(random.uniform(295, 305), 2),
                "process_temperature": round(random.uniform(308, 315), 2),
                "rotational_speed": int(random.uniform(1450, 1600)),
                "torque": round(random.uniform(35, 45), 2),
                "tool_wear": int(random.uniform(40, 90)),
                "vibration": round(random.uniform(3.0, 8.0), 2)
            })

    # Batch post
    chunk_size = 50
    success = 0
    for i in range(0, len(readings_batch), chunk_size):
        chunk = readings_batch[i:i+chunk_size]
        batch_res = requests.post(f"{BASE_URL}/sensors/readings/batch", json={"readings": chunk}, headers=headers)
        if batch_res.status_code == 201:
            success += len(chunk)
            
    print(f"  ✅ Successfully injected {success} telemetry sensor data points into PostgreSQL.")
    print("\n🎉 The entire Database is fully loaded and presentation-ready! 🎉")

if __name__ == "__main__":
    seed_data()
