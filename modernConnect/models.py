from django.db import models
from django.shortcuts import get_object_or_404
from django.contrib.auth.base_user import AbstractBaseUser
from .userManagement import MyAccountManager


class UserAccount(AbstractBaseUser):
    user_id = models.CharField(verbose_name="user_id", max_length=120, unique=True, blank=False, null=False,
                               editable=False, primary_key=True)
    user_name = models.CharField(verbose_name="user_name", max_length=20, unique=True, blank=False, null=False,
                                 default=None)
    user_email = models.EmailField(verbose_name="user_email", max_length=60, unique=True, blank=True, null=True,
                                   default=None)
    user_full_name = models.CharField(verbose_name="user_full_name", unique=False, blank=False, null=False,
                                      max_length=60)
    user_gender = models.CharField(verbose_name="user_gender", unique=False, blank=False, null=False, max_length=6)
    user_account_type = models.CharField(verbose_name="user_account_type", blank=False, null=False, default="Student",
                                         max_length=25)
    user_contact = models.CharField(verbose_name="user_contact", blank=False, null=False, max_length=10)
    user_bio = models.CharField(verbose_name="user_contact", blank=True, null=True, max_length=480)
    user_if_email_verified = models.BooleanField(verbose_name="user_if_email_verified", default=False)
    is_admin = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    USERNAME_FIELD = "user_id"

    class Meta:
        db_table = "user_accounts"

    objects = MyAccountManager()

    def has_perms(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser

    def serialize(self, data):
        self.user_id = data['user_id']
        self.user_name = data['user_name']
        self.user_full_name = data['full_name']
        self.user_gender = data['gender']
        self.user_account_type = data['account_type']
        self.user_email = data['email_address']
        self.user_contact = data['contact_number']
        self.user_bio = data['about_yourself']
        self.user_if_email_verified = data['if_verified_email']
        self.user_if_access_given = data['if_access_given']
        self.set_password(raw_password=str(data['password']))

        return self
