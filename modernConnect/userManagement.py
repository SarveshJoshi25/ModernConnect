import uuid

from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.db import models


# Use this only user for both User and Alumni
class MyAccountManager(BaseUserManager):
    def create_user(self, user_id, user_name, user_email, user_password, user_full_name, user_gender,
                    user_account_type, user_contact, user_bio, user_if_email_verified, user_if_access_given):
        user = self.model(
            user_id=user_id,
            user_name=user_name,
            user_email=user_email,
            user_full_name=user_full_name,
            user_gender=user_gender,
            user_account_type=user_account_type,
            user_contact=user_contact,
            user_bio=user_bio,
            user_if_email_verified=user_if_email_verified,
            alumni_if_access_given=user_if_access_given,
        )

        user.set_password(user_password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email_address, password):
        user = self.model(
            email_address=email_address,
            user_password=password,
        )
        user.is_admin = True
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)





