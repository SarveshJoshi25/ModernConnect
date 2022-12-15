from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

mongodb_username = os.getenv("MONGODB_USERNAME")
mongodb_password = os.getenv("MONGODB_PASSWORD")
mongodb_cluster = os.getenv("MONGODB_CLUSTER_NAME")
secret_key = os.getenv("SECRET_KEY")
email_host_address = os.getenv("EMAIL_HOST_ADDRESS")
email_host_address_password = os.getenv("EMAIL_HOST_ADDRESS_PASSWORD")
jwt_secret = os.getenv("JWT_SECRET")
