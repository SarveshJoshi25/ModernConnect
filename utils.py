import pymongo
from config import mongodb_username, mongodb_password, mongodb_cluster


client = pymongo.MongoClient(f'mongodb+srv://{mongodb_username}:{mongodb_password}@{mongodb_cluster}/?retryWrites'
                             f'=true&w=majority')
db = client['modernconnect']
