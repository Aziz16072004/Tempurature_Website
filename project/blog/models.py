from django.conf import settings
from django.db import models
from django.utils import timezone

class TTNDevice(models.Model):
    device_id = models.CharField(max_length=100, unique=True)
    last_seen = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.device_id

class Uplink(models.Model):
    device = models.ForeignKey(TTNDevice, on_delete=models.CASCADE)
    raw_payload = models.TextField(null=True, blank=True)
    decoded_payload = models.JSONField(null=True, blank=True)
    rssi = models.IntegerField(null=True, blank=True)
    snr = models.FloatField(null=True, blank=True)
    fcnt = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
class User(models.Model):
    fullName = models.CharField(max_length=200)
    email = models.CharField(max_length=200)
    password = models.CharField(max_length=200)
    created_date = models.DateTimeField(default=timezone.now)
   
    def __str__(self):
        return self.fullName
    
class Task(models.Model):
    user = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class Post(models.Model):
    author = models.TextField(default='Anonymous')
    title = models.CharField(max_length=200)
    text = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)
    published_date = models.DateTimeField(blank=True, null=True)

    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.author  
    
