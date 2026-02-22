import os
import tweepy

auth = tweepy.OAuth1UserHandler(
    os.getenv("X_API_KEY"),
    os.getenv("X_API_SECRET"),
    os.getenv("X_ACCESS_TOKEN"),
    os.getenv("X_ACCESS_SECRET"),
)

api = tweepy.API(auth)

api.update_status("Teste de integração Giro Desportivo 🚀")
print("Postado com sucesso")
