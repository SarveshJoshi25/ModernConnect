import random
from django.core.mail import send_mail
from django.http import JsonResponse
from rest_framework import viewsets, status, generics, permissions
from rest_framework.views import APIView
import uuid
from .exceptions import InvalidUsernameLength, InvalidUsernameInvalidLetters, InvalidUsernameUnderscore, \
    InvalidUsernameAlreadyExists, InvalidGender, InvalidAccountType, InvalidEmailHost, InvalidFullName, \
    InvalidEmailAlreadyExists, InvalidLengthPassword
import string
import bcrypt
from utils import client, db
import datetime
from email_validator import validate_email, EmailNotValidError


def encrypt_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def validate_user_password(password: str):
    if len(password) < 5:
        raise InvalidLengthPassword
    return True


def validate_user(user_object):
    try:
        validate_user_name(user_name=user_object['user_name'])
        if not len(user_object['full_name']) > 5:
            raise InvalidFullName
        if not (user_object['gender'] == 'M' or user_object['gender'] == 'F' or user_object['gender'] == 'O'):
            raise InvalidGender

        if not (user_object['account_type'] == 'Student' or user_object['account_type'] == 'Alumni' or
                user_object['account_type'] == 'Admin'):
            raise InvalidAccountType
        validate_user_email(user_object)
        validate_user_password(user_object['password'])

    except InvalidUsernameLength:
        raise InvalidUsernameLength
    except InvalidUsernameInvalidLetters:
        raise InvalidUsernameInvalidLetters
    except InvalidUsernameUnderscore:
        raise InvalidUsernameUnderscore
    except InvalidGender:
        raise InvalidGender
    except InvalidAccountType:
        raise InvalidAccountType
    except InvalidEmailAlreadyExists:
        raise InvalidEmailAlreadyExists


def send_verification_email(user):
    collection_name = db['alumni_email_validation']
    otp = str(random.randrange(100000, 999999))
    collection_name.delete_many({
        "user_id": user['user_id']
    })
    collection_name.insert_one(
        {
            "user_id": user['user_id'],
            "otp": encrypt_password(str(otp)),
            "timestamp": datetime.datetime.now()
        }
    )
    send_mail('Verification for ModernConnect.', """Hello {0}, 
    \nThis Email is to inform you about registration of this email address on ModernConnect. 
    \nIgnore this message if you've not initiated this process. \nIf you've initiated this process, Please consider {1} as your One Time Password to verify this account! """.format(
        user['full_name'], otp),
              'sjfrommodernconnect@gmail.com', [user['email_address']], fail_silently=False)


def validate_user_name(user_name: str):
    match = string.ascii_letters + string.digits + '_'
    if not 20 >= len(user_name.lower()) >= 5:
        raise InvalidUsernameLength
    if not all([x in match for x in user_name]):
        raise InvalidUsernameInvalidLetters
    if user_name.lower()[0] == '_' or user_name.lower()[-1] == '_':
        raise InvalidUsernameUnderscore
    collection_name = db["user_accounts"]
    if len(list(collection_name.find({'user_name': user_name}))):
        raise InvalidUsernameAlreadyExists
    return True


def validate_user_email(user):
    if not validate_email(user['email_address'], check_deliverability=True, globally_deliverable=True):
        raise EmailNotValidError
    if user['account_type'] == 'Student':
        email, domain = str(user['email_address']).split('@')
        if domain != "moderncoe.edu.in":
            raise InvalidEmailHost
    collection_name = db["user_accounts"]
    if len(list(collection_name.find({'email_address': str(user['email_address'])}))):
        raise InvalidEmailAlreadyExists
    return True


class UserSignup(APIView):
    def post(self, request) -> JsonResponse:
        try:
            received_data = self.request.data

            user_name = str(received_data.get('user_name')).lower()
            gender = str(received_data.get('gender'))
            full_name = str(received_data.get('full_name'))
            account_type = str(received_data.get('account_type'))
            email_address = str(received_data.get('email_address'))
            contact_number = str(received_data.get('contact_number'))
            about_yourself = str(received_data.get('about_yourself'))
            password = str(received_data.get('password'))
            user_id = str(uuid.uuid4())
            collection_name = db["user_accounts"]

            if account_type == 'Student':
                user_object = {
                    'user_id': user_id,
                    'user_name': user_name,
                    'password': password,
                    'full_name': full_name,
                    'gender': gender,
                    'account_type': account_type,
                    'email_address': email_address,
                    'contact_number': contact_number,
                    'about_yourself': about_yourself,
                    'if_verified_email': False,
                }
            else:
                user_object = {
                    'user_id': user_id,
                    'user_name': user_name,
                    'password': password,
                    'full_name': full_name,
                    'gender': gender,
                    'account_type': account_type,
                    'email_address': email_address,
                    'contact_number': contact_number,
                    'about_yourself': about_yourself,
                    'if_verified_email': False,
                    'if_access_given': False
                }

            validate_user(user_object)
            user_object['password'] = encrypt_password(user_object['password'])

            if user_object['account_type'] == 'Student':
                collection_name.insert_one(user_object)
                send_verification_email(user_object)
            if user_object['account_type'] == 'Alumni':
                collection_name.insert_one(user_object)
                send_verification_email(user_object)
                collection_name = db["pending_alumni_accounts"]
                collection_name.insert_one(user_object)
                send_verification_email(user_object)

            # Add constraints

            return JsonResponse({'Response': "Success"}, status=status.HTTP_200_OK)

        except KeyError:
            return JsonResponse({"error": "Required Data was not found!"}, status=status.HTTP_406_NOT_ACCEPTABLE)
        except InvalidUsernameLength:
            return JsonResponse({"error": "The length of username should be between 5 to 20"},
                                status=status.HTTP_406_NOT_ACCEPTABLE)
        except InvalidUsernameInvalidLetters:
            return JsonResponse({"error": "Username can only contain alphanumeric and underscores."},
                                status=status.HTTP_406_NOT_ACCEPTABLE)

        except InvalidUsernameUnderscore:
            return JsonResponse({"error": "Username can't start or end with underscore."},
                                status=status.HTTP_406_NOT_ACCEPTABLE)

        except InvalidUsernameAlreadyExists:
            return JsonResponse({"error": "Username already taken by someone else."},
                                status=status.HTTP_406_NOT_ACCEPTABLE)

        except InvalidGender:
            return JsonResponse({"error": "Gender can be either M/F or O."},
                                status=status.HTTP_406_NOT_ACCEPTABLE)

        except InvalidEmailAlreadyExists:
            return JsonResponse({"error": "Email already registered with someone else."},
                                status=status.HTTP_406_NOT_ACCEPTABLE)
