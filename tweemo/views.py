from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import Context
from django.core.context_processors import csrf
from tweemo.models import TwitterStream
from django.shortcuts import render_to_response
import tweepy
import pymongo
import sys
import json
from django.utils import encoding
from nltk.probability import FreqDist
from datetime import date, timedelta
from nltk import WordPunctTokenizer
from nltk import WhitespaceTokenizer
from tweemo.models import ContactForm
from django import forms as forms
from django.forms.widgets import *
from django.core.mail import send_mail, BadHeaderError
import os
import string
import operator


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

def research(request):
	return render_to_response('research.html')

def gallary(request):
	return render_to_response('gallary.html')

def contactus(request):
	return send_message(request)

def thankyou(request):
	return render_to_response('thankyou.html')

def results(request):

    if 'query' in request.GET:
	message = request.GET['query']
        message = message.encode('ascii','ignore')
	
	# create data necessary for graphs/analysis
	data = pull_tweets(message)
		
    else:
        message = 'You submitted an empty form.'

    search_list = []
    terms = WordPunctTokenizer().tokenize(message)
    for word in terms:
	if word != 'and' and word != 'or' and word != 'AND' and word != 'OR' and word != '"' and word != '-':
		search_list.append(convert_unicode_to_string(word.lower()))
    
    # call methods to parse data as required for graphs/analysis
    dictData = create_dictData(data)
    dictData2 = create_dictData2(data)
    dictData3 = create_dictData3(data)
    dictData4 = create_dictData4(data)
    dictData5 = create_dictData5(data)
    dictData6 = create_dictData6(data)
    dictData7 = create_dictData7(data)
    trend_terms = str(dictData7[1][0]) + str(',')+str(dictData7[2][0])
    for word in search_list:
    	trend_terms += str(',') + str(word)
    trends = str("<iframe style=''src='http://www.google.com/trends/fetchComponent?q")+str(trend_terms)+str("&cid=TIMESERIES_GRAPH_0&export=5' id=\"frame\" name=\"info2\" width=\"985px\" height=\"350px\" seamless=\"\"></iframe>")
   			    
    return render_to_response('results.html',
				{'here': TwitterStream.objects.all(),
				'djangodict': json.dumps(dictData),
				'djangodict2': json.dumps(dictData2), 
				'djangodict3': json.dumps(dictData3),
				'djangodict4': dictData4, 
				'djangodict5': json.dumps(dictData5),
				'djangodict6': json.dumps(dictData6),
				'djangodict7': json.dumps(dictData7),
				'trend_terms': trends,	
				'query': message } )


