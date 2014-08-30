from django.db import models
from django import forms as forms
from django.forms.widgets import *
from django.core.mail import send_mail, BadHeaderError

# Create your models here.

class TwitterStream(models.Model):
	text = models.CharField(max_length=200)
	created_at = models.CharField(max_length=200)
	retweet_count = models.CharField(max_length=200)
	sentiment = models.CharField(max_length=200)
	country = models.CharField(max_length=200)
	matches = models.CharField(max_length=200)
	
class ContactForm(forms.Form):
        name = forms.CharField()
        email = forms.EmailField()
        topic = forms.CharField()
        message = forms.CharField(widget=Textarea())
