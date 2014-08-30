from django.http import HttpResponse
from django.template.loader import get_template # used by temp_test
from django.template import Context # used by temp_test
from django.core.context_processors import csrf
from tweemo.models import TwitterStream
from tweemo.models import n_sent
from tweemo.models import nt_sent
from tweemo.models import p_sent
from tweemo.models import n_sent2
from tweemo.models import p_sent2
from tweemo.models import England_p_sent2
from tweemo.models import Ireland_p_sent2
from tweemo.models import America_p_sent2
from tweemo.models import France_p_sent2
from tweemo.models import Germany_p_sent2
from tweemo.models import Canada_p_sent2
from tweemo.models import Spain_p_sent2
from django.shortcuts import render_to_response
from django.template import RequestContext
import tweepy
from tweepy import API
import pymongo
import sys
import sys
import json
from nltk.stem.lancaster import LancasterStemmer
 


def home(request):
	return render_to_response('home.html',{'here': TwitterStream.objects.all() })

def results(request):

    if 'query' in request.GET:
	message = request.GET['query']
        message = message.encode('ascii','ignore')
	pull_tweets(message, 'Ireland')
	pull_tweets(message, 'America')
	pull_tweets(message, 'France')
	pull_tweets(message, 'Germany')
	pull_tweets(message, 'Spain')
	pull_tweets(message, 'Canada')
	pull_tweets(message, 'England')
	pull_tweets(message, 'All')
		
    else:
        message = 'You submitted an empty form.'


    p = ''
    nt = ''
    n = ''
    p2 = ''
    n2 = ''
    print 'outside'
    for x in p_sent.objects.all():
	print 'inside'
	p = x.positive
    for x in nt_sent.objects.all():
	nt = x.neutral
    for x in n_sent.objects.all():
	n = x.negative
    for x in p_sent2.objects.all():
	p2 = x.positive
    for x in n_sent2.objects.all():
	n2 = x.negative

    Ireland_p2 = ''    
    England_p2 = ''
    America_p2 = ''
    France_p2 = ''
    Spain_p2 = ''
    Canada_p2 = ''
    Germany_p2 = ''  

    for x in Ireland_p_sent2.objects.all():
	Ireland_p2 = x.positive
    for x in England_p_sent2.objects.all():
	England_p2 = x.positive
    for x in America_p_sent2.objects.all():
	America_p2 = x.positive
    for x in France_p_sent2.objects.all():
	France_p2 = x.positive
    for x in Spain_p_sent2.objects.all():
	Spain_p2 = x.positive
    for x in Canada_p_sent2.objects.all():
	Canada_p2 = x.positive
    for x in Germany_p_sent2.objects.all():
	Germany_p2 = x.positive
   


    dictData=[[ 'Sentiment', 'Polarity'],['Positive', p ],['Negative', n ],['Objective', nt ]]
    dictData2=[[ 'Sentiment', 'Polarity'],['Positive', p2 ],['Negative', n2 ]]
    dictData3=[['City','Sentiment'],[ 'Ireland', Ireland_p2 ],[ 'United Kingdom', England_p2 ],[ 'America', America_p2 ],[ 'France', France_p2 ], [ 'Germany', Germany_p2 ],[ 'Canada', Canada_p2 ], [ 'Spain', Spain_p2 ]]

    return render_to_response('results.html',{'here': TwitterStream.objects.all() , 'djangodict': json.dumps(dictData),'djangodict2': json.dumps(dictData2), 'djangodict3': json.dumps(dictData3), 'query': message } )

#def results(request):
	#return render_to_response('results.html',{'here': TwitterStream.objects.all() })

def contactus(request):
	return render_to_response('contactus.html',{'here': TwitterStream.objects.all() })

def aboutus(request):
	return render_to_response('aboutus.html',{'here': TwitterStream.objects.all() })

"""def temp_test(request): # this function 
	here = 'spaggetti'
	t = get_template('temp_example.html')
	html = t.render(Context({'here': here}))
	return HttpResponse(html)"""

def tweets(request):
	return render_to_response('temp_example.html',
		{'here': TwitterStream.objects.all() })