def pull_tweets(q):

	# For the purposes of iterating over the API.search by country
	country_dictionary = { 'Ireland': '53.344103,-6.267493,50mi', 
			       'Canada': '43.653226,-79.383184,50mi', 
                               'America': '40.7127,-74.0059,50mi', 
                               'Germany': '52.5167,13.3833,100mi', 
                               'Spain': '40.4333,-3.7000,100mi', 
                               'England': '51.5072,0.1275,100mi', 
                               'France': '48.8567,2.3508,100mi' }

	# For the purposes of iterating over the API.search by day
	today = date.today()
	time_list =[[today - timedelta(days=2)],
			  [today - timedelta(days=1)],
			  [today 		    ]]
	
	# initialize/store total values (not by country or day) for pie charts
	overall_negative_count = 0
	overall_neutral_count = 0
	overall_positive_count = 0
	overall_negative_strength = 0
	overall_positive_strength = 0

	# c_score contains 7 different sentiment scores for each country
	# and will append this information for each day (3 times)
	c_score = {}
	c_score['Canada'] = []
	c_score['England'] = []
	c_score['America'] = []
	c_score['Spain'] = []
	c_score['France'] = []
	c_score['Germany'] = []
	c_score['Ireland'] = []

	# initialize three dictionaries to store sentiment scores by day
	time_sample_1 ={'Ireland': 0, 
			'Canada': 0, 
                        'America': 0, 
                        'Germany': 0, 
                        'Spain': 0, 
                        'England': 0, 
                        'France': 0 }
	time_sample_2 = time_sample_1.copy()
	time_sample_3 = time_sample_1.copy()

	# initialize list to store all three time samples
	master_samples = []

	# for passing all tweet words to fdist
	tweet_words = []

	# access mongo collection
	posts = access_mongo_collection()
	# Clear any old Tweets from collection
	posts.remove({})

	# create dictionary of word-sentiment scores
	scores = create_lexicon()
	
	# create dictionary of booster-sentiment scores
	boosterwords = create_booster_lexicon()
	
	# create dictionary of emoticon-sentiment scores
	emoticons = create_emoticon_lexicon()

 	BASE_DIR = os.path.dirname(os.path.dirname(__file__))
	
	stopw = set(line.strip() for line in open(os.path.join(BASE_DIR, 'assets/Dictionaries/stopwords')))
	negation = set(line.strip() for line in open(os.path.join(BASE_DIR,'assets/Dictionaries/negation.txt')))
	eng = set(line.strip() for line in open(os.path.join(BASE_DIR,'assets/Dictionaries/english.txt')))
	
	search_list = []
	
	
	or_check = False

	terms = WordPunctTokenizer().tokenize(q)
	for word in terms:
		
		if word == 'or' or word == 'OR':
			or_check = True
		if word != 'and' and word != 'or' and word != 'AND' and word != 'OR' and word != '"':
			search_list.append(convert_unicode_to_string(word.lower()))

	for time in time_list:
		for country in country_dictionary:
			
			tweet_list = []
			query_in_text = True
			# Stores total sentiment-counts (must be reset)
			positive_sentiment_total = 0
			positive_sentiment_count = 0
			negative_sentiment_total = 0
			neutral_sentiment_count = 0
			negative_sentiment_count = 0	

			# Tweepy query for collecting tweets
			searched_tweets = tweepy_search(q,"en",time[0],time[0] + timedelta(days=1),country_dictionary[country],2)

			
			# make tweets lowercase, filter out names and stopwords, update relevant global values and
			# return a summary of each tweet
			for tweet in searched_tweets:
				temp_tweet = WordPunctTokenizer().tokenize(tweet.text)	
				for word in temp_tweet:
					tweet_list.append(convert_unicode_to_string(word).encode('ascii','ignore'))
				tweet_list_lower = [i.lower() for i in tweet_list]
				tweet_words += tweet_list_lower		
				for search_term in search_list:
					if search_term not in tweet_list_lower and or_check == False:
						
						query_in_text = False
						break
					elif or_check == True:
						if search_term in tweet_list_lower:
							
							query_in_text = True
							break
						else:
							query_in_text = False
						
				
				if query_in_text:
					tot = send_processed_tweet_to_db(posts, country, tweet, stopw, negation, boosterwords, scores, emoticons,eng,q,search_list)
				else:
					continue
				if tot < 0:
					negative_sentiment_count += 1
					negative_sentiment_total += tot
				elif tot > 0:
					positive_sentiment_count += 1
					positive_sentiment_total += tot
				elif tot == 0:
					neutral_sentiment_count += 1

			# Append new Country data for new day 		
			c_score[country].append(
					       [[positive_sentiment_total + negative_sentiment_total],
					       [negative_sentiment_total],
					       [positive_sentiment_total],
					       [neutral_sentiment_count],
					       [positive_sentiment_count],
					       [negative_sentiment_count],
					       [negative_sentiment_count + positive_sentiment_count + neutral_sentiment_count ]])
			
			# Accrue overall values for all three days 	
			overall_negative_strength += negative_sentiment_total
			overall_positive_strength += positive_sentiment_total
			overall_negative_count += negative_sentiment_count
			overall_positive_count += positive_sentiment_count
			overall_neutral_count += neutral_sentiment_count
	
	fdist1 = FreqDist(tweet_words)
	vocab = fdist1.keys()

	tweet_words_dic = {}
	for word in vocab:
	    if word not in stopw and word in scores and word not in search_list:
		tweet_words_dic[word] = fdist1[word]

	punctuation = ['.',',','<','/',';',"'",'[',']','`','>','<','?',':','co','rt',
		      '|','`','~','!','@','%','^','&','*','(',')','-','_','+','http','://','https','']
	context_words_dic = {}
	for word in vocab:
	    if word not in stopw and word not in scores and word not in search_list and word not in punctuation and squeeze(word) not in punctuation and word not in 'ru#"' and len(word) > 1:
		context_words_dic[word] = fdist1[word]
	

	# To get total scores just by country (and not also by day) we must add the data together from the three days.
	for country in c_score:
		for i in range(0,7):
			c_score[country][0][i] = c_score[country][0][i][0] + c_score[country][1][i][0] + c_score[country][2][i][0]

	# retrieve tweet summaries from MongoDB (MOngo wasn't actually necassy here, but it's educational)
	cursor = posts.find()

	# divide the tweet sentiment scores into three samples based on day
	for i in cursor:
		c = str(i['country'])
		if i['created_at'].date() == time_list[0][0]:		
			time_sample_1[c] += i['sentiment'] 
		elif i['created_at'].date() == time_list[1][0]:	
			time_sample_2[c] += i['sentiment'] 
		elif i['created_at'].date() == time_list[2][0]:
			time_sample_3[c] += i['sentiment'] 
       	
	# find AVERAGE scores for each country-day combination 
	# based on the number of tweets retrieved in each case 	
	for i in time_sample_1:
		d1 =  c_score[i][0][6] - (c_score[i][1][6][0] + c_score[i][2][6][0])
		if d1 != 0 and time_sample_1[i] != 0:
			print i
			print str('This ') + str(time_sample_1[i]) + str(' divided by ') + str(d1)
			print float(time_sample_1[i] / d1)
			print '.............'
			time_sample_1[i] = float(time_sample_1[i] / d1)
		else:
			print i
			print str('This       ') + str(time_sample_1[i]) + str(' divided by ') + str(d1)
			time_sample_1[i] = 0.0

	for i in time_sample_2:
		if c_score[i][1][6][0] != 0 and time_sample_2[i] != 0:
			print i
			print str('This ') + str(time_sample_2[i]) + str(' divided by ') + str(c_score[i][1][6][0])
			print float(time_sample_2[i] / (c_score[i][1][6][0]))
			print '.............'
			time_sample_2[i] = float(time_sample_2[i] / (c_score[i][1][6][0]))
		else:
			print i
			print str('This        ') + str(time_sample_2[i]) + str(' divided by ') + str(c_score[i][1][6][0])
			time_sample_2[i] = 0.0

	for i in time_sample_3:
		if c_score[i][2][6][0] != 0 and time_sample_3[i] != 0:
			print i
			print str('This ') + str(time_sample_3[i]) + str(' divided by ') + str(c_score[i][2][6][0])
			print float(time_sample_3[i] / (c_score[i][2][6][0]))
			print '.............'
			time_sample_3[i] = float(time_sample_3[i] / (c_score[i][2][6][0]))
		else:
			print i
			print str('This       ') + str(time_sample_3[i]) + str(' divided by ') + str(c_score[i][2][6][0])
			time_sample_3[i] = 0.0
		

	# Collect the four main data structures and return one composite structure

	master_samples = [[time_sample_1],[time_sample_2],[time_sample_3]]
	
	
	data_count = {'negative_sentiment_count': overall_negative_count, 
		      'positive_sentiment_count': overall_positive_count, 
                      'neutral_sentiment_count': overall_neutral_count
                     }

	data_strength = {'negative_sentiment_total': (overall_negative_strength * -1),
                         'positive_sentiment_total': overall_positive_strength
                        }
	
	data_list = [[data_count],[data_strength],[c_score],[master_samples],[tweet_words_dic],[context_words_dic]]	
			
	return data_list

