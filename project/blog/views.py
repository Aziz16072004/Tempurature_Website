from django.http import HttpResponse ,JsonResponse,HttpResponseNotAllowed
from django.shortcuts import render,redirect
from .form import UserSignInForm , UserSignUpForm
from .models import User , Task
from django.contrib import messages
import json
import requests
from django.utils import timezone
from datetime import timedelta
import sys
import os

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
                print("Invalid login")
        else:
            print("Form errors:", form.errors)
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
                print("User with this email already exists.")
            else:
                user = form.save()
                print("Saved user:", user)
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
    """API endpoint to get latest temperature data from TTN"""
    try:
        # Check if TTN configuration is properly set
        if not TTN_API_KEY or TTN_API_KEY.strip().lower() == "your-api-key":
            return JsonResponse({
                'temperature': None,
                'device_id': DEVICE_ID,  # Your actual device ID
                'last_update': None,
                'rssi': None,
                'snr': None,
                'source': 'ttn_api',
                'error': 'Configuration required',
                'message': f'Device {DEVICE_ID} and Application {TTN_APPLICATION_ID} are configured, but you need to update TTN_API_KEY in ttn_config.py',
                'device_info': {
                    'device_id': DEVICE_ID,
                    'application_id': TTN_APPLICATION_ID,
                    'appeui': '1231231231231231',
                    'deveui': '70B3D57ED00721A2',
                    'status': 'device_and_app_ready'
                }
            }, status=400)
        
        # Try multiple TTN endpoints to find available data
        # Order: Try data endpoints first, device info last
        endpoints_to_try = [
            # 1. Try to get latest uplink message from device storage with FPort 1
            f"{TTN_API_BASE_URL}/as/applications/{TTN_APPLICATION_ID}/devices/{DEVICE_ID}/packages/storage/uplink_message?f_port=1&limit=1",
            # 2. Try application-wide storage with FPort 1 filter
            f"{TTN_API_BASE_URL}/as/applications/{TTN_APPLICATION_ID}/packages/storage/uplink_message?f_port=1&limit=10",
            # 3. Try device-specific storage with FPort 1 filter
            f"{TTN_API_BASE_URL}/as/applications/{TTN_APPLICATION_ID}/devices/{DEVICE_ID}/packages/storage/uplink_message?f_port=1",
            # 4. Try device-specific storage without FPort filter
            f"{TTN_API_BASE_URL}/as/applications/{TTN_APPLICATION_ID}/devices/{DEVICE_ID}/packages/storage/uplink_message?limit=1",
            # 5. Try application-wide storage without FPort filter
            f"{TTN_API_BASE_URL}/as/applications/{TTN_APPLICATION_ID}/packages/storage/uplink_message?limit=10",
            # 6. Device info (fallback - only if no data found)
            f"{TTN_API_BASE_URL}/as/applications/{TTN_APPLICATION_ID}/devices/{DEVICE_ID}"
        ]
        
        headers = {
            "Authorization": f"Bearer {TTN_API_KEY}",
            "Accept": "application/json",
            **ADDITIONAL_HEADERS
        }
        
        # Try each endpoint until we find data
        for i, ttn_api_url in enumerate(endpoints_to_try):
            print(f"Trying endpoint {i+1}: {ttn_api_url}")
            
            try:
                response = requests.get(ttn_api_url, headers=headers, timeout=REQUEST_TIMEOUT)
                print(f"Endpoint {i+1} - Status: {response.status_code}, Content-Length: {len(response.text)}")
                
                if response.status_code == 200 and response.text.strip():
                    # We found data!
                    try:
                        data = response.json()
                        print(f"Successfully parsed JSON from endpoint {i+1}")
                        print(f"Data structure: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                        
                        # Handle different response structures
                        if 'result' in data and 'uplink_message' in data['result']:
                            # Single uplink message response
                            uplink = data['result']['uplink_message']
                            print(f"Found single uplink message from endpoint {i+1}")
                            return _extract_temperature_data(uplink)
                            
                        elif 'result' in data and isinstance(data['result'], list) and len(data['result']) > 0:
                            # List of messages - find the most recent one
                            messages = data['result']
                            print(f"Found {len(messages)} messages from endpoint {i+1}")
                            
                            # Sort by timestamp if available, otherwise use first
                            if messages and 'received_at' in messages[0]:
                                messages.sort(key=lambda x: x.get('received_at', ''), reverse=True)
                            
                            uplink = messages[0]  # Use most recent message
                            print(f"Using most recent message from {len(messages)} available")
                            return _extract_temperature_data(uplink)
                            
                        elif 'ids' in data and i == 3:  # Only endpoint 4 (device info)
                            # Device info response - this means no data was found
                            print(f"Reached device info endpoint - no data available")
                            return JsonResponse({
                                'temperature': None,
                                'device_id': data.get('ids', {}).get('device_id'),
                                'last_update': data.get('last_seen'),
                                'rssi': None,
                                'snr': None,
                                'source': 'ttn_api',
                                'message': 'Device found but no uplink messages available',
                                'endpoint_used': f"endpoint_{i+1}",
                                'device_status': 'active' if data.get('last_seen') else 'inactive',
                                'debug_note': 'This endpoint only provides device status, not temperature data'
                            })
                        else:
                            print(f"Unexpected data structure from endpoint {i+1}: {data}")
                            continue
                            
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error from endpoint {i+1}: {e}")
                        continue
                else:
                    print(f"Endpoint {i+1} returned no data or error")
                    continue
                    
            except Exception as e:
                print(f"Error with endpoint {i+1}: {e}")
                continue
        
        # If we get here, no endpoint returned usable data
        return JsonResponse({
            'temperature': None,
            'device_id': DEVICE_ID,
            'last_update': None,
            'rssi': None,
            'snr': None,
            'source': 'ttn_api',
            'error': 'No data available',
            'message': 'Tried multiple TTN endpoints but found no uplink messages or temperature data',
            'debug_info': {
                'endpoints_tried': endpoints_to_try,
                'application_id': TTN_APPLICATION_ID,
                'device_id': DEVICE_ID,
                'suggestion': 'Check if device has sent any uplink messages recently'
            }
        }, status=404)
            
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            'temperature': None,
            'device_id': None,
            'last_update': None,
            'rssi': None,
            'snr': None,
            'source': 'ttn_api',
            'error': 'Network error',
            'message': str(e)
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'temperature': None,
            'device_id': None,
            'last_update': None,
            'rssi': None,
            'snr': None,
            'source': 'ttn_api',
            'error': 'Unexpected error',
            'message': str(e)
        }, status=500)

