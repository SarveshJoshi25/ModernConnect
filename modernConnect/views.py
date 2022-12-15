import random
from django.core.mail import send_mail
from django.http import JsonResponse
from rest_framework import status
import uuid
from .exceptions import InvalidUsernameLength, InvalidUsernameInvalidLetters, InvalidUsernameUnderscore, \
    InvalidUsernameAlreadyExists, InvalidGender, InvalidAccountType, InvalidEmailHost, InvalidFullName, \
    InvalidEmailAlreadyExists, InvalidLengthPassword, InvalidUserContactLengthNot10, InvalidUserContactNotDigit
import string
import bcrypt
from utils import db
import datetime
from email_validator import validate_email, EmailNotValidError
from .models import UserAccount
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
import jwt
from config import jwt_secret


def encrypt_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def validate_user_password(password: str):
    if len(password) < 5:
        raise InvalidLengthPassword
    return True


def validate_user_contact_number(contact_number: str):
    if not contact_number.isdigit():
        raise InvalidUserContactNotDigit
    if not len(contact_number) == 10:
        raise InvalidUserContactLengthNot10


def validate_user_full_name(user_full_name: str):
    for y in [x.isalpha() is True for x in user_full_name.split(' ')]:
        if y is False:
            raise InvalidFullName


def validate_user(user_object):
    try:
        validate_user_name(user_name=user_object['user_name'])
        validate_user_full_name(user_full_name=user_object['full_name'])
        if not (user_object['gender'] == 'M' or user_object['gender'] == 'F' or user_object['gender'] == 'O'):
            raise InvalidGender

        if not (user_object['account_type'] == 'Student' or user_object['account_type'] == 'Alumni' or
                user_object['account_type'] == 'Admin'):
            raise InvalidAccountType
        validate_user_email(user_object)
        validate_user_password(user_object['password'])
        validate_user_contact_number(user_object['contact_number'])

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
    if len(list(collection_name.find({'user_email': str(user['email_address'])}))):
        raise InvalidEmailAlreadyExists
    return True


def generate_jwt_token(data):
    return jwt.encode({"user_id": data["user_id"], "account_type": data["account_type"]}, jwt_secret, algorithm="HS256")


# View calls below.
@api_view(["POST"])
@permission_classes([AllowAny])
def UserSignup(request):
    try:
        received_data = request.data
        user_name = (str(received_data.get('user_name')).lower()).strip()
        gender = (str(received_data.get('gender'))).strip()
        full_name = (str(received_data.get('full_name'))).strip()
        account_type = (str(received_data.get('account_type'))).strip()
        email_address = (str(received_data.get('email_address'))).strip()
        contact_number = (str(received_data.get('contact_number'))).strip()
        about_yourself = (str(received_data.get('about_yourself'))).strip()
        password = (str(received_data.get('password'))).strip()
        user_id = str(uuid.uuid4())

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
        account = UserAccount.serialize(UserAccount(), data=user_object)

        account.save()
        send_verification_email(user_object)
        jsonResponse = JsonResponse({"Response": "Account created successfully! "})
        jsonResponse.set_cookie(key="JWT_TOKEN", value=generate_jwt_token(user_object))
        return jsonResponse


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

    except InvalidAccountType:
        return JsonResponse({"error": "The account type can be only Student or Alumni."},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

    except InvalidEmailHost:
        return JsonResponse({"error": "Please use your college email address for registration, "
                                      "and not the private email address."}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except InvalidFullName:
        return JsonResponse({"error": "The full name length is invalid."}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except InvalidLengthPassword:
        return JsonResponse({"error": "The Password length is Invalid."},
                            status=status.HTTP_406_NOT_ACCEPTABLE)
    except InvalidUserContactNotDigit:
        return JsonResponse({"error": "Invalid Contact number."},
                            status=status.HTTP_406_NOT_ACCEPTABLE)
    except InvalidUserContactLengthNot10:
        return JsonResponse({"error": "Invalid Contact number."},
                            status=status.HTTP_406_NOT_ACCEPTABLE)
