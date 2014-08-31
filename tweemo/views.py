from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template.loader import get_template # used by temp_test
from django.template import Context # used by temp_test
from django.core.context_processors import csrf
from tweemo.models import TwitterStream
from django.shortcuts import render_to_response
from django.template import RequestContext, Context
import tweepy
from tweepy import API
import pymongo
import sys
import sys
import json
from datetime import date,datetime, timedelta
from nltk.stem.lancaster import LancasterStemmer
'from nltk.corpus import stopwords, names'
from nltk import WordPunctTokenizer
from tweemo.models import ContactForm
from django import forms as forms
from django.forms.widgets import *
from django.core.mail import send_mail, BadHeaderError
import os


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
 


def home(request):
	return render_to_response('home.html')

def tweets(request):
	return render_to_response('tweets.html',
				{'here': TwitterStream.objects.all()} )

def stream(request):
	return render_to_response('stream.html')

def aboutus(request):
	return render_to_response('aboutus.html')

def usingtweemo(request):
	return render_to_response('usingtweemo.html')

def howto(request):
	return render_to_response('howto.html')

def gallary(request):
	return render_to_response('gallary.html')

def contactus(request):
		subject = request.POST.get('topic', '')
		message = request.POST.get('message', '')
		from_email = request.POST.get('email', '')

		if subject and message and from_email:
		        try:
					send_mail(subject, message, from_email, ['kevinmcinerney8@gmail.com'])
        		except BadHeaderError:
            			return HttpResponse('Invalid header found.')
        		return HttpResponseRedirect('/home/thankyou')
		else:
			return render_to_response('contactus.html', {'form': ContactForm()})
	
		return render_to_response('contactus.html', {'form': ContactForm()},
			RequestContext(request))

def thankyou(request):
		return render_to_response('thankyou.html')


message = ''
def results(request):

    overall_negative_count = 0

    if 'query' in request.GET:
	message = request.GET['query']
        message = message.encode('ascii','ignore')
	
	create_lexicon()
	data = pull_tweets(message)
		
    else:
        message = 'You submitted an empty form.'
    

    dictData=[[ 'Sentiment', 'Polarity'],['Negative', data[0][0]['negative_sentiment_count'] ],
					 ['Objective', data[0][0]['neutral_sentiment_count'] ],
					 ['Positive', data[0][0]['positive_sentiment_count'] ] ]


    dictData2=[[ 'Sentiment', 'Strength'],['Negative', data[1][0]['negative_sentiment_total'] ],
					  ['Positive', data[1][0]['positive_sentiment_total'] ] ]

    dictData3=[['City','Sentiment'],	[ 'Ireland', data[2][0]['Ireland'][0][0] ],	
					[ 'United Kingdom', data[2][0]['England'][0][0] ],	
					[ 'America', data[2][0]['America'][0][0] ],
					[ 'France', data[2][0]['France'][0][0]  ], 
					[ 'Germany', data[2][0]['Germany'][0][0] ],
					[ 'Canada', data[2][0]['Canada'][0][0]  ], 
					[ 'Spain', data[2][0]['Spain'][0][0]  ] ]

    dictData4=[	[  data[2][0]['Ireland'][0] ],
		[  data[2][0]['Spain'  ][0] ],
		[  data[2][0]['Germany'][0] ],
		[  data[2][0]['America'][0] ],
		[  data[2][0]['England'][0] ],
		[  data[2][0]['Canada'][0] ],
		[  data[2][0]['France'][0] ] ]
   
    day1 = str((date.today() - timedelta(days=2)))
    day2 = str((date.today() - timedelta(days=1)))
    day3 = str(date.today())
    dictData5=[ ['Day', 'Ireland', 'America', 'Germany', 'Spain', 'France', 'England', 'Canada'],
		[day1,					  data[3][0][0][0]['Ireland'],
				 		 	  data[3][0][0][0]['America'],
						 	  data[3][0][0][0]['Germany'],
						 	  data[3][0][0][0]['Spain'],
							  data[3][0][0][0]['France'],
							  data[3][0][0][0]['England'],
							  data[3][0][0][0]['Canada']],
		[day2,				          data[3][0][1][0]['Ireland'],
							  data[3][0][1][0]['America'],
							  data[3][0][1][0]['Germany'],
							  data[3][0][1][0]['Spain'],
							  data[3][0][1][0]['France'],
							  data[3][0][1][0]['England'],
							  data[3][0][1][0]['Canada']],
		[day3,		  	    	 	  data[3][0][2][0]['Ireland'],
							  data[3][0][2][0]['America'],			
							  data[3][0][2][0]['Germany'],
							  data[3][0][2][0]['Spain'],
							  data[3][0][2][0]['France'],
							  data[3][0][2][0]['England'],
							  data[3][0][2][0]['Canada']]]
				

    
    return render_to_response('results.html',
				{'here': TwitterStream.objects.all(),
				'djangodict': json.dumps(dictData),
				'djangodict2': json.dumps(dictData2), 
				'djangodict3': json.dumps(dictData3),
				'djangodict4': dictData4, 
				'djangodict5': json.dumps(dictData5),
				'query': message } )


