from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

mongodb_username = os.getenv("MONGODB_USERNAME")
mongodb_password = os.getenv("MONGODB_PASSWORD")
mongodb_cluster = os.getenv("MONGODB_CLUSTER_NAME")
secret_key = os.getenv("SECRET_KEY")
