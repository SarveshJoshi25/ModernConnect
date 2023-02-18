import datetime

import pymongo

from .threads import sendVerificationEmail
from django.http import JsonResponse
from rest_framework import status
import uuid
import string
import bcrypt
from utils import db
from email_validator import validate_email
import validators
from .models import UserAccount, WorkExperience, EducationalExperience, ProjectDetails, ContextPost, Skills, \
    SocialLinks, ProfileSkills, Posts, Polls
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
import jwt
from config import jwt_secret
from rest_framework.authtoken.models import Token
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404


def encrypt_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def validate_user_password(password: str):
    if len(password) < 5:
        raise Exception("error: Password Length must be more than 5.")
    return True


def validate_user_contact_number(contact_number: str):
    if not contact_number.isdigit():
        raise Exception("error: Invalid Phone number.")
    if not len(contact_number) == 10:
        raise Exception("error: Phone Number must be of length 10.")


def validate_user_full_name(user_full_name: str):
    for y in [x.isalpha() is True for x in user_full_name.split(' ')]:
        if y is False:
            raise Exception("error: Invalid Name of User.")


def verify_edit_users(user_data):
    try:
        validate_user_full_name(user_data["full_name"])
        if not (user_data['gender'] == 'M' or user_data['gender'] == 'F' or user_data['gender'] == 'O'):
            raise Exception("error: User's Gender must be either M, F or O.")

        if not (user_data['account_type'] == 'Student' or user_data['account_type'] == 'Alumni' or
                user_data['account_type'] == 'Admin'):
            raise Exception("error: Account Type must be either Student, Alumni or Admin.")
        validate_user_contact_number(user_data['contact_number'])
    except Exception as e:
        raise e


def verify_links(links, user_id):
    list_of_verified_links = []
    for each_link in links:
        link = SocialLinks()
        if len(each_link["social_link_title"]) <= 0:
            raise Exception("error: Invalid Social Link Title.")
        link.social_link_title = each_link["social_link_title"]

        if not validators.url(str(each_link['social_link'])):
            raise Exception("error: Invalid Social Link.")
        link.social_link = each_link['social_link']

        link.social_link_author = UserAccount.objects.get(user_id=user_id)
        link.social_link_id = str(uuid.uuid4())
        list_of_verified_links.append(link)
    return list_of_verified_links


def validate_user(user_object):
    try:
        validate_user_name(user_name=user_object['user_name'])
        validate_user_full_name(user_full_name=user_object['full_name'])
        if not (user_object['gender'] == 'M' or user_object['gender'] == 'F' or user_object['gender'] == 'O'):
            raise Exception("error: User's Gender must be either M, F or O.")

        if not (user_object['account_type'] == 'Student' or user_object['account_type'] == 'Alumni' or
                user_object['account_type'] == 'Admin'):
            raise Exception("error: Account Type must be either Student, Alumni or Admin.")
        validate_user_email(user_object)
        validate_user_password(user_object['password'])
        validate_user_contact_number(user_object['contact_number'])
    except Exception as e:
        raise e


def send_verification_email(user):
    sendVerificationEmail(user).start()


def validate_user_name(user_name: str):
    match = string.ascii_letters + string.digits + '_'
    if not 20 >= len(user_name.lower()) >= 5:
        raise Exception("error: Username's Length must be more than or equal to 5 and less than or equal to 20.")
    if not all([x in match for x in user_name]):
        raise Exception("error: Invalid Username (can only contain letters, digits and underscores)")
    if user_name.lower()[0] == '_' or user_name.lower()[-1] == '_':
        raise Exception("error: Invalid Username (Underscores can't exist at front or rear ends of username) ")
    collection_name = db["user_accounts"]
    if len(list(collection_name.find({'user_name': user_name, "user_if_email_verified": True}))):
        raise Exception("error: Invalid Username (Username already registered) ")
    return True


def validate_user_email(user):
    if not validate_email(user['email_address'], check_deliverability=True, globally_deliverable=True):
        raise Exception("error: Invalid Email Address")
    if user['account_type'] == 'Student':
        email, domain = str(user['email_address']).split('@')
        if domain != "moderncoe.edu.in":
            raise Exception("error: Invalid Email (Students need to use Email Address provided by College.)")
    collection_name = db["user_accounts"]
    if len(list(collection_name.find({'user_email': str(user['email_address']), "user_if_email_verified": True}))):
        raise Exception("error: Invalid Email Address (Email Address already registered) ")
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


