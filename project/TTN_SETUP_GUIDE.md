# TTN API Setup Guide

## Quick Setup

1. **Install required package:**
   ```bash
   pip install requests
   ```

2. **Update `ttn_config.py`:**
   - Replace `your-application-id` with your TTN app ID
   - Replace `your-api-key` with your TTN API key  
   - Replace `your-device-id` with your device ID
   - Update cluster if needed (eu1, us1, au1)

3. **Get TTN Credentials:**
   - Go to [TTN Console](https://console.thethings.network/)
   - Navigate to your application
   - Copy Application ID
   - Generate API key with "Read application data" permission
   - Note your device ID

4. **Test the connection:**
   - Visit your dashboard
   - Check browser console for any errors
   - The widget should show real-time temperature data

## API Endpoint
The widget fetches data from: `/api/ttn/temperature/`

## Data Format Expected
Your TTN device should send payloads with a `temperature` field in the decoded payload.

## Troubleshooting
- Check browser console for error messages
- Verify API key permissions
- Ensure device is sending data
- Check cluster configuration






