from django.urls import path

from . import views

urlpatterns = [
  path("user/signup/", views.UserSignup, name="User Signup"),
  path("user/verify_email/", views.verifyEmailAddress, name="Email Verification")
]