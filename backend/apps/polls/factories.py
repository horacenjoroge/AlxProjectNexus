"""
Factory Boy factories for Poll models.
"""

import factory
from django.contrib.auth.models import User
from django.utils import timezone
from faker import Faker

from .models import Category, Poll, PollOption, Tag

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


class CategoryFactory(factory.django.DjangoModelFactory):
    """Factory for Category model."""

    class Meta:
        model = Category
        django_get_or_create = ("slug",)

    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(" ", "-"))
    description = factory.Faker("text", max_nb_chars=200)


class TagFactory(factory.django.DjangoModelFactory):
    """Factory for Tag model."""

    class Meta:
        model = Tag
        django_get_or_create = ("slug",)

    name = factory.Sequence(lambda n: f"tag{n}")
    slug = factory.LazyAttribute(lambda obj: obj.name.lower())


class PollFactory(factory.django.DjangoModelFactory):
    """Factory for Poll model."""

    class Meta:
        model = Poll

    title = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("text", max_nb_chars=500)
    created_by = factory.SubFactory(UserFactory)
    is_active = True
    is_draft = False
    starts_at = factory.LazyFunction(timezone.now)
    ends_at = None
    settings = factory.Dict({})
    security_rules = factory.Dict({})
    cached_total_votes = 0
    cached_unique_voters = 0
    category = None

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for tag in extracted:
                self.tags.add(tag)


class PollOptionFactory(factory.django.DjangoModelFactory):
    """Factory for PollOption model."""

    class Meta:
        model = PollOption

    poll = factory.SubFactory(PollFactory)
    text = factory.Sequence(lambda n: f"Option {n}")
    order = factory.Sequence(lambda n: n)
    cached_vote_count = 0