#--------------------------------------------------------------------------------#
def connect():
	
	url =  'mongodb://kevin:6841734aa@ds027489.mongolab.com:27489/twitter'
	try:
	    conn=pymongo.MongoClient(url)
	    print "Connected successfully!!!"
	except pymongo.errors.ConnectionFailure, e:
	   print "Could not connect to MongoDB: %s" % e 

	return conn

#--------------------------------------------------------------------------------#

def create_lexicon():
	scores = {}
	BASE_DIR = os.path.dirname(os.path.dirname(__file__))
	with open(os.path.join(BASE_DIR, 'assets/Dictionaries/super.txt')) as f:
		for line in f:
	       		(key, val) = line.split('\t')
	       		scores[key] = int(val)
	return scores

#--------------------------------------------------------------------------------#

def create_booster_lexicon():
	boosterwords = {}
	BASE_DIR = os.path.dirname(os.path.dirname(__file__))
	with open(os.path.join(BASE_DIR, 'assets/Dictionaries/boosterwords.txt')) as f:
		for line in f:
	       		(key, val) = line.split('\t')
	       		boosterwords[key] = int(val)
	return boosterwords

#--------------------------------------------------------------------------------#

def create_emoticon_lexicon():
	scores = {}
	BASE_DIR = os.path.dirname(os.path.dirname(__file__))
	with open(os.path.join(BASE_DIR, 'assets/Dictionaries/emoticons.txt')) as f:
		for line in f:
	       		(key, val) = line.split('\t')
	       		scores[key] = int(val)
	return scores

