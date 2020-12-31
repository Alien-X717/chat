
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
# Create your models here.

class User(AbstractUser):
    profile_pic =models.ImageField(null=True,blank=True,editable=True, upload_to="profilepics/",default="profilepics/user.jpg")

class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sender', on_delete=models.CASCADE)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='recipient', on_delete=models.CASCADE)
    is_readed = models.BooleanField(default=False)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.sender.username

    def recent_msgs(self):
        return Message.objects.order_by('timestamp').all()    

class contact(models.Model):
    channel_name = models.TextField(null=True)
    contact_id = models.ForeignKey(settings.AUTH_USER_MODEL,related_name='contact',on_delete=models.DO_NOTHING)