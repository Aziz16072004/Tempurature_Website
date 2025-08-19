import json
import base64
import paho.mqtt.client as mqtt
from django.core.management.base import BaseCommand
from django.conf import settings
from blog.models import TTNDevice, Uplink

def on_connect(client, userdata, flags, rc):
    print("Connected with result code", rc)
    client.subscribe("#")  # Subscribe to all topics temporarily for testing

def on_message(client, userdata, msg):
    print(f"Received message on topic {msg.topic}")
    data = json.loads(msg.payload.decode())
    dev_id = data['end_device_ids']['device_id']
    uplink = data['uplink_message']
    decoded = uplink.get('decoded_payload')
    raw = uplink.get('frm_payload')

    device, _ = TTNDevice.objects.get_or_create(device_id=dev_id)
    Uplink.objects.create(
        device=device,
        raw_payload=raw,
        decoded_payload=decoded,
        fcnt=uplink.get('f_cnt')
    )
    print(f"[UPLINK] {dev_id}: {decoded or raw}")

def send_downlink(client, dev_id, fport, payload_bytes):
    topic = f"v3/{settings.TTN_APP_ID}/devices/{dev_id}/down/push"
    message = {
        "downlinks": [{
            "f_port": fport,
            "frm_payload": payload_bytes,  # base64 string
            "priority": "NORMAL"
        }]
    }
    client.publish(topic, json.dumps(message))
    print(f"[DOWNLINK] Sent to {dev_id}")

class Command(BaseCommand):
    help = "Connect to TTN via MQTT"

    def handle(self, *args, **options):
        client = mqtt.Client()
        client.username_pw_set(
            f"{settings.TTN_APP_ID}@eu1",  # Add tenant if needed, else just use TTN_APP_ID
            settings.TTN_API_KEY
        )
        client.tls_set()
        client.on_connect = on_connect
        client.on_message = on_message

        client.connect(settings.TTN_MQTT_HOST, 8883)
        client.loop_start()  # Run network loop in background

        # Send test downlink after connection
        import time
        time.sleep(2)  # Wait a bit to ensure connection and subscription

        device_id = "lora-app123"  # Replace with your device id
        payload = base64.b64encode(b"Hello device").decode()
        send_downlink(client, device_id, 1, payload)

        client.loop_forever()

