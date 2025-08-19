# TTN v3 API Setup Guide

## Important Note
The credentials you have (AppEUI, DevEUI, AppKey) are **LoRaWAN device credentials** used for device registration and communication. For the temperature widget to fetch data, you need **TTN v3 API credentials**.

## Step-by-Step Setup

### 1. Access TTN Console
- Go to [TTN Console](https://console.thethings.network/)
- Sign in with your account

### 2. Find Your Application
- In the left sidebar, click on "Applications"
- Find and click on your application (the one with AppEUI: 1231231231231231)

### 3. Get Application ID
- In your application overview, you'll see "Application ID" at the top
- This is NOT the AppEUI - it's usually a human-readable name
- Copy this Application ID

### 4. Generate API Key
- In the left sidebar, click on "API keys"
- Click "Add API key"
- Give it a name (e.g., "Temperature Widget")
- Select these permissions:
  - ✅ "Read application data"
  - ✅ "Read application info"
- Click "Create API key"
- **IMPORTANT**: Copy the API key immediately (you won't see it again!)

### 5. Get Device ID
- In the left sidebar, click on "End devices"
- Find your device (with DevEUI: 70B3D57ED00721A2)
- The Device ID is usually the same as DevEUI or a custom name
- Copy this Device ID

### 6. Update Configuration
Update `ttn_config.py` with your actual values:
```python
TTN_APPLICATION_ID = "your-actual-application-id"
TTN_API_KEY = "your-actual-api-key"
DEVICE_ID = "your-actual-device-id"
```

### 7. Test Connection
- Visit your dashboard
- Check browser console for any errors
- The widget should show real-time temperature data

## Example Configuration
```python
# Example (replace with your actual values)
TTN_APPLICATION_ID = "my-temperature-app"
TTN_API_KEY = "NNSXS.ABC123DEF456..."
DEVICE_ID = "70B3D57ED00721A2"
```

## Troubleshooting

### "Configuration required" error
- Make sure you've updated `ttn_config.py` with real values
- Don't leave the placeholder values

### "TTN API error: 401" 
- Check your API key is correct
- Ensure API key has "Read application data" permission

### "TTN API error: 404"
- Verify your Application ID and Device ID are correct
- Check if your device has sent any data recently

### No temperature data
- Ensure your device is sending data with a `temperature` field
- Check the decoded payload format in TTN Console

## Data Format Expected
Your TTN device should send payloads that decode to:
```json
{
  "temperature": 23.5,
  "humidity": 45
}
```

## Need Help?
- Check TTN Console for device activity
- Verify payload decoder is working
- Look at browser console for detailed error messages



