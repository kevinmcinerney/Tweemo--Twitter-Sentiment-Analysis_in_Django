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
	emoticons = models.CharField(max_length=200)
	hashtags = models.CharField(max_length=200)
	negated_words = models.CharField(max_length=200)
	exclamated_words = models.CharField(max_length=200)
	boosted = models.CharField(max_length=200)
	consecutive_words = models.CharField(max_length=200)
	repeated_letter_words = models.CharField(max_length=200)
	capitalized_words = models.CharField(max_length=200)
	search_term = models.CharField(max_length=200)
	search_list = models.CharField(max_length=200)

	
class ContactForm(forms.Form):
        name = forms.CharField()
        email = forms.EmailField()
        topic = forms.CharField()
        message = forms.CharField(widget=Textarea())
