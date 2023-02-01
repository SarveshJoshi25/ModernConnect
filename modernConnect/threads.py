import threading
import random
from utils import db
import datetime
from django.core.mail import send_mail, EmailMessage
from django.http import JsonResponse
from rest_framework import status
from django.utils.html import strip_tags
from django.template.loader import render_to_string, get_template
import bcrypt
from django.template import Context


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
            message = get_template("mail-template.html").render({
                "user_name": self.user['full_name'],
                "otp": otp
            })

            mail = EmailMessage(
                subject="Verification for ModernConnect.",
                body=message,
                from_email="sjfrommodernconnect@gmail.com",
                to=[self.user['email_address']],
                reply_to=["sjfrommodernconnect@gmail.com"],
            )
            mail.content_subtype = "html"
            mail.send()
            print("Email sent successfully. at {0}".format(datetime.datetime.now()))
        except Exception as e:
            return JsonResponse({"error": "An error has occurred during sending verification email. "},
                                status=status.HTTP_406_NOT_ACCEPTABLE)


