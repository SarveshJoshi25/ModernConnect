import datetime

import pymongo

from .threads import sendVerificationEmail
from django.http import JsonResponse
from rest_framework import status
import uuid
from .exceptions import InvalidUsernameLength, InvalidUsernameInvalidLetters, InvalidUsernameUnderscore, \
    InvalidUsernameAlreadyExists, InvalidGender, InvalidAccountType, InvalidEmailHost, InvalidFullName, \
    InvalidEmailAlreadyExists, InvalidLengthPassword, InvalidUserContactLengthNot10, InvalidUserContactNotDigit, \
    InvalidInstituteName, InvalidLocation, InvalidEnrollmentYear, InvalidCompletion, InvalidEnrollmentCompletionPair, \
    InvalidDegree, InvalidStream
import string
import bcrypt
from utils import db
from email_validator import validate_email, EmailNotValidError
from .models import UserAccount
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
import jwt
from config import jwt_secret
from rest_framework.authtoken.models import Token
from django.shortcuts import get_object_or_404


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
    sendVerificationEmail(user).start()


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


def generate_jwt_token(user_id, account_type):
    return jwt.encode({"user_id": user_id, "account_type": account_type}, jwt_secret, algorithm="HS256")


def decode_jwt_token(received_token: str):
    return jwt.decode(received_token, jwt_secret, algorithms="HS256")


def get_user_account_type(received_token: str) -> str:
    decoded_token = decode_jwt_token(received_token)
    return str(decoded_token.get("account_type"))


def set_degree(degree_id: int):
    this_degree = db["degrees"].find({"degree_id": int(degree_id)}, {"_id": 0, "degree": 1})
    return list(this_degree)[0]['degree']


def verify_degree(degree_id: int) -> bool:
    return db["degrees"].find({"degree_id": degree_id}).count() > 0


def verify_education(list_of_education, user_id):
    for education in list_of_education:
        if len(str(education.get("institute")).strip()) == 0:
            raise InvalidInstituteName

        if len(str(education.get("location")).strip()) == 0:
            raise InvalidLocation

        if not (str(education.get("enrollment_year")).strip()).isdigit():
            raise InvalidEnrollmentYear

        if not (str(education.get("completion_year")).strip()).isdigit():
            raise InvalidCompletion

        if int(education.get("enrollment_year")) > int(education.get("completion_year")):
            raise InvalidEnrollmentCompletionPair

        if not verify_degree(int(education.get("degree"))):
            raise InvalidDegree

        if len(str(education.get("stream")).strip()) == 0:
            raise InvalidStream
        education["user_id"] = user_id
        education["degree"] = set_degree(education.get("degree"))
        education["education_id"] = str(uuid.uuid4())
    return list_of_education


# View calls below.
@api_view(["POST"])
@permission_classes([AllowAny])
def UserSignup(request):
    """

    How to create a user using API Call?

    Requirements: None.
    Request type: POST

    1. Request body for Student =
        Request body: {
           {
            "user_name": "sarvesh_joshi",
            "password": "FakePassword",
            "email_address": "my_email@moderncoe.edu.in",
            "full_name": "Sarvesh Joshi",
            "account_type": "Student",
            "gender": "M",
            "contact_number": "1234567890",
            "about_yourself": "Backend Developer"
        }
        :returns Success message, and an OTP is sent on Email for verification.

    2. Request body for Student =
        Request body: {
            {
            "user_name": "sarvesh_joshi",
            "password": "FakePassword",
            "email_address": "my_email@gmail.com",
            "full_name": "Sarvesh Joshi",
            "account_type": "Student",
            "gender": "M",
            "contact_number": "1234567890",
            "about_yourself": "Backend Developer"
        }
    :returns Success message, and an OTP is sent on Email for verification,
             Two cookies - 1. JWT Token: Keep this set in cookie.
                           2. Authentication Token: Set "Token + <sent token>"  in Authentication header.

    :exception: KeyErrors, ValidationErrors -> A 406 Error Response will be raised.

    ON SUCCESS -> redirect user to OTP verification page, and send a request verify_email API.

    """

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
        account.is_active = True
        account.last_login = datetime.datetime.now()
        account.save()
        send_verification_email(user_object)

        token = Token.objects.create(user=account)

        jsonResponse = JsonResponse({"Response": "Account created successfully! "})
        jsonResponse.set_cookie(key="JWT_TOKEN", value=generate_jwt_token(user_object['user_id'],
                                                                          user_object['account_type']))
        jsonResponse.set_cookie(key="AUTHENTICATION_TOKEN", value=token)
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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def verifyEmailAddress(request):
    # Requirements: Header - Authorization: Token <token sent by server either after signup or login>
    # Cookie - JWT_TOKEN : set by server as a cookie, don't remove it.
    try:
        received_token = request.COOKIES.get("JWT_TOKEN")
        authenticate_this = decode_jwt_token(received_token)

        received_data = request.data
        user_entered_otp = str(received_data.get('otp')).strip()

        user_collection = db['user_accounts']
        collection_name = db['email_validation']
        requesting_user = user_collection.find_one({'user_id': authenticate_this.get("user_id")})
        if requesting_user['user_if_email_verified']:
            return JsonResponse({"response": "Your email is already verified!"}, status=status.HTTP_200_OK)

        if not len(list(collection_name.find({'user_id': authenticate_this.get("user_id")}))):
            return JsonResponse({"error": "Can't find your request for OTP at database. Please re-request for "
                                          "Verification Email."}, status=status.HTTP_406_NOT_ACCEPTABLE)
        if not bcrypt.checkpw(password=user_entered_otp.encode("utf-8"), hashed_password=(
                collection_name.find_one({"user_id": authenticate_this.get("user_id")})['otp']).encode("utf-8")):
            return JsonResponse({"error": "Incorrect OTP."}, status=status.HTTP_406_NOT_ACCEPTABLE)

        collection_name.delete_one({"user_id": authenticate_this.get("user_id")})

        user_collection.find_one_and_update(
            filter={
                'user_id': str(authenticate_this.get("user_id"))
            },
            update=
            {
                "$set": {
                    'user_if_email_verified': True
                }
            })

        return JsonResponse({"response": "Your Email has been verified. Now you can access all features for the Users"},
                            status=status.HTTP_200_OK)

    except KeyError:
        return JsonResponse({"error": "Required Data was not found!"}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["POST"])
