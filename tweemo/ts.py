import tweepy
from tweepy import API
import pymongo
import sys

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

#lookup ='the'
api = tweepy.API(auth)

search = []


query = str(sys.argv[1])
max_tweets = 10
searched_tweets = [status for status in tweepy.Cursor(api.search, q=query).items(max_tweets)]

#tweets = api.search(geocode='39.833193,-94.862794,5mi')
for tweet in searched_tweets:
	search.append(tweet)
	
    
posts.remove({})
# loop through search and insert dictionary into mongoDB
for tweet in search:
    # Empty dictionary for storing tweet related data
    data ={}
    data['text'] = tweet.text
    # Insert process
    posts.insert(data)
    print data.items()




