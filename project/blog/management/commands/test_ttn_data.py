from django.core.management.base import BaseCommand
from django.utils import timezone
from blog.models import TTNDevice, Uplink
import json
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Create test TTN device and temperature data for testing the dashboard'

    def handle(self, *args, **options):
        # Create a test TTN device
        device, created = TTNDevice.objects.get_or_create(
            device_id='test_temp_sensor_001',
            defaults={'last_seen': timezone.now()}
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created TTN device: {device.device_id}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'TTN device already exists: {device.device_id}')
            )
        
        # Create some sample temperature uplinks
        temperatures = [22.5, 23.1, 22.8, 23.5, 22.9, 23.2, 22.7, 23.0, 22.6, 23.3]
        
        for i, temp in enumerate(temperatures):
            # Create uplinks with timestamps going back in time
            timestamp = timezone.now() - timedelta(minutes=i*5)  # 5 minutes apart
            
            uplink = Uplink.objects.create(
                device=device,
                raw_payload=f'temperature={temp}',
                decoded_payload={'temperature': temp, 'humidity': 45 + random.randint(-5, 5)},
                rssi=-85 + random.randint(-10, 10),
                snr=8.5 + random.uniform(-2, 2),
                fcnt=i + 1,
                created_at=timestamp
            )
            
            self.stdout.write(
                f'Created uplink {i+1}: Temperature={temp}°C, RSSI={uplink.rssi}, SNR={uplink.snr:.1f}'
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {len(temperatures)} test uplinks')
        )
        
        # Update device last seen
        device.last_seen = timezone.now()
        device.save()
        
        self.stdout.write(
            self.style.SUCCESS('Test TTN data setup complete! You can now view the dashboard.')
        )


