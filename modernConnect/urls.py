from django.urls import path

from . import views

urlpatterns = [
    path("awake/", views.IsAwake, name = "Is Awake"),

    path("user/signup/", views.UserSignup, name="User Signup"),
    path("user/login/", views.UserLogin, name="User Login"),
    path("user/logout/", views.userLogout, name="User Logout"),
    path("user/verify_email/", views.verifyEmailAddress, name="Email Verification"),

    path("user/add/educational_details/", views.UserAddEducationalDetails, name="Add educational details"),
    path("user/get/educational_details/", views.getEducationalDetails, name="Get Educational Details"),
    path("user/update/educational_details/<str:education_id>/", views.editEducationalDetailsSeparate,
         name="Edit Educational Details Separate"),
    path("user/delete/educational_details/<str:education_id>", views.deleteEducationalDetailsSeparate,
         name="Delete Educational Details Separate"),

    path("user/add/work_details/", views.UserAddWorkExperience, name="Add work experience"),
    path("user/get/work_details/", views.GetWorkDetails, name="Get Work Details"),
    path("user/update/work_details/<str:work_id>/", views.editWorkDetailsSeparate,
         name="Edit Work Details Separate"),
    path("user/delete/work_details/<str:work_id>/", views.deleteWorkDetails,
         name="Delete Work Details Separate"),

    path("user/add/project_details/", views.UserAddProjectExperience, name="Add work experience"),
    path("user/get/project_details/", views.GetProjectDetails, name="Get Work Details"),
    path("user/update/project_details/<str:project_id>/", views.editProjectDetailsSeparate,
         name="Edit Work Details Separate"),
    path("user/delete/project_details/<str:project_id>/", views.deleteProjectDetails,
         name="Delete Work Details Separate"),
    #
    #


    path("get/degrees/", views.get_degree_types, name="Get Degrees"),


]