def validate_post(received_data, post_author):
    post_id = str(uuid.uuid4())

    if len(str(received_data["post_content"])) <= 0:
        raise Exception("Invalid Post Content.")

    context = ContextPost.objects.get(context_id=received_data["context_id"])
    post = Posts(post_id=post_id, post_author=UserAccount.objects.get(user_id=post_author), post_context=context,
                 post_content=str(received_data["post_content"]))

    if context.context_name == "#collaborate":
        skills_str = str(received_data['skills'])
        skill_list = skills_str.split(",")
        if not (0 < len(skills_str) <= 3):
            raise Exception("Invalid Skills")
        for each in skill_list:
            if Skills.objects.filter(skill_id=int(each)).count() == 0:
                raise Exception("Invalid Skill.")
        post.skills = str(received_data["skills"])

    post.save()

    if received_data["poll"] and context.context_name == "#ask":
        poll_options = received_data["poll_options"]
        if not (2 <= len(poll_options) <= 4):
            raise Exception("Invalid Poll Options. (2 to 4 required)")
        for each_option in poll_options:
            Polls(post_id=Posts.objects.get(post_id=post_id), poll_option_id=str(uuid.uuid4()),
                  poll_option_text=each_option).save()


#     post_id = models.CharField(verbose_name="post_id", primary_key=True, default=str(uuid.uuid4()), editable=False,
#                                max_length=60)
#     post_author = models.ForeignKey("UserAccount", verbose_name="post_author", on_delete=models.CASCADE)
#     posted_on = models.DateTimeField(verbose_name="posted_on", default=datetime.datetime.now(), editable=False)
#     post_content = models.CharField(verbose_name="post_content", max_length=480, null=False)
#     post_context = models.ForeignKey("ContextPost", verbose_name="post_context", on_delete=models.CASCADE)
#     skills = models.CharField(validators=[validate_comma_separated_integer_list], max_length=120)


def verify_education(list_of_education, user_id):
    verified_education = []
    for education in list_of_education:
        if len(str(education.get("institute")).strip()) == 0:
            raise Exception("error: Invalid Institute (Institute Name can't be None.) ")

        if len(str(education.get("location")).strip()) == 0:
            raise Exception("error: Invalid Location (Location can't be None.) ")

        if not (str(education.get("enrollment_year")).strip()).isdigit():
            raise Exception("error: Invalid Enrollment Year (Enrollment Year should only contain digits.) ")

        if not (str(education.get("completion_year")).strip()).isdigit():
            raise Exception("error: Invalid Completion Year (Completion Year should only contain digits.) ")

        if int(education.get("enrollment_year")) > int(education.get("completion_year")):
            raise Exception("error: Invalid Completion Year and Enrollment Year Pair.")

        if not verify_degree(int(education.get("degree"))):
            raise Exception("error: Invalid Degree.")

        if len(str(education.get("stream")).strip()) == 0:
            raise Exception("error: Invalid Stream (Stream can't be None.)")

        verified_education.append(EducationalExperience(
            institute=str(education.get("institute")).strip(),
            location=str(education.get("location")).strip(),
            enrollment_year=int(str(education.get("enrollment_year")).strip()),
            completion_year=int(str(education.get("completion_year")).strip()),
            degree=set_degree(education.get("degree")),
            user_id=user_id,
            stream=str(education.get("stream")).strip(),
            education_id=str(uuid.uuid4()),
            grade=education.get("grade")
        ))
    return verified_education


def verify_work(list_of_work, user_id):
    list_of_verified_work = []
    for each_work_experience in list_of_work:
        work = WorkExperience()
        if len(each_work_experience["work_designation"]) <= 0:
            raise Exception("error: Invalid Completion Year and Enrollment Year Pair.")
        work.work_designation = each_work_experience["work_designation"]

        if len(each_work_experience["work_organization"]) <= 0:
            raise Exception("error: Invalid Work Organization.")
        work.work_organization = each_work_experience["work_organization"]

        if not (str(each_work_experience["is_current_employer"]).title() == 'False' or
                str(each_work_experience["is_current_employer"]).title() == 'True'):
            raise Exception("error: Invalid Current Employer (should be either True or False) ")
        work.is_current_employer = each_work_experience["is_current_employer"]

        each_work_experience["first_day_at_work"] = datetime.datetime.strptime(
            each_work_experience["first_day_at_work"], "%Y-%m-%d").date()

        if each_work_experience["first_day_at_work"] > datetime.date.today():
            raise Exception("error: Invalid First Day at work (Future dates are not allowed)")
        work.first_day_at_work = each_work_experience["first_day_at_work"]

        if each_work_experience["is_current_employer"] == "False":
            each_work_experience["last_day_at_work"] = datetime.datetime.strptime(
                each_work_experience["last_day_at_work"], "%Y-%m-%d").date()

            if each_work_experience["first_day_at_work"] > each_work_experience["last_day_at_work"]:
                raise Exception("error: Invalid First Day at Work and First Day at Work Pair.")
            work.last_day_at_work = each_work_experience["last_day_at_work"]
            work_experience = (work.last_day_at_work.year - work.first_day_at_work.year) * 12 + \
                              work.last_day_at_work.month - work.first_day_at_work.month
            work.work_experience = "{0} Years, {1} Months".format(int(work_experience / 12), work_experience % 12)
        work.user_id = user_id
        work.work_description = each_work_experience["work_description"]
        work.work_experience_id = str(uuid.uuid4())
        list_of_verified_work.append(work)
    return list_of_verified_work


