import datetime
import uuid

from django.db import models
from django.shortcuts import get_object_or_404
from django.contrib.auth.base_user import AbstractBaseUser
from .userManagement import MyAccountManager
import django.utils.timezone
from django.core.validators import validate_comma_separated_integer_list


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


class WorkExperience(models.Model):
    work_experience_id = models.CharField(primary_key=True, default=str(uuid.uuid4()), editable=False, max_length=60)
    work_designation = models.CharField(max_length=60, null=False, editable=True,
                                        error_messages={"null": "Designation can't be null."})
    work_organization = models.CharField(max_length=120, null=False, editable=True,
                                         error_messages={"null": "Work Organization can't be null."})
    first_day_at_work = models.DateField()
    is_current_employer = models.BooleanField(editable=True, error_messages={"error": "Current Employee value can "
                                                                                      "only be True or False. "})
    last_day_at_work = models.DateField(null=True)
    work_description = models.CharField(max_length=1200, null=True, editable=True)
    work_experience = models.CharField(max_length=120, null=True, editable=False)
    user_id = models.CharField(editable=False, max_length=60)


class EducationalExperience(models.Model):
    education_id = models.CharField(primary_key=True, default=str(uuid.uuid4()), editable=False, max_length=60)
    institute = models.CharField(max_length=120, null=False, editable=True,
                                 error_messages={"null": "Institute can't be null."})
    location = models.CharField(max_length=120, null=False, editable=True,
                                error_messages={"null": "Institute Location can't be null."})
    enrollment_year = models.IntegerField()
    completion_year = models.IntegerField()
    degree = models.CharField(max_length=120, null=False, editable=True,
                              error_messages={"null": "Degree can't be null."})
    stream = models.CharField(max_length=120, null=False, editable=True,
                              error_messages={"null": "Stream can't be null."})
    grade = models.CharField(max_length=20, null=True, editable=True)
    user_id = models.CharField(editable=False, max_length=60)


class Skills(models.Model):
    skill_id = models.IntegerField(primary_key=True, editable=False)
    skill_name = models.CharField(max_length=120, null=False, editable=True)


class ProjectDetails(models.Model):
    project_id = models.CharField(primary_key=True, default=str(uuid.uuid4()), editable=False, max_length=60)
    project_title = models.CharField(max_length=60, null=False, editable=True,
                                     error_messages={'null': "Project title can't be empty."})
    project_headline = models.CharField(max_length=180, null=False, editable=True,
                                        error_messages={'null': "Project headline can't be empty."})
    project_link = models.CharField(max_length=1200, null=True, editable=True)
    project_description = models.TextField(null=True, editable=True)
    user_id = models.CharField(editable=False, max_length=60)


class ContextPost(models.Model):
    context_id = models.IntegerField(primary_key=True, editable=False)
    context_name = models.CharField(max_length=120, null=False, editable=True)


class SocialLinks(models.Model):
    social_link_id = models.CharField(primary_key=True, default=str(uuid.uuid4()), editable=False, max_length=60)
    social_link_author = models.ForeignKey("UserAccount", verbose_name="social_link_author", on_delete=models.CASCADE)
    social_link = models.URLField(null=False, max_length=1200, verbose_name="social_link", error_messages={
        "null": "URL field can't be null."
    })
    social_link_title = models.CharField(max_length=120, verbose_name="social_link_title", null=False)


class ProfileSkills(models.Model):
    profile_skill_id = models.CharField(primary_key=True, default=str(uuid.uuid4()), editable=False, max_length=60)
    user_id = models.ForeignKey("UserAccount", verbose_name="user_id", on_delete=models.CASCADE)
    skill_id = models.ForeignKey("Skills", verbose_name="skill_id", on_delete=models.CASCADE)


class Polls(models.Model):
    post_id = models.ForeignKey("Posts", verbose_name="post_id", on_delete=models.CASCADE)
    poll_option_id = models.CharField(primary_key=True, verbose_name="poll_option_id", editable=False, max_length=60)
    poll_option_text = models.CharField(verbose_name="poll_option_text", max_length=60)


class PollVotes(models.Model):
    poll_option_id = models.ForeignKey("Polls", verbose_name="poll_option_id", on_delete=models.CASCADE)
    voter_id = models.ForeignKey("UserAccount", verbose_name="post_author", on_delete=models.CASCADE)
    post_id = models.ForeignKey("Posts", verbose_name="post_id", on_delete=models.CASCADE)

class UpvotePosts(models.Model):
    post_id = models.ForeignKey("Posts", verbose_name="post_id", on_delete=models.CASCADE)
    upvote_by = models.ForeignKey("UserAccount", verbose_name="upvote_by", on_delete=models.CASCADE)


class Posts(models.Model):
    post_id = models.CharField(verbose_name="post_id", primary_key=True, default=str(uuid.uuid4()), editable=False,
                               max_length=60)
    post_author = models.ForeignKey("UserAccount", verbose_name="post_author", on_delete=models.CASCADE)
    posted_on = models.DateTimeField(verbose_name="posted_on", default=django.utils.timezone.now, editable=False)
    post_content = models.CharField(verbose_name="post_content", max_length=480, null=False)
    post_context = models.ForeignKey("ContextPost", verbose_name="post_context", on_delete=models.CASCADE)
    skills = models.CharField(validators=[validate_comma_separated_integer_list], max_length=120)
    post_active = models.BooleanField(default=True)
