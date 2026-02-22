import os
import tweepy

client = tweepy.Client(
    consumer_key=os.getenv("X_API_KEY"),
    consumer_secret=os.getenv("X_API_SECRET"),
    access_token=os.getenv("X_ACCESS_TOKEN"),
    access_token_secret=os.getenv("X_ACCESS_SECRET"),
)

response = client.create_tweet(
    text="Teste de integração Giro Desportivo 🚀"
)

print("Tweet publicado:", response.data)