def _extract_temperature_data(uplink):
    """Helper method to extract temperature data from uplink message"""
    try:
        # Get decoded payload
        decoded_payload = uplink.get('decoded_payload', {})
        temperature = decoded_payload.get('temperature')
        
        # Get device info
        device_id = uplink.get('end_device_ids', {}).get('device_id')
        
        # Get timestamp
        received_at = uplink.get('received_at')
        
        # Get signal quality
        rx_metadata = uplink.get('rx_metadata', [{}])[0] if uplink.get('rx_metadata') else {}
        rssi = rx_metadata.get('rssi')
        snr = rx_metadata.get('snr')
        
        if temperature is not None:
            return JsonResponse({
                'temperature': temperature,
                'device_id': device_id,
                'last_update': received_at,
                'rssi': rssi,
                'snr': snr,
                'source': 'ttn_api'
            })
        else:
            return JsonResponse({
                'temperature': None,
                'device_id': device_id,
                'last_update': received_at,
                'rssi': rssi,
                'snr': snr,
                'source': 'ttn_api',
                'message': 'No temperature data in payload'
            })
    except Exception as e:
        return JsonResponse({
            'temperature': None,
            'device_id': None,
            'last_update': None,
            'rssi': None,
            'snr': None,
            'source': 'ttn_api',
            'error': 'Data extraction error',
            'message': str(e)
        }, status=500)

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
# def post_new(request):
#     form = PostForm()
#     return render(request, 'blog/post_edit.html', {'form': form})