#--------------------------------------------------------------------------------#
def send_message(request):
	subject = request.POST.get('topic', '')
	message = request.POST.get('message', '')
	from_email = request.POST.get('email', '')

	if subject and message and from_email:
	        try:
			send_mail(subject, message, from_email, ['kevinmcinerney8@gmail.com'])
		except BadHeaderError:
    			return HttpResponse('Invalid header found.')
		return HttpResponseRedirect('/thankyou')
	else:
		return render_to_response('contactus.html', {'form': ContactForm()})

#--------------------------------------------------------------------------------#
def create_dictData(data):
	dictData=[[ 'Sentiment', 'Polarity'],['Negative', data[0][0]['negative_sentiment_count'] ],
					 ['Objective', data[0][0]['neutral_sentiment_count'] ],
					 ['Positive', data[0][0]['positive_sentiment_count'] ] ]
	return dictData

#--------------------------------------------------------------------------------#
def create_dictData2(data):
	dictData2=[[ 'Sentiment', 'Strength'],['Negative', data[1][0]['negative_sentiment_total'] ],
					  ['Positive', data[1][0]['positive_sentiment_total'] ] ]
	return dictData2

#--------------------------------------------------------------------------------#
def create_dictData3(data):
	dictData3=[['City','Sentiment'],	[ 'Ireland', data[2][0]['Ireland'][0][0] ],	
					[ 'United Kingdom', data[2][0]['England'][0][0] ],	
					[ 'America', data[2][0]['America'][0][0] ],
					[ 'France', data[2][0]['France'][0][0]  ], 
					[ 'Germany', data[2][0]['Germany'][0][0] ],
					[ 'Canada', data[2][0]['Canada'][0][0]  ], 
					[ 'Spain', data[2][0]['Spain'][0][0]  ] ]
	return dictData3

#--------------------------------------------------------------------------------#
def create_dictData4(data):
	dictData4=[	[  data[2][0]['Ireland'][0] ],
			[  data[2][0]['Spain'  ][0] ],
			[  data[2][0]['Germany'][0] ],
			[  data[2][0]['America'][0] ],
			[  data[2][0]['England'][0] ],
			[  data[2][0]['Canada'][0] ],
			[  data[2][0]['France'][0] ] ]
	return dictData4

