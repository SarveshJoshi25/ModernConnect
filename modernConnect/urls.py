from django.urls import path

from . import views

urlpatterns = [
    path("user/signup/", views.UserSignup, name="User Signup"),
    path("user/login/", views.UserLogin, name="User Login"),
    path("user/logout/", views.userLogout, name="User Logout"),

    path("user/verify_email/", views.verifyEmailAddress, name="Email Verification"),

    path("user/add/educational_details/", views.UserAddEducationalDetails, name="Add educational details"),
    path("user/get/educational_details/", views.getEducationalDetails, name="Get Educational Details"),
    path("user/update/educational_details/<str:education_id>/", views.editEducationalDetailsSeparate,
         name="editEducationalDetailsSeparate"),
    path("user/delete/educational_details/<str:education_id>", views.deleteEducationalDetailsSeparate,
         name="DeleteEducationalDetailsSeparate"),

    path("user/add/work_details/", views.UserAddWorkExperience, name="Add work experience"),


    path("get/degrees/", views.get_degree_types, name="Get Degrees"),


]
