import threading
import random
from utils import db
import datetime
from django.core.mail import send_mail
from django.http import JsonResponse
from rest_framework import status
import bcrypt


def encrypt_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


class sendVerificationEmail(threading.Thread):
    def __init__(self, user):
        self.user = user
        threading.Thread.__init__(self)

    def run(self):
        try:
            print("Sending an verification email to {0} at {1}".format(self.user['email_address'],
                                                                       datetime.datetime.now()))
            collection_name = db['email_validation']
            otp = str(random.randrange(100000, 999999))
            collection_name.delete_many({
                "user_id": self.user['user_id']
            })
            collection_name.insert_one(
                {
                    "user_id": self.user['user_id'],
                    "otp": encrypt_password(str(otp)),
                    "timestamp": datetime.datetime.now()
                }
            )
            send_mail('Verification for ModernConnect.', """Hello {0}, 
            \nThis Email is to inform you about registration of this email address on ModernConnect. 
            \nIgnore this message if you've not initiated this process. \nIf you've initiated this process, 
            Please consider {1} as your One Time Password to verify this account! """.format(
                self.user['full_name'], otp),
                      'sjfrommodernconnect@gmail.com', [self.user['email_address']], fail_silently=False)
            print("Email sent successfully. at {0}".format(datetime.datetime.now()))
        except Exception as e:
            return JsonResponse({"error": "An error has occurred during sending verification email. "},
                                status=status.HTTP_406_NOT_ACCEPTABLE)
