# TTN Configuration File
# Update these values with your actual TTN application details

# Your TTN Application ID (found in TTN Console - NOT the AppEUI)
TTN_APPLICATION_ID = "lora-app123"

# Your TTN API Key (generate this in TTN Console - NOT the AppKey)
TTN_API_KEY = "NNSXS.DUSB7Q3IBCG3XJAYHNAW43Q5PIJA67JTQPUHCWA.3NXJU2RYUHJNIW2W5DNKPW3ZWUTIGW32TFJOZ7JQPKAGW7UCRFSA"
TTN_CLUSTER = "eu1"
# Your Device ID (the specific device you want to monitor)
DEVICE_ID = "lora-app123"

# TTN Cluster (usually eu1, us1, or au1)



# How often to fetch data (in seconds)
UPDATE_INTERVAL = 30

# Optional: Customize the API endpoint if needed
TTN_API_BASE_URL = f"https://{TTN_CLUSTER}.cloud.thethings.network/api/v3"

# Optional: Add additional headers if needed
ADDITIONAL_HEADERS = {
    # "Custom-Header": "value"
}

# Optional: Timeout for API requests (in seconds)
REQUEST_TIMEOUT = 10

# Your Device Credentials (for reference - these are LoRaWAN credentials)
DEVICE_APPEUI = "1231231231231231"
DEVICE_DEVEUI = "70B3D57ED00721A2"
DEVICE_APPKEY = "A22B377A064DBB4DFAEFDEDF9376158B"

# Alternative API endpoints you can try if the main one doesn't work
ALTERNATIVE_ENDPOINTS = {
    "uplink_messages": "/as/applications/{app_id}/devices/{device_id}/packages/storage/uplink_message",
    "device_info": "/as/applications/{app_id}/devices/{device_id}",
    "application_data": "/as/applications/{app_id}/packages/storage/uplink_message"
}

# Configuration Status
CONFIG_STATUS = {
    "device_configured": True,  # Your device credentials are set
    "application_configured": True,  # Your application ID is set
    "api_key_configured": True,  # Your API key is set
    "status": "fully_configured",  # All credentials are ready
    "next_step": "Test your configuration and view the temperature widget!"
}