def pull_tweets(q):

	conn = connect()
	ckey = "UJpisXUidLEdjEMVQhNOw"
	csecret = "VoBehORY0X1NhNe1QaaUSiak2rqAQpV5Hiz7N4QueeY"
	atoken = "93476811-dCDo7Kic1RcRoVub33p2pMycnflvrj5qyegq682yB"
	asecret = "prwsP2dSD6UqlC2Pmaer0Vt5EyJTInGgOClOqT00c"

	auth = tweepy.OAuthHandler(ckey, csecret)
	auth.set_access_token(atoken, asecret)

	#Define my mongoDB database
	db = conn.twitter

	# Define my collection where I'll insert my search
	posts = db.tweemo_twitterstream
	
	posts.remove({})
	
	country_dictionary = { 'Ireland': '53.344103,-6.267493,50mi', 
			       'Canada': '43.653226,-79.383184,50mi', 
                               'America': '40.7127,-74.0059,50mi', 
                               'Germany': '52.5167,13.3833,100mi', 
                               'Spain': '40.4333,-3.7000,100mi', 
                               'England': '51.5072,0.1275,100mi', 
                               'France': '48.8567,2.3508,100mi' }

	today = date.today()
	time_dictionary = []
	time_dictionary =[[today - timedelta(days=2)],
			  [today - timedelta(days=1)],
			  [today 		    ]]
	
	overall_negative_count = 0
	overall_neutral_count = 0
	overall_positive_count = 0
	overall_negative_strength = 0
	overall_positive_strength = 0
	
	date_list = []

	matches = []
	positive_sentiment_total = 0
	positive_sentiment_count = 0
	negative_sentiment_total = 0
	neutral_sentiment_count = 0
	negative_sentiment_count = 0
	tot = 0

	stopw = set()
	stopw = set('/app/assets/Dictionaries/stopwords.txt')
	word_splitter = WordPunctTokenizer()
	st = LancasterStemmer()
	m_names = '/app/assets/Dictionaries/males.txt'
	w_names = '/app/assets/Dictionaries/females.txt'
	c_score = {}
	c_score['Canada'] = []
	c_score['England'] = []
	c_score['America'] = []
	c_score['Spain'] = []
	c_score['France'] = []
	c_score['Germany'] = []
	c_score['Ireland'] = []
	time_sample_1 ={'Ireland': 0, 
			'Canada': 0, 
                        'America': 0, 
                        'Germany': 0, 
                        'Spain': 0, 
                        'England': 0, 
                        'France': 0 }
	time_sample_2 = time_sample_1.copy()
	time_sample_3 = time_sample_1.copy()
	master_samples = []
	api = tweepy.API(auth)
	query = q
	max_tweets = 1
	

	for time in time_dictionary:
		for country in country_dictionary:
			positive_sentiment_total = 0
			positive_sentiment_count = 0
			negative_sentiment_total = 0
			neutral_sentiment_count = 0
			negative_sentiment_count = 0	
			# this doesn'ensure the query is in the text!
			

			searched_tweets = [status for status in tweepy.Cursor(api.search, 
									      q=query, 
									      lang="en",
									      since=time[0],
									      until=time[0] + timedelta(days=1),
									      geocode=country_dictionary[country], 
									      ).items(max_tweets)]
			print len(searched_tweets)
			
			for tweet in searched_tweets:
				print tweet.text
				if tweet.text:	
					words = word_splitter.tokenize(tweet.text)
					for word in words:
						w = word.lower()
						if w in scores and w != stopw and w != m_names and w != w_names and len(word) > 2:
							tot += scores[w]
							matches.append(w)
					if tot < 0:
						negative_sentiment_count += 1
						negative_sentiment_total += tot
					elif tot > 0:
						positive_sentiment_count += 1
						positive_sentiment_total += tot
					elif tot == 0:
							neutral_sentiment_count += 1
				data = { 'text': tweet.text, 
		                         'created_at': tweet.created_at, 
		                         'retweet_count': tweet.retweet_count, 
		                         'sentiment': tot , 
		                         'country': country, 
		                         'matches': matches 
		                        }
				
				date_list.append(tweet.created_at)
	
				posts.insert(data)	
				tot = 0
				matches = []
					
			c_score[country].append(
					       [[positive_sentiment_total + negative_sentiment_total],
					       [negative_sentiment_total],
					       [positive_sentiment_total],
					       [neutral_sentiment_count],
					       [positive_sentiment_count],
					       [negative_sentiment_count],
					       [negative_sentiment_count + positive_sentiment_count + neutral_sentiment_count ]])
				
			#print c_score[country][0]

			overall_negative_strength += negative_sentiment_total
			overall_positive_strength += positive_sentiment_total
			overall_negative_count += negative_sentiment_count
			overall_positive_count += positive_sentiment_count
			overall_neutral_count += neutral_sentiment_count

	for country in c_score:
		c_score[country][0][0] = c_score[country][0][0][0] + c_score[country][1][0][0] + c_score[country][2][0][0]
		c_score[country][0][1] = c_score[country][0][1][0] + c_score[country][1][1][0] + c_score[country][2][1][0]
		c_score[country][0][2] = c_score[country][0][2][0] + c_score[country][1][2][0] + c_score[country][2][2][0]
		c_score[country][0][3] = c_score[country][0][3][0] + c_score[country][1][3][0] + c_score[country][2][3][0]
		c_score[country][0][4] = c_score[country][0][4][0] + c_score[country][1][4][0] + c_score[country][2][4][0]
		c_score[country][0][5] = c_score[country][0][5][0] + c_score[country][1][5][0] + c_score[country][2][5][0]
		c_score[country][0][6] = c_score[country][0][6][0] + c_score[country][1][6][0] + c_score[country][2][6][0]
	
	cursor = posts.find()

	for i in cursor:
		c = str(i['country'])
		if i['created_at'].date() == time_dictionary[2][0]:		
			time_sample_1[c] += i['sentiment'] 
		elif i['created_at'].date() == time_dictionary[1][0]:	
			time_sample_2[c] += i['sentiment'] 
		elif i['created_at'].date() == time_dictionary[0][0]:
			time_sample_3[c] += i['sentiment'] 

	for country in c_score:
		print country
		print c_score[country][0][6] 
		print c_score[country][1][6][0]
		print c_score[country][2][6][0]
		print c_score[country][0][6] - (c_score[country][1][6][0] + c_score[country][2][6][0])
		
	print time_sample_1
	print time_sample_2
	print time_sample_3
       		
	for i in time_sample_1:
		d1 =  c_score[i][0][6] - (c_score[i][1][6][0] + c_score[i][2][6][0])
		if d1 != 0:
			print '----1'
			print i
			print time_sample_1[i]
			print (c_score[i][0][6] - (c_score[i][1][6][0] + c_score[i][2][6][0]))
 
			time_sample_1[i] = float(time_sample_1[i] / (c_score[i][0][6] - (c_score[i][1][6][0] + c_score[i][2][6][0]))
)
		else:
			print ''
	for i in time_sample_2:
		if c_score[i][1][6][0] != 0:
			print '---2'
                        print i
                        print time_sample_2[i]
                        print  c_score[i][1][6][0]
			time_sample_2[i] = float(time_sample_2[i] / (c_score[i][1][6][0]))
		else:
			 print ''
	for i in time_sample_3:
		if c_score[i][2][6][0] != 0:
			print '---3'
                        print i
                        print time_sample_3[i]
                        print c_score[i][2][6][0]
			time_sample_3[i] = float(time_sample_3[i] / (c_score[i][2][6][0]))
		else:
			print ''

	print time_sample_1
	print time_sample_2
        print time_sample_3


	master_samples = [[time_sample_1],[time_sample_2],[time_sample_3]]
	
	
	data_count = {'negative_sentiment_count': overall_negative_count, 
		      'positive_sentiment_count': overall_positive_count, 
                      'neutral_sentiment_count': overall_neutral_count
                     }

	data_strength = {'negative_sentiment_total': (overall_negative_strength * -1),
                         'positive_sentiment_total': overall_positive_strength
                        }
	
	data_list = [[data_count],[data_strength],[c_score],[master_samples]]	
			
	return data_list

def connect():
	
	# Connection to Mongo DB
	url =  'mongodb://kevin:6841734aa@ds027489.mongolab.com:27489/twitter'
	try:
	    conn=pymongo.MongoClient(url)
	    print "Connected successfully!!!"
	except pymongo.errors.ConnectionFailure, e:
	   print "Could not connect to MongoDB: %s" % e 
	conn

	return conn

scores = {}
def create_lexicon():
	with open(os.path.join(BASE_DIR, 'assets/Dictionaries/super.txt')) as f:
		for line in f:
	       		(key, val) = line.split('\t')
	       		scores[key] = int(val)
	return scores








