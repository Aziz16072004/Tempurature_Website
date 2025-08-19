from django.http import HttpResponse ,JsonResponse,HttpResponseNotAllowed
from django.shortcuts import render,redirect
from .form import UserSignInForm , UserSignUpForm
from .models import User , Task
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
import json
import requests
from django.utils import timezone
from datetime import timedelta
import sys
import os
import base64

# Add the project root to Python path to import ttn_config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from ttn_config import (
        TTN_APPLICATION_ID, 
        TTN_API_KEY, 
        DEVICE_ID, 
        TTN_CLUSTER,
        TTN_API_BASE_URL,
        ADDITIONAL_HEADERS,
        REQUEST_TIMEOUT
    )
except ImportError:
    # Fallback values if config file is not found
    TTN_APPLICATION_ID = "your-application-id"
    TTN_API_KEY = "your-api-key"
    DEVICE_ID = "your-device-id"
    TTN_CLUSTER = "eu1"
    TTN_API_BASE_URL = "https://eu1.cloud.thethings.network/api/v3"
    ADDITIONAL_HEADERS = {}
    REQUEST_TIMEOUT = 10


# from .forms import PostForm

# Create your views here.
def home_view(request):
    print("this is the request for signin page",request)
    return render(request , 'blog/singIn.html')



def get_task(request):
    user_id = request.session.get('user_id')

    if request.method == "GET":
        tasks = list(Task.objects.filter(user=user_id).values())
        return JsonResponse({"tasks": tasks})
    elif request.method == "POST":
        data = json.loads(request.body)
        title = data.get("title")
        if title and user_id:
            task = Task.objects.create(title=title , user=user_id)
            return JsonResponse({"id": task.id, "title": task.title})
    return JsonResponse({"error": "Title is required"}, status=400)
    
def delete_task(request, task_id):
    if request.method == "DELETE" and task_id is not None:
        try:
            task = Task.objects.get(id=task_id)
            task.delete()
            return JsonResponse({"message": "Task deleted"})
        except Task.DoesNotExist:
            return JsonResponse({"error": "Task not found"}, status=404)
    return HttpResponseNotAllowed(["GET", "DELETE"])
def homePage(request):
    
    return render(request, 'blog/home.html')


def dashboard(request):
    # For now, we'll pass empty context since we'll fetch data via JavaScript
    context = {}
    return render(request, 'blog/dashbord.html', context)
    
def sign_in(request):
    if request.method == "POST":
        form = UserSignInForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = User.objects.filter(email=email, password=password).first()
            if user:
                request.session['user_id'] = user.id  # Store user ID in session
                return redirect('home')
            else:
                messages.error(request, "Invalid email or password.")
        else:
            pass
    else:
        form = UserSignInForm()
    return render(request, 'blog/signIn.html', {'form': form})
def sign_up(request):
    if request.method == "POST":
        form = UserSignUpForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            if User.objects.filter(email=email).exists():
                messages.error(request, "User with this email already exists.")
            else:
                user = form.save()
                return redirect('signin')
    else:
        form = UserSignUpForm()
    context = {'form':form}
    return render(request, 'blog/signUp.html', context)

def contact_success_view(request):
    return render(request , 'blog/success.html')