#--------------------------------------------------------------------------------#
def create_dictData5(data):

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
	return dictData5

#--------------------------------------------------------------------------------#

def create_dictData6(data):
    count = 1
    dictData6 = []
    sorted_dic = iter(sorted(data[4][0].iteritems(), key=operator.itemgetter(1), reverse=True)[:50])
    dictData6.append(['Sentiment Words', 'Freq'])
    for item in sorted_dic:
        dictData6.append([item[0], item[1]])
        count += 1
    return dictData6

#--------------------------------------------------------------------------------#

def create_dictData7(data):
    count = 1
    dictData7 = []
    sorted_dic = iter(sorted(data[5][0].iteritems(), key=operator.itemgetter(1), reverse=True)[:50])
    dictData7.append(['Contextual Words', 'Freq'])
    for item in sorted_dic:
        dictData7.append([item[0], item[1]])
        count += 1
    return dictData7

#--------------------------------------------------------------------------------#
def tweepy_search(q,lang,since,until,country,max_tweets):

	# Twitter Authorization codes
	ckey = "UJpisXUidLEdjEMVQhNOw"
	csecret = "VoBehORY0X1NhNe1QaaUSiak2rqAQpV5Hiz7N4QueeY"
	atoken = "93476811-dCDo7Kic1RcRoVub33p2pMycnflvrj5qyegq682yB"
	asecret = "prwsP2dSD6UqlC2Pmaer0Vt5EyJTInGgOClOqT00c"

	auth = tweepy.OAuthHandler(ckey, csecret)
	auth.set_access_token(atoken, asecret)

	# initialize tweepy authorization and key search parameters
	api = tweepy.API(auth)
	
	searched_tweets = [status for status in tweepy.Cursor(api.search, 
							      q=q, 
							      lang=lang,
							      since=since,
							      until=until,
							      geocode=country, 
							      ).items(max_tweets)]
	return searched_tweets

#--------------------------------------------------------------------------------#
def access_mongo_collection():
	# Connection to MongoLab via pymongo
	conn = connect()

	#Define MongoDB database
	db = conn.twitter

	# Define MongoDB collection 
	posts = db.tweemo_twitterstream

	return posts