def verify_projects(list_of_projects, user_id):
    list_of_verified_projects = []
    for each_project in list_of_projects:
        project = ProjectDetails()
        if len(each_project["project_title"]) <= 0:
            raise Exception("error: Invalid Project Title (Project title can't be null).")
        project.project_title = each_project["project_title"]

        if len(each_project["project_headline"]) <= 0:
            raise Exception("error: Invalid Project Headline (Project headline can't be null).")
        project.project_headline = each_project["project_headline"]

        if each_project['project_link']:
            if not validators.url(str(each_project['project_link'])):
                raise Exception("error: Invalid Project Link.")
            project.project_link = each_project['project_link']

        if each_project['project_description']:
            if len(each_project['project_description']) <= 0:
                raise Exception("error: Invalid Project Description (Project Description can't be null).")
            project.project_description = each_project['project_description']

        project.user_id = user_id
        project.project_id = str(uuid.uuid4())
        list_of_verified_projects.append(project)
    return list_of_verified_projects


@api_view(["GET"])
@permission_classes([AllowAny])
def IsAwake(request):
    """
        Checks if Server is Awake, sends a 200 response every time.
    """
    return JsonResponse({"message": "The server is awake!"}, status=status.HTTP_200_OK)


# View calls below.
@api_view(["POST"])
@permission_classes([AllowAny])
def UserSignup(request):
    """
    How to create a user using API Call?

    Requirements: None.
    Request type: POST

    1. Request body for Student =
        Request body:
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

        returns Success message, and an OTP is sent on Email for verification.

    2. Request body for Student =
        Request body:
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
    except Exception as e:
        return JsonResponse({"error": e.args}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(['POST'])
@permission_classes([AllowAny])
def editUserDetails(request):
    try:
        received_token = request.COOKIES.get("JWT_TOKEN")
        authenticate_this = decode_jwt_token(received_token)

        requesting_user = UserAccount.objects.filter(user_id=authenticate_this['user_id'])

        received_data = request.data
        verify_edit_users(received_data)

        # "full_name": "Sarvesh Joshi",
        #     "account_type": "Student",
        #     "gender": "M",
        #     "contact_number": "9373496540",
        #     "about_yourself": "Backend Developer, and developer of this platform."

        requesting_user = requesting_user.update(user_full_name=received_data['full_name'],
                                                 user_account_type=received_data['account_type'],
                                                 user_gender=received_data['gender'],
                                                 user_contact=received_data['contact_number'],
                                                 user_bio=received_data['about_yourself'])

        return JsonResponse({"message": "Updated data successfully."})
    except KeyError:
        return JsonResponse({"error": "Required Data was not found!"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except Exception as e:
        return JsonResponse({"error": e.args}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def userLogout(request):
    try:
        """
        requirements: JWT Token in Cookies, and Authorization header.
        :param request: None.
        :return: Status code 200.
        """
        db["authtoken_token"].delete_one(
            filter={"user_id": decode_jwt_token(request.COOKIES.get("JWT_TOKEN"))["user_id"]})
        return JsonResponse({"success": "Logged Out."})
    except jwt.exceptions.DecodeError:
        return JsonResponse({"error": "User is not Logged-In."}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def verifyEmailAddress(request):
    """
    requirements: Authorization Header, JWT_TOKEN
    Sample Input:
        {
            "otp": "132465"
        }
    :return: Status 200 on successful verification, OR status 406 with error message on generation of errors.
    """
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
    except Exception as e:
        return JsonResponse({"error": e.args}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except jwt.exceptions.DecodeError:
        return JsonResponse({"error": "User is not Logged-In."}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["POST"])
@permission_classes([AllowAny])
def UserLogin(request):
    """
    Sample Input:
        {
            "user_name": "Your_Username",
            "password": "raw_password"
        }

    :return: Status 200 with JWT_Token set as cookie, and Authorization Token set in cookie. Send "Token" +
                Authorization token as header "Authorization". (Example: if set cookie is 12312313,
                header will be "Token 13212313".
    """
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
    except Exception as e:
        return JsonResponse({"error": e.args}, status=status.HTTP_406_NOT_ACCEPTABLE)


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
    requirements: The User must be logged in.

    Sample Input:
        {
            "educational_data":
            [
                {
                    "institute": "Modern College of Engineering, Pune",
                    "location": "Pune, Maharashtra",
                    "enrollment_year": "2021",
                    "completion_year": "2024",
                    "degree": "2",
                    "stream": "Information Technology",
                    "grade": "8.7"
                },
                {
                    "institute": "Government Polytechnic, Pune",
                    "location": "Pune, Maharashtra",
                    "enrollment_year": "2018",
                    "completion_year": "2021",
                    "degree": "3",
                    "stream": "Computer Engineering",
                    "grade": "93.8"
                }
            ]
        }

    :return: Status 200 on success, or Status 406 on errors.
    """
    try:
        received_token = request.COOKIES.get("JWT_TOKEN")
        received_data = request.data
        list_of_education = list(received_data.get("educational_data"))
        decoded_token = decode_jwt_token(received_token)
        verified_education = verify_education(list_of_education, decoded_token["user_id"])
        for v in verified_education:
            v.save()
        return JsonResponse({"success": "Education added successfully."}, status=status.HTTP_200_OK)
    except jwt.exceptions.DecodeError:
        return JsonResponse({"error": "User is not logged in."}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except KeyError:
        return JsonResponse({"error": "Required Data was not found!"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except Exception as e:
        return JsonResponse({"error": e.args}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def getEducationalDetails(request):
    """
    requirement: User must be logged in.
    :return: Status 200 on success, OR Status 406 for errors.
    """
    try:
        received_token = request.COOKIES.get("JWT_TOKEN")
        decoded_token = decode_jwt_token(received_token)
        educational_details = EducationalExperience.objects.filter(user_id=decoded_token['user_id']).order_by(
            "enrollment_year").values()
        educational_details = list(educational_details)
        return JsonResponse({"educational_details": educational_details}, status=status.HTTP_200_OK)
    except jwt.exceptions.DecodeError:
        return JsonResponse({"error": "User is not logged in."}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except KeyError:
        return JsonResponse({"error": "Required Data was not found!"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except Exception as e:
        return JsonResponse({"error": e.args}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def editEducationalDetailsSeparate(request, education_id):
    """
    :requirements: The User must be logged in.
    :param: send educational id as a parameter.

    Sample Input:
        {
            "institute": "Modern College of Engineering, Pune",
            "location": "Pune, Maharashtra",
            "enrollment_year": "2021",
            "completion_year": "2024",
            "degree": "2",
            "stream": "Information Technology",
            "grade": "8.7"
        }

    :return: Status 200 on success, or Status 406 on errors.

    """
    try:
        received_token = request.COOKIES.get("JWT_TOKEN")
        decoded_token = decode_jwt_token(received_token)
        fetched_details = EducationalExperience.objects.filter(user_id=decoded_token['user_id'],
                                                               education_id=education_id)
        if fetched_details.count() == 0:
            return JsonResponse({"error": "Invalid Educational ID."}, status=status.HTTP_406_NOT_ACCEPTABLE)
        received_data = request.data
        educational_list = [received_data]
        educational_list = verify_education(educational_list, decoded_token["user_id"])
        EducationalExperience.objects.filter(user_id=decoded_token['user_id'], education_id=education_id).delete()
        educational_list[0].save()
        return JsonResponse({"success": "Educational details are updated!"}, status=status.HTTP_200_OK)

    except KeyError:
        return JsonResponse({"error": "Required Data was not found!"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except jwt.exceptions.DecodeError:
        return JsonResponse({"error": "User is not logged in."}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except Exception as e:
        return JsonResponse({"error": e.args}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def deleteEducationalDetailsSeparate(request, education_id):
    """
    :requirements: User must be logged in, Send educational ID as parameters.

    :param request:
    :param education_id:

    :return:
    """
    try:
        received_token = request.COOKIES.get("JWT_TOKEN")
        decoded_token = decode_jwt_token(received_token)
        deleted_ = EducationalExperience.objects.filter(user_id=decoded_token['user_id'],
                                                        education_id=education_id).delete()
        if deleted_[0] == 0:
            return JsonResponse({"error": "Requested Educational Experience not found."},
                                status=status.HTTP_406_NOT_ACCEPTABLE)
        return JsonResponse({"success": "Educational Experience deleted successfully!"}, status=status.HTTP_200_OK)
    except KeyError:
        return JsonResponse({"error": "Required Data was not found!"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except jwt.exceptions.DecodeError:
        return JsonResponse({"error": "User is not logged in."}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except Exception as e:
        return JsonResponse({"error": e.args}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def UserAddWorkExperience(request):
    """
    :requirements: User must be logged in

    Sample Input:
        {
            "work_data":
            [
                {
                    "work_designation": "Backend Developer Intern",
                    "work_organization": "Rhythmflows Solutions Pvt. Ltd.",
                    "first_day_at_work": "01-08-2022",
                    "last_day_at_work": "01-11-2022",
                    "is_current_employer": "No",
                    "work_description": "Developed features for the company's Financial Reconciliation Software. The
                    day-to-day tasks include developing APIs using Python/Django to fetch and process data from PostgresSQL
                    databases and sending responses to the front-end using JSON and collaborating with Front-end developers
                    to develop full-stack features."
                }
            ]
        }

    :returns: A Status 200 on Success, and 406 on errors.

    """
    try:
        received_token = request.COOKIES.get("JWT_TOKEN")
        received_data = request.data
        list_of_work = list(received_data.get("work_data"))
        decoded_token = decode_jwt_token(received_token)
        list_of_verified_work = verify_work(list_of_work, decoded_token["user_id"])
        for verified_work in list_of_verified_work:
            verified_work.save()
        return JsonResponse({"success": "Work Experience added successfully."}, status=status.HTTP_200_OK)
    except ValidationError as v:
        print(v.message)
        return JsonResponse({"error": v.message}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except jwt.exceptions.DecodeError:
        return JsonResponse({"error": "User is not logged in."}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except AttributeError:
        return JsonResponse({"error": "Something went wrong!"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except KeyError:
        return JsonResponse({"error": "Required Data was not found!"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except Exception as e:
        return JsonResponse({"error": e.args}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def GetWorkDetails(request):
    """
    :requirements: User must be logged in.
    :param request:
    :return: A Status 200 on Success, and 406 on errors.
    """

    try:
        received_token = request.COOKIES.get("JWT_TOKEN")
        decoded_token = decode_jwt_token(received_token)
        work_details = WorkExperience.objects.filter(user_id=decoded_token['user_id']).order_by(
            'first_day_at_work').values()
        for each in work_details:
            if each['is_current_employer']:
                work_experience = (datetime.datetime.today().year - each['first_day_at_work'].year) * 12 + \
                                  datetime.datetime.today().month - each['first_day_at_work'].month
                each['work_experience'] = "{0} Years, {1} Months".format(int(work_experience / 12),
                                                                         work_experience % 12)
        return JsonResponse({"work_details": list(work_details)}, status=status.HTTP_200_OK)
    except jwt.exceptions.DecodeError:
        return JsonResponse({"error": "User is not Logged-In."}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except Exception as e:
        return JsonResponse({"error": e.args}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def editWorkDetailsSeparate(request, work_id):
    """
    :requirements: User must be logged in, send work_id as a parameter.

    Sample Input :
    {
        "work_designation": "Backend Developer Intern",
        "work_organization": "Rhythmflows Solutions Pvt. Ltd.",
        "first_day_at_work": "2022-08-01",
        "last_day_at_work": "2022-11-01",
        "is_current_employer": "False",
        "work_description": "Developed features for the company's Financial Reconciliation Software. The
        day-to-day tasks include developing APIs using Python/Django to fetch and process data from PostgresSQL
        databases and sending responses to the front-end using JSON and collaborating with Front-end developers
        to develop full-stack features."
    }

    :param request:
    :param work_id:
    :return: A 200 Status code, 406 for errors.
    """
    try:
        received_token = request.COOKIES.get("JWT_TOKEN")
        decoded_token = decode_jwt_token(received_token)
        fetched_details = WorkExperience.objects.filter(user_id=decoded_token['user_id'], work_experience_id=work_id)
        if fetched_details.count() == 0:
            return JsonResponse({"error": "Invalid Work ID."}, status=status.HTTP_406_NOT_ACCEPTABLE)
        received_data = request.data
        work_list = [received_data]
        work_list = verify_work(work_list, decoded_token["user_id"])
        WorkExperience.objects.filter(user_id=decoded_token['user_id'], work_experience_id=work_id).delete()
        work = work_list[0]
        work.work_experience_id = work_id
        work.save()
        return JsonResponse({"success": "Work Experience is updated!"}, status=status.HTTP_200_OK)
    except ValidationError as v:
        print(v.message)
        return JsonResponse({"error": v.message}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except jwt.exceptions.DecodeError:
        return JsonResponse({"error": "User is not logged in."}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except KeyError:
        return JsonResponse({"error": "Required Data was not found!"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except AttributeError:
        return JsonResponse({"error": "Something went wrong!"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except Exception as e:
        return JsonResponse({"error": e.args}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def deleteWorkDetails(request, work_id):
    """
        :requirements: User must be logged in, send work_id in parameters.
        :param work_id:
        :param request:
        :return: A Status 200 on Success, and 406 on errors.
    """
    try:
        received_token = request.COOKIES.get("JWT_TOKEN")
        decoded_token = decode_jwt_token(received_token)
        deleted_ = WorkExperience.objects.filter(user_id=decoded_token['user_id'], work_experience_id=work_id).delete()
        if deleted_[0] == 0:
            return JsonResponse({"error": "Requested Work Experience not found."},
                                status=status.HTTP_406_NOT_ACCEPTABLE)
        return JsonResponse({"success": "Work Experience deleted successfully!"}, status=status.HTTP_200_OK)
    except KeyError:
        return JsonResponse({"error": "Required Data was not found!"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except jwt.exceptions.DecodeError:
        return JsonResponse({"error": "User is not logged in."}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except Exception as e:
        return JsonResponse({"error": e.args}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def UserAddProjectExperience(request):
    """
    :requirements: User must be logged in

    Sample Input:
        {
            "projects":
            [
                {
                    "project_title": "ModernConnect",
                    "project_headline": "An exclusive platform for and from students of Modern College of Engineering",
                    "project_link": "https://www.github.com/SarveshJoshi25/ModernConnect",
                    "project_description": "Description!!!!"
                },
                {
                    "project_title": "ModernConnect",
                    "project_headline": "An exclusive platform for and from students of Modern College of Engineering",
                    "project_link": "https://www.github.com/SarveshJoshi25/ModernConnect",
                    "project_description": "Description!!!!"
                }
            ]
        }

    :returns: A Status 200 on Success, and 406 on errors.

    """
    try:
        received_token = request.COOKIES.get("JWT_TOKEN")
        received_data = request.data
        list_of_projects = list(received_data.get("projects"))
        decoded_token = decode_jwt_token(received_token)
        list_of_verified_projects = verify_projects(list_of_projects, decoded_token["user_id"])
        for verified_project in list_of_verified_projects:
            verified_project.save()
        return JsonResponse({"success": "Projects added successfully."}, status=status.HTTP_200_OK)
    except ValidationError as v:
        print(v.message)
        return JsonResponse({"error": v.message}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except jwt.exceptions.DecodeError:
        return JsonResponse({"error": "User is not logged in."}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except AttributeError:
        return JsonResponse({"error": "Something went wrong!"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except KeyError:
        return JsonResponse({"error": "Required Data was not found!"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except Exception as e:
        return JsonResponse({"error": e.args}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def GetProjectDetails(request):
    """
    :requirements: User must be logged in.
    :param request:
    :return: A Status 200 on Success, and 406 on errors.
    """

    try:
        received_token = request.COOKIES.get("JWT_TOKEN")
        decoded_token = decode_jwt_token(received_token)
        project_details = ProjectDetails.objects.filter(user_id=decoded_token['user_id']).values()
        return JsonResponse({"project_details": list(project_details)}, status=status.HTTP_200_OK)
    except jwt.exceptions.DecodeError:
        return JsonResponse({"error": "User is not Logged-In."}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except Exception as e:
        return JsonResponse({"error": e.args}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def editProjectDetailsSeparate(request, project_id):
    """
    :requirements: User must be logged in, send work_id as a parameter.

    Sample Input :
    {
        "project_title": "ModernConnect",
        "project_headline": "An exclusive platform for and from students of Modern College of Engineering",
        "project_link": "https://www.github.com/SarveshJoshi25/ModernConnect",
        "project_description": "Description!!!!"
    }

    :param request:
    :param project_id:
    :return: A 200 Status code, 406 for errors.
    """
    try:
        received_token = request.COOKIES.get("JWT_TOKEN")
        decoded_token = decode_jwt_token(received_token)
        fetched_details = ProjectDetails.objects.filter(user_id=decoded_token['user_id'], project_id=project_id)
        if fetched_details.count() == 0:
            return JsonResponse({"error": "Invalid Project ID."}, status=status.HTTP_406_NOT_ACCEPTABLE)
        received_data = request.data
        project_list = [received_data]
        project_list = verify_projects(project_list, decoded_token["user_id"])
        ProjectDetails.objects.filter(user_id=decoded_token['user_id'], project_id=project_id).delete()
        project = project_list[0]
        project.project_id = project_id
        project.save()
        return JsonResponse({"success": "Project Details is updated!"}, status=status.HTTP_200_OK)
    except ValidationError as v:
        print(v.message)
        return JsonResponse({"error": v.message}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except jwt.exceptions.DecodeError:
        return JsonResponse({"error": "User is not logged in."}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except KeyError:
        return JsonResponse({"error": "Required Data was not found!"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except AttributeError:
        return JsonResponse({"error": "Something went wrong!"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except Exception as e:
        return JsonResponse({"error": e.args}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def deleteProjectDetails(request, project_id):
    """
        :requirements: User must be logged in, send work_id in parameters.
        :param project_id:
        :param request:
        :return: A Status 200 on Success, and 406 on errors.
    """
    try:
        received_token = request.COOKIES.get("JWT_TOKEN")
        decoded_token = decode_jwt_token(received_token)
        deleted_ = ProjectDetails.objects.filter(user_id=decoded_token['user_id'], project_id=project_id).delete()
        if deleted_[0] == 0:
            return JsonResponse({"error": "Requested Project Details not found."},
                                status=status.HTTP_406_NOT_ACCEPTABLE)
        return JsonResponse({"success": "Project Details deleted successfully!"}, status=status.HTTP_200_OK)
    except KeyError:
        return JsonResponse({"error": "Required Data was not found!"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except jwt.exceptions.DecodeError:
        return JsonResponse({"error": "User is not logged in."}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except Exception as e:
        return JsonResponse({"error": e.args}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def UserAddSocialLink(request):
    """
    {
    "social_links":[
        {
            "social_link_title": "GitHub",
            "social_link": "https://www.github.com/SarveshJoshi25/"
        },
        {
            "social_link_title": "Linktree",
            "social_link": "https://linktr.ee/_sarveshjoshi"
        }
        ]
    }
    :param request:
    :return:
    """
    try:
        received_token = request.COOKIES.get("JWT_TOKEN")
        received_data = request.data
        list_of_links = list(received_data.get("social_links"))
        decoded_token = decode_jwt_token(received_token)
        list_of_verified_social_links = verify_links(list_of_links, decoded_token["user_id"])
        for verified_links in list_of_verified_social_links:
            verified_links.save()
        return JsonResponse({"success": "Social Links added successfully."}, status=status.HTTP_200_OK)
    except ValidationError as v:
        print(v.message)
        return JsonResponse({"error": v.message}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except jwt.exceptions.DecodeError:
        return JsonResponse({"error": "User is not logged in."}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except AttributeError:
        return JsonResponse({"error": "Something went wrong!"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except KeyError:
        return JsonResponse({"error": "Required Data was not found!"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except Exception as e:
        return JsonResponse({"error": e.args}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def GetSocialLink(request):
    try:
        received_token = request.COOKIES.get("JWT_TOKEN")
        decoded_token = decode_jwt_token(received_token)
        link_details = SocialLinks.objects.filter(social_link_author=decoded_token['user_id']).values()
        return JsonResponse({"social_links": list(link_details)}, status=status.HTTP_200_OK)
    except jwt.exceptions.DecodeError:
        return JsonResponse({"error": "User is not Logged-In."}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except Exception as e:
        return JsonResponse({"error": e.args}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def editSocialLink(request, social_link_id):
    try:
        received_token = request.COOKIES.get("JWT_TOKEN")
        decoded_token = decode_jwt_token(received_token)
        fetched_details = SocialLinks.objects.filter(social_link_author=decoded_token['user_id'],
                                                     social_link_id=social_link_id)
        if fetched_details.count() == 0:
            return JsonResponse({"error": "Invalid Social Link ID."}, status=status.HTTP_406_NOT_ACCEPTABLE)
        received_data = request.data

        social_link_list = [received_data]
        social_link_list = verify_links(social_link_list, decoded_token["user_id"])

        update_this = SocialLinks.objects.filter(social_link_author=decoded_token['user_id'],
                                                 social_link_id=social_link_id)
        update_this.update(social_link=social_link_list[0].social_link,
                           social_link_title=social_link_list[0].social_link_title)

        return JsonResponse({"success": "Social Link is updated!"}, status=status.HTTP_200_OK)
    except ValidationError as v:
        print(v.message)
        return JsonResponse({"error": v.message}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except jwt.exceptions.DecodeError:
        return JsonResponse({"error": "User is not logged in."}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except KeyError:
        return JsonResponse({"error": "Required Data was not found!"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except AttributeError:
        return JsonResponse({"error": "Something went wrong!"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except Exception as e:
        return JsonResponse({"error": e.args}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def deleteSocialLink(request, social_link_id):
    try:
        received_token = request.COOKIES.get("JWT_TOKEN")
        decoded_token = decode_jwt_token(received_token)
        deleted_ = SocialLinks.objects.filter(social_link_author=decoded_token['user_id'],
                                              social_link_id=social_link_id).delete()
        if deleted_[0] == 0:
            return JsonResponse({"error": "Requested Social Link Details not found."},
                                status=status.HTTP_406_NOT_ACCEPTABLE)
        return JsonResponse({"success": "Social Link deleted successfully!"}, status=status.HTTP_200_OK)
    except KeyError:
        return JsonResponse({"error": "Required Data was not found!"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except jwt.exceptions.DecodeError:
        return JsonResponse({"error": "User is not logged in."}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except Exception as e:
        return JsonResponse({"error": e.args}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def UserAddSkill(request):
    """
    {
    "skills":[
        {
            "skill_id": 1,

        },
        {
            "skill_id": 5,

        },
        ]
    }
    :param request:
    :return:
    """
    try:
        received_token = request.COOKIES.get("JWT_TOKEN")
        received_data = request.data
        list_of_skills = list(received_data.get("skills"))
        decoded_token = decode_jwt_token(received_token)
        verified_skills = []
        for each_skill in list_of_skills:
            skill = ProfileSkills(skill_id=Skills.objects.get(skill_id=each_skill['skill_id']),
                                  user_id=UserAccount.objects.get(user_id=decoded_token["user_id"]),
                                  profile_skill_id=str(uuid.uuid4()))
            verified_skills.append(skill)
        for skill in verified_skills:
            skill.save()
        return JsonResponse({"success": "Skills added successfully."}, status=status.HTTP_200_OK)
    except ValidationError as v:
        print(v.message)
        return JsonResponse({"error": v.message}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except jwt.exceptions.DecodeError:
        return JsonResponse({"error": "User is not logged in."}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except AttributeError:
        return JsonResponse({"error": "Something went wrong!"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except KeyError:
        return JsonResponse({"error": "Required Data was not found!"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except Exception as e:
        return JsonResponse({"error": e.args}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def deleteSkill(request, skill_id):
    try:
        received_token = request.COOKIES.get("JWT_TOKEN")
        decoded_token = decode_jwt_token(received_token)
        deleted_ = ProfileSkills.objects.filter(user_id=decoded_token['user_id'],
                                                profile_skill_id=skill_id).delete()
        if deleted_[0] == 0:
            return JsonResponse({"error": "Skill not found."},
                                status=status.HTTP_406_NOT_ACCEPTABLE)
        return JsonResponse({"success": "Skill deleted successfully!"}, status=status.HTTP_200_OK)
    except KeyError:
        return JsonResponse({"error": "Required Data was not found!"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except jwt.exceptions.DecodeError:
        return JsonResponse({"error": "User is not logged in."}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except Exception as e:
        return JsonResponse({"error": e.args}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def CreatePost(request):
    try:
        received_token = request.COOKIES.get("JWT_TOKEN")
        decoded_token = decode_jwt_token(received_token)
        received_data = request.data

        validate_post(received_data, decoded_token["user_id"])

        return JsonResponse({"success": "Posted successfully!"}, status=status.HTTP_201_CREATED)

    except KeyError:
        return JsonResponse({"error": "Required Data was not found!"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except jwt.exceptions.DecodeError:
        return JsonResponse({"error": "User is not logged in."}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except Exception as e:
        return JsonResponse({"error": e.args}, status=status.HTTP_406_NOT_ACCEPTABLE)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def GetProfileInformation(request, user_name):
    pass


@api_view(["GET"])
@permission_classes([AllowAny])
def getContext(request):
    try:
        context_details = ContextPost.objects.all()
        return JsonResponse({"context_details": list(context_details.values())}, status=status.HTTP_200_OK)
    except Exception as e:
        return JsonResponse({"error": e.args}, status=status.HTTP_406_NOT_ACCEPTABLE)


@api_view(["GET"])
@permission_classes([AllowAny])
def getSkills(request):
    try:
        skills_details = Skills.objects.all()
        return JsonResponse({"skills": list(skills_details.values())}, status=status.HTTP_200_OK)
    except Exception as e:
        return JsonResponse({"error": e.args}, status=status.HTTP_406_NOT_ACCEPTABLE)