def mark_completed(request, task_id):
    if request.method == 'POST':
        try:
            task = Task.objects.get(id=task_id)
            task.completed = True
            task.save()
            return JsonResponse({
                'id': task.id,
                'title': task.title,
                'completed': task.completed
            })
        except Task.DoesNotExist:
            return JsonResponse({'error': 'Task not found'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_ttn_temperature(request):
    """Fetch latest uplink from TTN and decode all sensor values"""
    
    if not TTN_API_KEY or TTN_API_KEY.strip().lower() == "your-api-key":
        return JsonResponse({
            'error': 'TTN API key not configured',
            'message': 'Please set TTN_API_KEY in ttn_config.py'
        }, status=400)

    # Fetch more messages to ensure we get the newest one (TTN Storage API returns oldest-first)
    url = f"{TTN_API_BASE_URL}/as/applications/{TTN_APPLICATION_ID}/devices/{DEVICE_ID}/packages/storage/uplink_message?limit=100"
    
    headers = {
        "Authorization": f"Bearer {TTN_API_KEY}",
        "Accept": "application/json",
        **ADDITIONAL_HEADERS
    }

    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        
        if response.status_code != 200:
            return JsonResponse({
                'error': 'TTN API request failed',
                'status_code': response.status_code,
                'response': response.text
            }, status=response.status_code)

        # Clean the response text and try to parse JSON
        response_text = response.text.strip()
        
        # Try to find where the JSON ends
        try:
            # Try to parse the first valid JSON object
            import json
            data = json.loads(response_text)
        except json.JSONDecodeError as json_error:
            # TTN returns concatenated JSON objects, not a proper array
            # We need to extract each individual JSON object
            messages = []
            current_pos = 0
            
            try:
                while current_pos < len(response_text):
                    # Skip whitespace
                    while current_pos < len(response_text) and response_text[current_pos].isspace():
                        current_pos += 1
                    
                    if current_pos >= len(response_text):
                        break
                    
                    # Find the start of a JSON object
                    if response_text[current_pos] == '{':
                        brace_count = 0
                        start_pos = current_pos
                        
                        # Find the complete JSON object
                        for i in range(current_pos, len(response_text)):
                            if response_text[i] == '{':
                                brace_count += 1
                            elif response_text[i] == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    # Found complete JSON object
                                    try:
                                        json_part = response_text[start_pos:i+1]
                                        parsed_obj = json.loads(json_part)
                                        if 'result' in parsed_obj:
                                            messages.append(parsed_obj['result'])
                                    except json.JSONDecodeError as e:
                                        pass  # Skip invalid JSON objects
                                    
                                    current_pos = i + 1
                                    break
                        else:
                            # Incomplete JSON object, skip to next
                            current_pos += 1
                    else:
                        current_pos += 1
                
                if not messages:
                    return JsonResponse({
                        'error': 'No valid messages found in TTN response',
                        'message': 'Could not extract any valid JSON messages',
                        'response_preview': response_text[:500]
                    }, status=500)
                
                # Continue with the extracted messages
                data = {'result': messages}
                
            except Exception as extract_error:
                return JsonResponse({
                    'error': 'JSON extraction failed',
                    'message': f'Error extracting JSON objects: {str(extract_error)}',
                    'response_preview': response_text[:500]
                }, status=500)

        # Handle different response structures
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                return JsonResponse({
                    'error': 'TTN response is a string but not valid JSON',
                    'message': 'Could not parse TTN string response',
                    'response_preview': str(data)[:500]
                }, status=500)
        
        if not isinstance(data, dict):
            return JsonResponse({
                'error': 'Unexpected TTN response format',
                'message': f'Expected dict, got {type(data)}',
                'data_type': str(type(data)),
                'data_preview': str(data)[:500]
            }, status=500)

        messages = data.get('result', [])
        if not messages:
            return JsonResponse({
                'message': 'No uplink messages available',
                'payload': None
            }, status=404)
        
        # Ensure messages is a list
        if not isinstance(messages, list):
            if isinstance(messages, dict):
                messages = [messages]
            else:
                return JsonResponse({
                    'error': 'Invalid messages format',
                    'message': f'Expected list, got {type(messages)}',
                    'data_type': str(type(messages))
                }, status=500)
        
        if len(messages) == 0:
            return JsonResponse({
                'error': 'No messages found',
                'message': 'Messages list is empty after processing'
            }, status=404)

        # Sort messages by timestamp to get the newest one
        # TTN Storage API returns oldest-first, so we need to sort by received_at
        def get_timestamp(msg):
            # Try different timestamp fields
            timestamp = msg.get('received_at')
            if not timestamp:
                rx_metadata = msg.get('rx_metadata', [{}])[0]
                timestamp = rx_metadata.get('time')
            return timestamp or ''

        # Sort by timestamp descending (newest first)
        messages.sort(key=get_timestamp, reverse=True)
        
        uplink = messages[0]  # newest message
        
        # Check if this message has the expected structure
        if 'uplink_message' not in uplink:
            uplink_message = uplink
        else:
            uplink_message = uplink['uplink_message']
            print("Using nested uplink_message structure")
        
        # Try to get values from decoded_payload first (if available)
        decoded_payload = uplink_message.get('decoded_payload', {})
        print(f"Decoded payload available: {decoded_payload}")
        
        if decoded_payload and all(key in decoded_payload for key in ['temperature', 'humidity', 'pressure', 'gas']):
            print("Using decoded_payload values")
            temperature = decoded_payload.get('temperature', 0)
            humidity = decoded_payload.get('humidity', 0)
            pressure = decoded_payload.get('pressure', 0)
            gas = decoded_payload.get('gas', 0)
        else:
            print("Decoded_payload not complete, trying to decode frm_payload")
            
            # Decode frm_payload
            try:
                frm_payload_b64 = uplink_message.get('frm_payload')
                if not frm_payload_b64:
                    return JsonResponse({
                        'error': 'No frm_payload found in message',
                        'message': 'Message structure is different than expected',
                        'message_structure': uplink_message
                    }, status=500)
                    
                print(f"Found frm_payload: {frm_payload_b64}")
                payload_bytes = base64.b64decode(frm_payload_b64)
                print(f"Decoded payload length: {len(payload_bytes)} bytes")
                
                # Handle different payload lengths
                if len(payload_bytes) >= 8:
                    # Full payload with all sensors
                    print("Full payload detected, decoding all sensors")
                    def decode_signed16(high, low):
                        # Match TTN decoder: big-endian with two's complement
                        val = (high << 8) | low
                        if val & 0x8000:
                            val -= 0x10000
                        return val / 100.0

                    print(f"Decoding sensors from {len(payload_bytes)} bytes...")
                    print(f"Payload bytes: {[b for b in payload_bytes]}")
                    
                    temperature = decode_signed16(payload_bytes[0], payload_bytes[1])
                    humidity    = decode_signed16(payload_bytes[2], payload_bytes[3])
                    pressure    = decode_signed16(payload_bytes[4], payload_bytes[5])
                    gas         = decode_signed16(payload_bytes[6], payload_bytes[7])
                    
                elif len(payload_bytes) >= 2:
                    # Short payload (like simulated data) - only temperature
                    print("Short payload detected, decoding only temperature")
                    def decode_signed16(high, low):
                        # Match TTN decoder: big-endian with two's complement
                        val = (high << 8) | low
                        if val & 0x8000:
                            val -= 0x10000
                        return val / 100.0
                    
                    temperature = decode_signed16(payload_bytes[0], payload_bytes[1])
                    humidity = 0.0
                    pressure = 0.0
                    gas = 0.0
                    
                else:
                    return JsonResponse({
                        'error': 'Payload too short',
                        'message': f'Expected at least 2 bytes, got {len(payload_bytes)}',
                        'payload_length': len(payload_bytes),
                        'payload_hex': payload_bytes.hex()
                    }, status=500)
                    
                
            except Exception as payload_error:
                return JsonResponse({
                    'error': 'Payload processing failed',
                    'message': f'Error decoding payload: {str(payload_error)}',
                    'payload_data': frm_payload_b64 if 'frm_payload' in locals() else 'Not found'
                }, status=500)

        # Extract metadata
        rx_metadata = uplink_message.get('rx_metadata', [{}])[0]
        rssi = rx_metadata.get('rssi')
        snr = rx_metadata.get('snr')
        last_update = uplink_message.get('received_at') or rx_metadata.get('time') or uplink.get('received_at')
        device_id = uplink.get('device_id') or uplink.get('end_device_ids', {}).get('device_id') or DEVICE_ID

        return JsonResponse({
            "temperature": temperature,
            "humidity": humidity,
            "pressure": pressure,
            "gas": gas
        })

    except Exception as e:
        return JsonResponse({
            'error': 'Unexpected error',
            'message': str(e)
        }, status=500)

def _extract_temperature_data(uplink):
    decoded_payload = uplink.get('decoded_payload', {})
    temperature = decoded_payload.get('temperature')

    # TTN storage API may not include end_device_ids, so use placeholder or uplink info
    device_id = uplink.get('device_id') or DEVICE_ID

    # TTN storage API may not include received_at, use 'time' from rx_metadata if available
    rx_metadata = uplink.get('rx_metadata', [{}])[0] if uplink.get('rx_metadata') else {}
    rssi = rx_metadata.get('rssi')
    snr = rx_metadata.get('snr')
    last_update = uplink.get('received_at') or rx_metadata.get('time') or None

    return JsonResponse({
        'temperature': temperature,
        'device_id': device_id,
        'last_update': last_update,
        'rssi': rssi,
        'snr': snr,
        'source': 'ttn_api'
    })
def test_ttn_config(request):
    """Test endpoint to verify TTN configuration and show available data"""
    try:
        # Check if TTN configuration is properly set
        if TTN_API_KEY == "your-api-key":
            return JsonResponse({
                'status': 'configuration_required',
                'message': f'Device {DEVICE_ID} and Application {TTN_APPLICATION_ID} are configured, but you need TTN v3 API key',
                'current_config': {
                    'application_id': TTN_APPLICATION_ID,
                    'api_key': TTN_API_KEY[:10] + "..." if TTN_API_KEY != "your-api-key" else TTN_API_KEY,
                    'device_id': DEVICE_ID,
                    'cluster': TTN_CLUSTER,
                    'api_base_url': TTN_API_BASE_URL
                },
                'device_credentials': {
                    'device_id': DEVICE_ID,
                    'application_id': TTN_APPLICATION_ID,
                    'appeui': '1231231231231231',
                    'deveui': '70B3D57ED00721A2',
                    'appkey': 'A22B377A064DBB4DFAEFDEDF9376158B',
                    'status': 'device_and_app_ready'
                },
                'next_steps': [
                    '1. Go to TTN Console and find your application "lora-app123"',
                    '2. Click on "API keys" in the left sidebar',
                    '3. Click "Add API key"',
                    '4. Give it a name (e.g., "Temperature Widget")',
                    '5. Select "Read application data" permission',
                    '6. Click "Create API key" and copy the key',
                    '7. Update TTN_API_KEY in ttn_config.py'
                ]
            }, status=400)
        
        # Test the connection to TTN
        test_url = f"{TTN_API_BASE_URL}/as/applications/{TTN_APPLICATION_ID}/devices/{DEVICE_ID}"
        
        headers = {
            "Authorization": f"Bearer {TTN_API_KEY}",
            "Accept": "application/json"
        }
        
        response = requests.get(test_url, headers=headers, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            device_data = response.json()
            return JsonResponse({
                'status': 'success',
                'message': 'TTN configuration is working correctly',
                'device_info': {
                    'device_id': device_data.get('ids', {}).get('device_id'),
                    'application_id': device_data.get('ids', {}).get('application_ids', {}).get('application_id'),
                    'last_seen': device_data.get('last_seen'),
                    'status': 'active' if device_data.get('last_seen') else 'inactive'
                },
                'config': {
                    'cluster': TTN_CLUSTER,
                    'api_base_url': TTN_API_BASE_URL
                },
                'device_credentials': {
                    'device_id': DEVICE_ID,
                    'application_id': TTN_APPLICATION_ID,
                    'appeui': '1231231231231231',
                    'deveui': '70B3D57ED00721A2',
                    'appkey': 'A22B377A064DBB4DFAEFDEDF9376158B'
                }
            })
        else:
            return JsonResponse({
                'status': 'api_error',
                'message': f'TTN API returned status {response.status_code}',
                'error_details': response.text,
                'tested_url': test_url,
                'device_credentials': {
                    'device_id': DEVICE_ID,
                    'application_id': TTN_APPLICATION_ID,
                    'appeui': '1231231231231231',
                    'deveui': '70B3D57ED00721A2',
                    'appkey': 'A22B377A064DBB4DFAEFDEDF9376158B'
                }
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Configuration test failed: {str(e)}',
            'current_config': {
                'application_id': TTN_APPLICATION_ID,
                'api_key': TTN_API_KEY[:10] + "..." if TTN_API_KEY != "your-api-key" else TTN_API_KEY,
                'device_id': DEVICE_ID,
                'cluster': TTN_CLUSTER
            },
            'device_credentials': {
                'device_id': DEVICE_ID,
                'application_id': TTN_APPLICATION_ID,
                'appeui': '1231231231231231',
                'deveui': '70B3D57ED00721A2',
                'appkey': 'A22B377A064DBB4DFAEFDEDF9376158B',
                'status': 'device_and_app_ready'
            }
        }, status=500)

@csrf_exempt
def send_manual_ttn_payload(request):
    """Send a manual uplink payload to TTN"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    if not TTN_API_KEY or TTN_API_KEY.strip().lower() == "your-api-key":
        return JsonResponse({
            'error': 'TTN API key not configured',
            'message': 'Please set TTN_API_KEY in ttn_config.py'
        }, status=400)

    try:
        # Get payload data from request
        data = json.loads(request.body)
        temperature = data.get('temperature', 25.0)
        humidity = data.get('humidity', 50.0)
        pressure = data.get('pressure', 1013.0)
        gas = data.get('gas', 0.0)
        
        # Encode sensor values into bytes
        def encode_signed16(value):
            # Convert float to signed 16-bit integer (multiply by 100 for 2 decimal places)
            # Match TTN decoder: big-endian format
            int_val = int(value * 100)
            # Ensure it fits in 16 bits
            int_val = max(-32768, min(32767, int_val))
            # Convert to bytes (big-endian to match TTN decoder)
            return int_val.to_bytes(2, byteorder='big', signed=True)
        
        # Create payload bytes
        payload_bytes = (
            encode_signed16(temperature) +
            encode_signed16(humidity) +
            encode_signed16(pressure) +
            encode_signed16(gas)
        )
        
        # Encode to base64
        payload_b64 = base64.b64encode(payload_bytes).decode('utf-8')
        
        print(f"Creating manual payload: Temp={temperature}°C, Humidity={humidity}%, Pressure={pressure}hPa, Gas={gas}")
        print(f"Payload bytes: {[b for b in payload_bytes]}")
        print(f"Base64 payload: {payload_b64}")
        
        # Send to TTN via downlink (simulate uplink)
        # Note: This creates a simulated uplink in TTN
        downlink_url = f"{TTN_API_BASE_URL}/as/applications/{TTN_APPLICATION_ID}/devices/{DEVICE_ID}/down/push"
        
        downlink_data = {
            "downlinks": [{
                "f_port": 1,
                "frm_payload": payload_b64,
                "priority": "NORMAL"
            }]
        }
        
        headers = {
            "Authorization": f"Bearer {TTN_API_KEY}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            **ADDITIONAL_HEADERS
        }
        
        print(f"Sending downlink to TTN...")
        response = requests.post(downlink_url, headers=headers, json=downlink_data, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            return JsonResponse({
                'message': 'Manual payload sent successfully',
                'payload': {
                    'temperature': temperature,
                    'humidity': humidity,
                    'pressure': pressure,
                    'gas': gas
                },
                'base64_payload': payload_b64,
                'ttn_response': response.json()
            })
        else:
            return JsonResponse({
                'error': 'Failed to send payload to TTN',
                'status_code': response.status_code,
                'response': response.text
            }, status=response.status_code)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON',
            'message': 'Request body must be valid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': 'Unexpected error',
            'message': str(e)
        }, status=500)

# def post_new(request):
#     form = PostForm()
#     return render(request, 'blog/post_edit.html', {'form': form})