#--------------------------------------------------------------------------------#
def send_processed_tweet_to_db(posts,country, tweet, stopw, negation, boosterwords, scores, emoticons, eng,q,search_list):

	# initialize sentiment score
	tot = 0

	# Stores matched sentiment words from tweets (must be reset)
	matches = []
	emoticon_matches = []
	hash_words = []
	negation_matches = []
	exclamation_matches = []
	boost_matches = []
	consecutive_matches = []
	squeezed_matches = []
	all_caps_matches = []
	hash_matches = []
	tweet_list = []
	slang_abbrev = expand_slang()

	if tweet.text:
		temp_tweet = WordPunctTokenizer().tokenize(tweet.text)
		for i in temp_tweet:
			tweet_list.append(convert_unicode_to_string(i))	
		#print tweet_list
		hashtags = hashtag_finder(tweet.text)
		if len(hashtags) > 0:
			hash_words = get_hashtag_words(hashtags,scores,slang_abbrev,eng)
			hash_matches = hash_words
		emo_dict = emoticon_score(tweet.text,emoticons)
		emoticon_matches = [i for i in emo_dict]
		tot = sum([emo_dict[i] for i in emo_dict])
		words = replace_abbrevs(tweet.text)
		words += hash_words
		consecutive_sentiment_checker = [0 for x in range(0,len(words))]
		booster_sentiment_checker = [0 for x in range(0,len(words))]
		negation_checker = create_negation_vector(words,negation)
		num = 0
		w_score = 0
		ws_score = 0
		for i in range(0,len(words)):
			if i > 0:
				num = 1
			w = convert_unicode_to_string(words[i].lower())
			ws = convert_unicode_to_string(squeeze(w))
			all_caps = is_all_caps(words[i])
			if w in boosterwords:
				booster_sentiment_checker[i] = boosterwords[w]
			elif ws in boosterwords:
				booster_sentiment_checker[i] = boosterwords[ws]
			if w not in stopw and negation_checker[(i-num)] != 1:
				if  w in scores:
					w_score = scores[w]
					tot += w_score
					word_combo = (str(w) + str(': ') + str(w_score) + str('   '))
					matches.append(word_combo)
					consecutive_sentiment_checker[i] = w_score
					if i >= 1 and consecutive_sentiment_checker[i-1] > 0:
						consecutive_matches.append(w)
						tot += 1
					elif i >= 1 and consecutive_sentiment_checker[i-1] < 0:
						consecutive_matches.append(w)
						tot -= 1
					if i >= 1 and booster_sentiment_checker[i-1] != 0:
						boost_matches.append(w)
						if w_score > 0:
							tot += booster_sentiment_checker[i-1]
						else:
							tot -= booster_sentiment_checker[i-1]
					if all_caps == True:
						all_caps_matches.append(w)
						if w_score > 0:
							tot += 1
						elif w_score < 0:
							tot -= 1	
				elif ws in scores:
					squeezed_matches.append(ws)
					ws_score = scores[ws]
					if ws_score > 0:
						tot += ws_score + 1
					elif ws_score < 0:
						tot += ws_score - 1
					word_combo = (str(ws) + str(': ') + str(ws_score) + str('   '))
					matches.append(word_combo)
					consecutive_sentiment_checker[i] = ws_score
					if i >= 1 and consecutive_sentiment_checker[i-1] > 0:
						tot += 1
					elif i >= 1 and consecutive_sentiment_checker[i-1] < 0:
						tot -= 1
					if i >= 1 and booster_sentiment_checker[i-1] != 0:
						boost_matches.append(ws)
						if ws_score > 0:
							tot += booster_sentiment_checker[i-1]
						else:
							tot -= booster_sentiment_checker[i-1]
					if all_caps == True:
						all_caps_matches.append(ws)
						if ws_score > 0:
							tot += 1
						elif ws_score < 0:
							tot -= 1
		
			if i < len(words) and '!' in words[i]:
				tot = exclamation_boost(consecutive_sentiment_checker,w_score,i,tot,sum([x=='!' for x in words])) 
				for i in reversed(range(0,i+1)):
    					if consecutive_sentiment_checker[i] != 0:
						exclamation_matches.append(convert_unicode_to_string(words[i]))
						break
		
			if w in scores and negation_checker[(i-num)] == 1:
				negation_matches.append(w)#=============================
			elif ws in scores and negation_checker[(i-num)] == 1:
				negation_matches.append(ws)
	
		data = { 'text': [convert_unicode_to_string(x).encode('ascii', 'ignore') for x in tweet_list], 
			 'created_at': tweet.created_at, 
			 'retweet_count': tweet.retweet_count, 
			 'sentiment': tot, 
			 'country': convert_unicode_to_string(str(country)), 
			 'matches': [convert_unicode_to_string(x).encode('ascii', 'ignore') for x in matches],
			 'emoticons': [convert_unicode_to_string(x).encode('ascii', 'ignore') for x in emoticon_matches],
			 'hashtags': [convert_unicode_to_string(x).encode('ascii', 'ignore') for x in hash_matches],
			 'negated_words': [convert_unicode_to_string(x).encode('ascii', 'ignore') for x in negation_matches],
			 'exclamated_words': [convert_unicode_to_string(x).encode('ascii', 'ignore') for x in exclamation_matches],
			 'boosted': [convert_unicode_to_string(x).encode('ascii', 'ignore') for x in boost_matches],
			 'consecutive_words': [convert_unicode_to_string(x).encode('ascii', 'ignore') for x in consecutive_matches],
			 'repeated_letter_words':[convert_unicode_to_string(x).encode('ascii', 'ignore') for x in squeezed_matches],
			 'capitalized_words': [convert_unicode_to_string(x).encode('ascii', 'ignore') for x in all_caps_matches],
			 'search_list': [convert_unicode_to_string(x).encode('ascii', 'ignore') for x in search_list]
			}

		#print data

		# insert tweet data to MongoDB
		posts.insert(data)
	return tot