@permission_classes([AllowAny])
def UserLogin(request):
    try:
        received_data = request.data

        user_name = (str(received_data.get('user_name')).lower()).strip()
        password = (str(received_data.get('password'))).strip()

        user = get_object_or_404(UserAccount, user_name=user_name)

        if user.check_password(password):
            token = Token.objects.update_or_create(user=user)[0]
            # token = Token.objects.create(user=user)
            user_collection = db['user_accounts']
            user_collection.find_one_and_update(
                filter={
                    'user_name': user_name
                },
                update=
                {
                    "$set": {
                        'is_active': True,
                        'last_login': datetime.datetime.now()
                    }
                })

            # user.is_active = True
            # user.last_login = datetime.datetime.now()
            jsonResponse = JsonResponse({"Response": "Logged In Successfully! "})
            jsonResponse.set_cookie(key="JWT_TOKEN", value=generate_jwt_token(user_id=user.user_id,
                                                                              account_type=user.user_account_type))
            jsonResponse.set_cookie(key="AUTHENTICATION_TOKEN", value=token)
            return jsonResponse
        else:
            return JsonResponse({"response": "Username and Password didn't match."},
                                status=status.HTTP_406_NOT_ACCEPTABLE)


    except KeyError:
        return JsonResponse({"error": "Required fields not found."}, status=status.HTTP_406_NOT_ACCEPTABLE)

    except UserAccount.DoesNotExist:
        return JsonResponse({"error": "The Account with given Username doesn't exists."},
                            status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_degree_types(request):
    degree_collection = db["degrees"]
    degrees = degree_collection.find({}, {"degree_id": 1, "degree": 1, "_id": 0})
    degrees = degrees.sort("degree_id", pymongo.ASCENDING)
    return JsonResponse({"degrees": list(degrees)}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def UserAddEducationalDetails(request):
    """


{
    "educational_data": [{
    "institute": "Modern College of Engineering, Pune",
    "location": "Pune, Maharashtra",
    "enrollment_year": "2021",
    "completion_year": "2024",
    "degree": "2",
    "stream": "Information Technology",
    "grade": "8.7"
    }]
}
    :param request:
    :return:
    """
    try:
        received_token = request.COOKIES.get("JWT_TOKEN")
        received_data = request.data
        list_of_education = list(received_data.get("educational_data"))
        decoded_token = decode_jwt_token(received_token)
        list_of_education = verify_education(list_of_education, decoded_token["user_id"])
        db["education_details"].insert_many(list_of_education)
        return JsonResponse({"success": "Education added successfully."}, status=status.HTTP_200_OK)
    except jwt.exceptions.DecodeError:
        return JsonResponse({"error": "User is not logged in."}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except InvalidInstituteName:
        return JsonResponse({"error", "Invalid Institute Name."}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except InvalidLocation:
        return JsonResponse({"error", "Invalid Location."}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except InvalidEnrollmentYear:
        return JsonResponse({"error": "Invalid Enrollment Year"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except InvalidCompletion:
        return JsonResponse({"error": "Invalid Completion Year"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except InvalidEnrollmentCompletionPair:
        return JsonResponse({"error": "Enrollment Year can't be greater than Completion Year."},
                            status=status.HTTP_406_NOT_ACCEPTABLE)
    except InvalidDegree:
        return JsonResponse({"error": "Invalid Degree ID."}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except InvalidStream:
        return JsonResponse({"error": "Invalid Stream"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except KeyError:
        return JsonResponse({"error": "Required Data was not found!"}, status=status.HTTP_406_NOT_ACCEPTABLE)

