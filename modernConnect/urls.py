from django.urls import path

from . import views

urlpatterns = [
    path("awake/", views.IsAwake, name="Is Awake"),

    path("user/signup/", views.UserSignup, name="User Signup"),

    path("user/edit/details/", views.editUserDetails),

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

    path("user/add/social_link/", views.UserAddSocialLink, name="Add social_link"),
    path("user/get/social_link/", views.GetSocialLink, name="Get social_link"),
    path("user/update/social_link/<str:social_link_id>/", views.editSocialLink,
         name="Edit social_link"),
    path("user/delete/social_link/<str:social_link_id>/", views.deleteSocialLink,
         name="Delete social_link"),

    path("user/add/skill/", views.UserAddSkill, name="Add skill"),
    path("user/delete/skill/<str:skill_id>/", views.deleteSkill,
         name="Delete Skill"),


    path("profile/<str:user_name>", views.GetProfileInformation, name="GetProfileInformation"),

    path("user/create/post/", views.CreatePost, name="CreatePost"),
    path("user/delete/post/<str:post_id>/", views.DeletePost, name="DeletePost"),
    path("user/upvote/post/<str:post_id>/", views.UpvotePost, name="UpvotePost"),

    path("user/vote/<str:option_id>/", views.Vote, name="Vote"),
    path("user/get/poll/result/<str:post_id>/", views.GetVoteResult, name="GetVoteResult"),

    path("user/report/account/<str:profile_id>/", views.ReportAccount, name="ReportAccount"),
    path("user/report/post/<str:post_id>/", views.ReportPost, name="ReportPost"),

    path("get/degrees/", views.get_degree_types, name="Get Degrees"),
    path("get/context/", views.getContext, name="getContext")
]
