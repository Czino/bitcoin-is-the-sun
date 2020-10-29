import tweepy
import config as cf

# sinceId = int(args['since'])
auth = tweepy.OAuthHandler(cf.credentials['consumer_key'], cf.credentials['consumer_secret'])
auth.set_access_token(cf.credentials['access_token'], cf.credentials['access_token_secret'])

api = tweepy.API(auth)

originalTweet = api.get_status('1320092333157867521', include_entities=True, tweet_mode='extended')

print(originalTweet)