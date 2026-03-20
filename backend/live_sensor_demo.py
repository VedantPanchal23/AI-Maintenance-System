import requests
import random
import time
import uuid
from datetime import datetime, timezone

BASE_URL = "http://127.0.0.1:8000/api/v1"

def stream_live_data():
    print("\n" + "="*50)
    print("🚀 ACTIVATING LIVE TELEMETRY SIMULATOR 🚀")
    print("="*50 + "\n")
    
    # Login to get auth token
    login_res = requests.post(
        f"{BASE_URL}/auth/login", 
        json={"email": "admin@demo.com", "password": "Password123!"}
    )
    if login_res.status_code != 200:
        print("❌ Failed to log in. Please ensure the backend is running.")
        return
        
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Fetch all equipment for the organization
    equip_res = requests.get(f"{BASE_URL}/equipment/", headers=headers)
    if equip_res.status_code != 200:
        print("❌ Failed to fetch equipment.")
        return
        
    equipment_list = equip_res.json().get("items", [])
    if not equipment_list:
        print("⚠️ No equipment found! Please inject equipment first.")
        return
        
    print(f"📡 Found {len(equipment_list)} active assets. Initiating live WebSocket telemetry stream...")
    print("Press Ctrl+C to stop streaming.\n")
    
    try:
        while True:
            for eq in equipment_list:
                eq_id = eq["id"]
                
                # Generate a realistic live sensor pulse
                reading = {
                    "equipment_id": eq_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "air_temperature": round(random.uniform(298, 302), 2),
                    "process_temperature": round(random.uniform(310, 312), 2),
                    "rotational_speed": int(random.uniform(1490, 1510)),
                    "torque": round(random.uniform(39, 41), 2),
                    "tool_wear": int(random.uniform(50, 70)),
                    "vibration": round(random.uniform(4.0, 6.0), 2),
                    "power_consumption": round(random.uniform(10.0, 15.0), 2),
                    "pressure": round(random.uniform(100.0, 105.0), 2),
                    "humidity": round(random.uniform(40.0, 45.0), 2)
                }
                
                # Post to single reading endpoint (which triggers websocket broadcasts in the backend)
                res = requests.post(f"{BASE_URL}/sensors/readings", json=reading, headers=headers)
                
                if res.status_code == 201:
                    print(f"⚡ [LIVE] Pushed pulse for {eq['name'][:15]}... -> Status 201")
                else:
                    print(f"❌ Failed to push for {eq['name']}: {res.status_code}")
                    
            # Wait a few seconds before the next global pulse
            time.sleep(3)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Live Telemetry Simulator safely terminated.")

if __name__ == "__main__":
    stream_live_data()