def pull_tweets(q, country):
	
	ckey = "UJpisXUidLEdjEMVQhNOw"
	csecret = "VoBehORY0X1NhNe1QaaUSiak2rqAQpV5Hiz7N4QueeY"
	atoken = "93476811-dCDo7Kic1RcRoVub33p2pMycnflvrj5qyegq682yB"
	asecret = "prwsP2dSD6UqlC2Pmaer0Vt5EyJTInGgOClOqT00c"

	auth = tweepy.OAuthHandler(ckey, csecret)
	auth.set_access_token(atoken, asecret)


	# Connection to Mongo DB
	try:
	    conn=pymongo.MongoClient()
	    print "Connected successfully!!!"
	except pymongo.errors.ConnectionFailure, e:
	   print "Could not connect to MongoDB: %s" % e 
	conn

	#Define my mongoDB database
	db = conn.storage

	# Define my collection where I'll insert my search
	posts = db.tweemo_twitterstream
	p_sent = db.tweemo_p_sent
	n_sent = db.tweemo_n_sent
	nt_sent = db.tweemo_nt_sent
	p_sent2 = db.tweemo_p_sent2
	n_sent2 = db.tweemo_n_sent2
	Ireland_p_sent2 = db.tweemo_ireland_p_sent2
	England_p_sent2 = db.tweemo_england_p_sent2
	America_p_sent2 = db.tweemo_america_p_sent2
	Spain_p_sent2 = db.tweemo_spain_p_sent2
	France_p_sent2 = db.tweemo_france_p_sent2
	Canada_p_sent2 = db.tweemo_canada_p_sent2
	Germany_p_sent2 = db.tweemo_germany_p_sent2
	
	posts.remove({})

	if country == 'Ireland':
		c = '53.344103,-6.267493,50mi'
		Ireland_p_sent2.remove({})
		ireland_p_dic2 = {}
	elif country == 'Canada':
		c = '43.653226,-79.383184,50mi'
		Canada_p_sent2.remove({})
		canada_p_dic2 = {}
	elif country == 'America':
		c = '40.7127,-74.0059,100mi'
		America_p_sent2.remove({})
		america_p_dic2 = {}
	elif country == 'Germany':
		c = '52.5167,13.3833,100mi'
		Germany_p_sent2.remove({})
		germany_p_dic2 = {}
	elif country == 'Spain':
		c = '40.4333,-3.7000,100mi' 
		Spain_p_sent2.remove({})
		spain_p_dic2 = {}
	elif country == 'England':
		c = '51.5072,0.1275,100mi'
		England_p_sent2.remove({})
		england_p_dic2 = {}
	elif country == 'France':
		c = '48.8567,2.3508,100mi'
		France_p_sent2.remove({})
		france_p_dic2 = {}
	elif country == 'All':
		p_sent.remove({})
		n_sent.remove({})
		nt_sent.remove({})
		p_sent2.remove({})
		n_sent2.remove({})
		p_dic = {}
		n_dic = {}
		nt_dic = {}
		p_dic2 = {}
		n_dic2 = {}

	api = tweepy.API(auth)
	query = q
	max_tweets = 10
	if country != 'All':
		searched_tweets = [status for status in tweepy.Cursor(api.search, q=query, lang="en", geocode=c).items(max_tweets)]

	else:
		searched_tweets = [status for status in tweepy.Cursor(api.search, q=query, lang="en").items(max_tweets)]

	
	search = []
	for tweet in searched_tweets:
		search.append(tweet)

	for tweet in search:
	    data ={}
	    data['text'] = tweet.text
	    posts.insert(data)

	scores = {}
	# BAD PRACTICE!!!!!!!!! USE STATIC FOLDER!!!!!!
	with open("/home/kevin/django-kevin/bin/twitter/assets/Dictionaries/output.txt") as f:
		for line in f:
	       		(key, val) = line.split('\t')
	       		scores[key] = int(val)

	word_list = []
	for line in posts.find():	
		if "text" in line:
			word_list.append(line['text'])
		
	tot = 0.0
	st = LancasterStemmer()

	sent_list=[]
	for i in range(len(word_list)):
		text = word_list[i]
		text = text.split()
		for word in text:
			if st.stem(word) in scores:
				tot += scores[st.stem(word)]
		sent_list.append(tot)
		tot = 0

	print country
	print sent_list

	p_total2 = 0
	p_total = 0
	n_total = 0
	neutral = 0
	n_total2 = 0
	
	for i in sent_list:
		if i < 0:
			n_total += 1
			n_total2 += i
		elif i > 0:
			p_total += 1
			p_total2 += i
		elif i == 0:
			neutral += 1
	
	geo_total = (p_total2 + n_total2)	 

	if country == 'Ireland':
		ireland_p_dic2['positive'] = geo_total
		Ireland_p_sent2.insert(ireland_p_dic2)
	elif country == 'Canada':
		canada_p_dic2['positive'] = geo_total
		Canada_p_sent2.insert(canada_p_dic2)
	elif country == 'America':
		america_p_dic2['positive'] = geo_total
		America_p_sent2.insert(america_p_dic2)
	elif country == 'Germany':
		germany_p_dic2['positive'] = geo_total
		Germany_p_sent2.insert(germany_p_dic2)
	elif country == 'Spain':
		spain_p_dic2['positive'] = geo_total
		Spain_p_sent2.insert(spain_p_dic2)
	elif country == 'England':
		england_p_dic2['positive'] = geo_total
		England_p_sent2.insert(england_p_dic2)
	elif country == 'France':
		france_p_dic2['positive'] = geo_total
		France_p_sent2.insert(france_p_dic2)
	elif country == 'All':
		p_dic['positive'] = p_total
		n_dic['negative'] = n_total
		nt_dic['neutral'] = neutral
		p_dic2['positive'] = p_total2
		n_dic2['negative'] = (n_total2 * -1)
		p_sent.insert(p_dic)
		n_sent.insert(n_dic)
		nt_sent.insert(nt_dic)
		n_sent2.insert(n_dic2)
		p_sent2.insert(p_dic2)
		
	return ''



	










