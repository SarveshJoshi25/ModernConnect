from django.urls import path

from . import views

urlpatterns = [
    path("user/signup/", views.UserSignup, name="User Signup"),
    path("user/verify_email/", views.verifyEmailAddress, name="Email Verification"),
    path("user/login/", views.UserLogin, name="User Login"),
    path("user/educational_details/", views.UserAddEducationalDetails, name="Add educational details"),
    path("user/logout/", views.userLogout, name="User Logout"),

    path("user/get/educational_details/", views.getEducationalDetails, name="Get Educational Details"),
    path("user/update/educational_details/<str:education_id>", views.editEducationalDetailsSeparate,
         name="editEducationalDetailsSeparate"),
    path("get/degrees/", views.get_degree_types, name="Get Degrees"),


]