#--------------------------------------------------------------------------------#
def squeeze(string):
    word = string
    n = 1
    for l in range(0,len(string)-n):
        while(word[l] == word[(l+1)]):
            word = str(" ")+word[0:l] + word[(l+1):]
            n += 1
    return word.strip(' ')

#--------------------------------------------------------------------------------#

def expand_slang():
    d = {}
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    with open(os.path.join(BASE_DIR, 'assets/Dictionaries/slang.txt')) as f:
        for line in f:
            s = ''
            (a,b) = line.split('\t')
            b = WordPunctTokenizer().tokenize(b)
            for i in range(0,len(b)):
                s += str(b[i]) + str(' ')
            d[a] = s
    return d

#--------------------------------------------------------------------------------#
def replace_abbrevs(tweet):
    
    tweet = WordPunctTokenizer().tokenize(tweet)
    slang_abbrev = expand_slang()
    
    new_tweet = tweet
    replacement = []
    for i in range(0,len(tweet)):
        dif = abs(len(tweet) - len(new_tweet))
	
        word = convert_unicode_to_string(tweet[i].lower())
	
        all_caps = is_all_caps(tweet[i])
	if word == '#' and i < (len(tweet)-1):
		new_tweet[(i+1)] = '_hashtag_'
	if i > 0 and tweet[(i-1)] == 'http':
		new_tweet[i] = '_url_'
	
        if word in slang_abbrev:
            if all_caps:
                replacement = map(lambda x: x.upper(), slang_abbrev[word].split(' '))
            else:
                replacement = slang_abbrev[word].split(' ')
            new_tweet = new_tweet[0:(i+dif)] + replacement + new_tweet[((i+dif)+1):]
    return new_tweet

#--------------------------------------------------------------------------------#
def is_all_caps(word):
	return word.isupper()

#--------------------------------------------------------------------------------#
def emoticon_score(tweet, emoticons):
	d = {}
	for emo in tweet.split():
		es = squeeze(emo)
		if emo in emoticons:
			d[emo] = emoticons[emo]
		elif es in emoticons:
			d[es] = emoticons[es]
	return d

#--------------------------------------------------------------------------------#
def create_negation_vector(tweet,negation):
	vector = [0 for x in range(0,len(tweet))]
	for i in range(0,len(tweet)):
		if tweet[i].lower() == 't':
			if tweet[(i-2)].lower() in negation:
				vector[i] = 1
		elif tweet[i] in negation:
			vector[i] = 1
	return vector

#--------------------------------------------------------------------------------#
def exclamation_boost(vector,w_score,index,tot,exclam_num):
	for i in vector[0:index][::-1]:
		if i != 0 and w_score > 0:
			
			tot += (1 * exclam_num)
			break
		elif i != 0 and w_score < 0:
			
			tot -= (1 * exclam_num)
			break
	return tot

#--------------------------------------------------------------------------------#
def hashtag_finder(words):
	l = []
	words = words.split()
	for word in words:
		if word[0] == '#':
		    l.append(word[1:])
	return l

