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
from datetime import date, timedelta
from nltk import WordPunctTokenizer
from tweemo.models import ContactForm
from django import forms as forms
from django.forms.widgets import *
from django.core.mail import send_mail, BadHeaderError
import os
import string


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
    
    # call methods to parse data as required for graphs/analysis
    dictData = create_dictData(data)
    dictData2 = create_dictData2(data)
    dictData3 = create_dictData3(data)
    dictData4 = create_dictData4(data)
    dictData5 = create_dictData5(data)
   
 				    
    return render_to_response('results.html',
				{'here': TwitterStream.objects.all(),
				'djangodict': json.dumps(dictData),
				'djangodict2': json.dumps(dictData2), 
				'djangodict3': json.dumps(dictData3),
				'djangodict4': dictData4, 
				'djangodict5': json.dumps(dictData5),
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
	"""
	stopw = set(line.strip() for line in open('/home/kevin/django-kevin/bin/b_twitter/assets/Dictionaries/stopwords'))
	negation = set(line.strip() for line in open('/home/kevin/django-kevin/bin/b_twitter/assets/Dictionaries/negation.txt'))
	eng = set(line.strip() for line in open('/home/kevin/django-kevin/bin/b_twitter/assets/Dictionaries/english.txt'))"""

	stopw = set(line.strip() for line in open('/app/assets/Dictionaries/stopwords'))
	negation = set(line.strip() for line in open('/app/assets/Dictionaries/negation.txt'))
	eng = set(line.strip() for line in open('/app/assets/Dictionaries/english.txt'))


	for time in time_list:
		for country in country_dictionary:

			# Stores total sentiment-counts (must be reset)
			positive_sentiment_total = 0
			positive_sentiment_count = 0
			negative_sentiment_total = 0
			neutral_sentiment_count = 0
			negative_sentiment_count = 0	
			
			# Tweepy query for collecting tweets
			searched_tweets = tweepy_search(q,"en",time[0],time[0] + timedelta(days=1),country_dictionary[country],1)
			
			# make tweets lowercase, filter out names and stopwords, update relevant global values and
			# return a summary of each tweet
			for tweet in searched_tweets: 
				tot = send_processed_tweet_to_db(posts, country, tweet, stopw, negation, boosterwords, scores, emoticons,eng)
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

	# To get total scores just by country (and not also by day) we must add the data together from the three days.
	for country in c_score:
		for i in range(0,7):
			c_score[country][0][i] = c_score[country][0][i][0] + c_score[country][1][i][0] + c_score[country][2][i][0]

	# retrieve tweet summaries from MongoDB (MOngo wasn't actually necassy here, but it's educational)
	cursor = posts.find()

	# divide the tweet sentiment scores into three samples based on day
	for i in cursor:
		c = str(i['country'])
		if i['created_at'].date() == time_list[2][0]:		
			time_sample_1[c] += i['sentiment'] 
		elif i['created_at'].date() == time_list[1][0]:	
			time_sample_2[c] += i['sentiment'] 
		elif i['created_at'].date() == time_list[0][0]:
			time_sample_3[c] += i['sentiment'] 
       	
	# find AVERAGE scores for each country-day combination 
	# based on the number of tweets retrieved in each case 	
	for i in time_sample_1:
		d1 =  c_score[i][0][6] - (c_score[i][1][6][0] + c_score[i][2][6][0])
		if d1 != 0:
			time_sample_1[i] = float(time_sample_1[i] / d1)

	for i in time_sample_2:
		if c_score[i][1][6][0] != 0:
			time_sample_2[i] = float(time_sample_2[i] / (c_score[i][1][6][0]))

	for i in time_sample_3:
		if c_score[i][2][6][0] != 0:
			time_sample_3[i] = float(time_sample_3[i] / (c_score[i][2][6][0]))
		

	# Collect the four main data structures and return one composite structure

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
def send_processed_tweet_to_db(posts,country, tweet, stopw, negation, boosterwords, scores, emoticons, eng):

	# initialize sentiment score
	tot = 0

	# Stores matched sentiment words from tweets (must be reset)
	matches = []
	hash_words = []
	slang_abbrev = expand_slang()

	# three nltk corpi
	#stopw = set('/app/assets/Dictionaries/stopwords.txt')
	#m_names = set('/app/assets/Dictionaries/male.txt')
	#w_names = set('/app/assets/Dictionaries/female.txt')
	#m_names = set(line.strip() for line in open('/home/kevin/django-kevin/bin/b_twitter/assets/Dictionaries/male.txt'))
	#w_names = set(line.strip() for line in open('/home/kevin/django-kevin/bin/b_twitter/assets/Dictionaries/female.txt'))
	if tweet.text:
		negation_matches = []
		exclamation_matches = []
		boost_matches = []
		consecutive_matches = []
		squeezed_matches = []
		all_caps_matches = []
		hashtags = hashtag_finder(tweet.text)
		if len(hashtags) > 0:
			hash_words = get_hashtag_words(hashtags,scores,slang_abbrev,eng)
		emo_dict = emoticon_score(tweet.text,emoticons)
		matches += [i for i in emo_dict]
		tot += sum([emo_dict[i] for i in emo_dict])	
		words = replace_abbrevs(tweet.text)
		words += hash_words
		consecutive_sentiment_checker = [0 for x in range(0,len(words))]
		booster_sentiment_checker = [0 for x in range(0,len(words))]
		negation_checker = create_negation_vector(words,negation)
		num = 0
		w_score = 0
		ws_score = 0
		print words
		for i in range(0,len(words)):
			if i > 0:
				num = 1
			w = words[i].lower()
			ws = squeeze(w)
			all_caps = is_all_caps(words[i])
			if w in boosterwords:
				booster_sentiment_checker[i] = boosterwords[w]
			elif ws in boosterwords:
				booster_sentiment_checker[i] = boosterwords[ws]
			if w not in stopw and negation_checker[(i-num)] != 1:
				if  w in scores:
					w_score = scores[w]
					tot += w_score
					matches.append(w)
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
			
			elif ws not in stopw and negation_checker[(i-num)] != 1:	
				if ws in scores:
					squeezed_matches.append(ws)
					ws_score = scores[ws]
					tot += ws_score + 1
					matches.append(ws)
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
			if i < (len(words)-1) and squeeze(words[i]) == '!':
				tot = exclamation_boost(consecutive_sentiment_checker,w_score,i,tot)
				for i in reversed(range(0,index+1)):
    					if i != 0:
						exclamation_matches.append(squeeze(words[i])
			
			if w in scores and (negation_checker[(i-num)] == 1):
				negation_matches.append(w)
			elif ws in scores and (negation_checker[(i-num)] == 1):
				negation_matches.append(ws)
						
	data = { 'text': tweet.text, 
                 'created_at': tweet.created_at, 
                 'retweet_count': tweet.retweet_count, 
                 'sentiment': tot , 
                 'country': country, 
                 'matches': matches
		 'negated_words': negation_matches,
		 'exclamated_words': exclamation_matches,
		 'boosted': boost_matches,
		 'consecutive_words': consecutive_matches,
		 'repeated_letter_words':squeezed_matches,
		 'capitalized_words': all_caps_matches,
                }

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
#with open('/home/kevin/django-kevin/bin/b_twitter/assets/Dictionaries/slang.txt')as f:
def expand_slang():
    d = {}
    with open('/app/assets/Dictionaries/slang.txt')as f:
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
        word = tweet[i].lower()
        all_caps = is_all_caps(tweet[i])
        if word in slang_abbrev:
            if all_caps:
                replacement = map(lambda x: x.upper(), slang_abbrev[word].split(' '))
            else:
                replacement = slang_abbrev[word].split(' ')
            new_tweet = new_tweet[0:(i+dif)] + replacement + new_tweet[((i+dif)+1):]
	if word == '#' and i < (len(tweet)-1):
		tweet[(i+1)] = '_hashtag_'
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
def exclamation_boost(vector,w_score,index,tot):
	for i in vector[0:index][::-1]:
		if i != 0 and w_score > 0:
			tot += 1
			break
		elif i != 0 and w_score < 0:
			tot -= 1
			break
	return tot

#--------------------------------------------------------------------------------#
def hashtag_finder(words):
	l = []
	words = words.split()
	for word in words:
		if word[0] == '#':
		    l.append(word)
	return l

#--------------------------------------------------------------------------------#
def get_hashtag_words(hashtags,scores,slang_abbrev,eng):
    extracted_words = []
    exclude = []
    between_words = []
    end_words = []
    for hashtag in hashtags:
        hashtag = hashtag.encode('ascii','ignore').translate(None, string.punctuation)
        if hashtag[0:].lower() not in scores and hashtag[0:].lower() in eng:
            continue
        elif hashtag[0:].lower() in scores:
            extracted_words.append(hashtag[0:].lower())
            continue
        word_count = 0
        remainder_list = []
        remainder = hashtag
        for x in range(0,len(hashtag)+1):
            for y in range(x,len(hashtag)+1):
                if hashtag[x:y].lower() in scores:
                    if validate_hashtag_gap(hashtag[0:x].lower(),eng) == False:
                        continue
                    if validate_hashtag_gap(hashtag[y:].lower(),eng) == False:
                        continue
                    idx = y
                    for k in xrange(1,len(hashtag)):
                        if hashtag[x:y+k].lower() in scores:
                            idx = y + k
                    extracted_word = hashtag[x:idx]
                    word_count += 1
                    exclude += [i for i in range(x,idx)]
                    remainder = [hashtag[i] for i in range(1,len(hashtag)) if i not in exclude]
                    if word_count > 1:
                        between_words = ([hashtag[i] for i in range(1,y) if i not in exclude])
                        if validate_hashtag_gap(between_words,eng) == False:
                            continue
                    extracted_words.append(extracted_word)
                    x = y
		    break
        remainder = ''.join(remainder)
        remainder_list.append(remainder)
        extracted_words += hashtag_expander(remainder_list,slang_abbrev)
    return extracted_words
#--------------------------------------------------------------------------------#

def hashtag_expander(hashtags,slang_abbrev):
	extracted_words = []
	for hashtag in hashtags:
		for x in range(0,len(hashtag)+1):
			for y in range(0,len(hashtag)+1):
				if str(hashtag[x:y].lower()) in slang_abbrev:
					if is_all_caps(str(hashtag[x:y])) == True:
						extracted_words = (map(lambda x: x.upper(), slang_abbrev[str(hashtag[x:y].lower())]))
					else:
						extracted_words = (map(lambda x: x, slang_abbrev[str(hashtag[x:y].lower())]))
	return  extracted_words

#--------------------------------------------------------------------------------#
def validate_hashtag_gap(gap,eng):
    gap = ''.join(gap)
    gap_checker = [0 for i in range(0,len(gap))]
    for x in range(0,len(gap)+1):
        for y in range(x,len(gap)+1):
            if str(gap[x:(y+1)]).lower() in eng:
                gap_checker[x:(y+1)] = [1 for i in range(0,len(gap_checker[x:(y+1)]))]
    for i in gap_checker:
        if i == 0:
            return False
    return True
