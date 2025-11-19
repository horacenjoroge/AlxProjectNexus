"""
Factory Boy factories for User models.
"""

import factory
from django.contrib.auth.models import User
from faker import Faker

from .models import Follow, UserProfile

fake = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for User model."""

    class Meta:
        model = User
        django_get_or_create = ("username",)

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    is_staff = False
    is_superuser = False

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return
        password = extracted or "testpass123"
        self.set_password(password)
        self.save()


class UserProfileFactory(factory.django.DjangoModelFactory):
    """Factory for UserProfile model."""

    class Meta:
        model = UserProfile

    user = factory.SubFactory(UserFactory)
    bio = factory.Faker("text", max_nb_chars=500)


class FollowFactory(factory.django.DjangoModelFactory):
    """Factory for Follow model."""

    class Meta:
        model = Follow

    follower = factory.SubFactory(UserFactory)
    following = factory.SubFactory(UserFactory)