#--------------------------------------------------------------------------------#
def get_hashtag_words(hashtags,scores,slang_abbrev,eng):
    extracted_words = []
    exclude = []
    between_words = []
    end_words = []
    #print '......'
    for hashtag in hashtags:
	#print str('Evaluate this hashtag: ') + str(convert_unicode_to_string(hashtag))
        hashtag = convert_unicode_to_string(hashtag)
        if hashtag[0:].lower() not in scores and hashtag[0:].lower() in eng:
	    #print str(hashtag[0:].lower()) + str(' is a whole word, but not a sentiment word ')
            continue
        elif hashtag[0:].lower() in scores:
	    #print str(hashtag[0:].lower()) + str(' is a whole sentiment word ')
            extracted_words.append(hashtag[0:].lower())
	    extracted_words.append('_stop_hashtags_getting_consecutive_boost')
	    #print str('proof of whole extracted word: ') + str(extracted_words)
            continue
        word_count = 0
        remainder_list = []
        remainder = hashtag
        for x in range(0,len(hashtag)+1):
            for y in range(x,len(hashtag)+1):
                if hashtag[x:y].lower() in scores:
		    #print str('Sentiment Word Detected: ') + str(convert_unicode_to_string(hashtag[x:y]).lower())
		    #print str('Front gap: ') + str(hashtag[0:x].lower()) + str(' is ') + str(validate_hashtag_gap(hashtag[0:x].lower(),eng))
		    #print str('End gap: ') + str(hashtag[y:].lower()) + str(' is ') + str(validate_hashtag_gap(hashtag[y:].lower(),eng))
                    if validate_hashtag_gap(hashtag[0:x].lower(),eng) == False:
                        continue
                    if validate_hashtag_gap(hashtag[y:].lower(),eng) == False:
                        continue
                    idx = y
                    for k in xrange(1,len(hashtag)):
                        if hashtag[x:y+k].lower() in scores:
                            idx = y + k
                    extracted_word = hashtag[x:idx]
		    #print str('===========> Successful ID: ') + str(convert_unicode_to_string(extracted_word))
                    word_count += 1
                    exclude += [i for i in range(x,idx)]
                    remainder = [hashtag[i] for i in range(1,len(hashtag)) if i not in exclude]
                    if word_count > 1:
                        between_words = ([hashtag[i] for i in range(1,y) if i not in exclude])
                        if validate_hashtag_gap(between_words,eng) == False:
                            continue
                    extracted_words.append(extracted_word)
		    extracted_words.append('_stop_hashtags_getting_consecutive_boost') 
                    x = y
		    break
        remainder = ''.join(remainder)
        remainder_list.append(remainder)
        extracted_words += hashtag_expander(remainder_list,slang_abbrev,eng)
    return extracted_words
#--------------------------------------------------------------------------------#

def hashtag_expander(hashtags,slang_abbrev,eng):
	extracted_words = []
	idx = 0
	for hashtag in hashtags:
		for x in range(0,len(hashtag)+1):
			for y in range(0,len(hashtag)+1):
				if str(hashtag[x:y].lower()) in slang_abbrev:
					if validate_hashtag_gap(hashtag[0:x].lower(),eng) == False:
						continue
					if validate_hashtag_gap(hashtag[y:].lower(),eng) == False:
						continue
					idx = y
					for k in xrange(1,len(hashtag)):
						if hashtag[x:y+k].lower() in slang_abbrev:
							idx = y + k
					extracted_word = convert_unicode_to_string(hashtag[x:idx])
					if is_all_caps(str(hashtag[x:idx])) == True:
						extracted_words = (map(lambda x: x.upper(), slang_abbrev[extracted_word.lower()]))
					else:
						extracted_words = (map(lambda x: x, slang_abbrev[extracted_word.lower()]))
	
	return  extracted_words

#--------------------------------------------------------------------------------#
def validate_hashtag_gap(gap,eng):
    gap = ''.join(gap)
    gap_checker = [0 for i in range(0,len(gap))]
    for x in range(0,len(gap)+1):
        for y in range(x,len(gap)+1):
            if str(gap[x:(y+1)]).lower() in eng:
		#print str('(Re)Compiling valid gaps:  ') + str(gap[x:(y+1)].lower())
                gap_checker[x:(y+1)] = [1 for i in range(0,len(gap_checker[x:(y+1)]))]
    for i in gap_checker:
        if i == 0:
            return False
    return True

#--------------------------------------------------------------------------------#

def convert_unicode_to_string(x):
    
    return "".join(i for i in x if ord(i)<128)
