from django.http import JsonResponse
from rest_framework import viewsets, status, generics, permissions
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
import pymongo
from utils import client, db


def validate_user_name(user_name: str) -> bool:
    return len(user_name) > 0


class UserSignup(APIView):
    def post(self, request) -> JsonResponse:
        try:
            received_data = self.request.data

            user_name = str(received_data.get('user_name'))
            gender = str(received_data.get('gender'))
            account_type = str(received_data.get('account_type'))
            email_address = str(received_data.get('email_address'))
            contact_number = str(received_data.get('contact_number'))
            about_yourself = str(received_data.get('about_yourself'))


        except KeyError:
            return JsonResponse({"error": "Required Data was not found!"}, status=status.HTTP_406_NOT_ACCEPTABLE)
