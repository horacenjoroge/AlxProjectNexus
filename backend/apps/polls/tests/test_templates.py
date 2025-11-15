"""
Comprehensive tests for poll templates.
"""

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.polls.models import Poll, PollOption
from apps.polls.templates import (
    create_poll_from_template,
    get_template,
    list_templates,
    validate_template_options,
)


@pytest.mark.unit
class TestTemplateDefinitions:
    """Test template definitions."""

    def test_all_templates_exist(self):
        """Test that all required templates exist."""
        templates = list_templates()
        assert "yes_no" in templates
        assert "multiple_choice" in templates
        assert "rating_scale" in templates
        assert "agreement_scale" in templates
        assert "ranking" in templates

    def test_yes_no_template_structure(self):
        """Test yes/no template structure."""
        template = get_template("yes_no")
        assert template is not None
        assert template["name"] == "Yes/No Poll"
        assert len(template["default_options"]) == 2
        assert template["default_options"][0]["text"] == "Yes"
        assert template["default_options"][1]["text"] == "No"

    def test_multiple_choice_template_structure(self):
        """Test multiple choice template structure."""
        template = get_template("multiple_choice")
        assert template is not None
        assert template["name"] == "Multiple Choice Poll"
        assert len(template["default_options"]) == 4
        assert all(opt["text"].startswith("Option ") for opt in template["default_options"])

    def test_rating_scale_template_structure(self):
        """Test rating scale template structure."""
        template = get_template("rating_scale")
        assert template is not None
        assert template["name"] == "Rating Scale Poll"
        assert len(template["default_options"]) == 5
        assert all("Star" in opt["text"] for opt in template["default_options"])

    def test_agreement_scale_template_structure(self):
        """Test agreement scale template structure."""
        template = get_template("agreement_scale")
        assert template is not None
        assert template["name"] == "Agreement Scale Poll"
        assert len(template["default_options"]) == 5
        assert template["default_options"][0]["text"] == "Strongly Disagree"
        assert template["default_options"][4]["text"] == "Strongly Agree"

    def test_ranking_template_structure(self):
        """Test ranking template structure."""
        template = get_template("ranking")
        assert template is not None
        assert template["name"] == "Ranking Poll"
        assert len(template["default_options"]) == 5
        assert all(opt["text"].startswith("Item ") for opt in template["default_options"])


@pytest.mark.django_db
class TestTemplatePollCreation:
    """Test creating polls from templates."""

    def test_yes_no_template_creates_correct_structure(self, user):
        """Test that yes/no template creates correct poll structure."""
        poll_data = create_poll_from_template(
            template_id="yes_no",
            title="Do you like pizza?",
        )

        assert poll_data["title"] == "Do you like pizza?"
        assert len(poll_data["options"]) == 2
        assert poll_data["options"][0]["text"] == "Yes"
        assert poll_data["options"][1]["text"] == "No"
        assert poll_data["settings"]["allow_multiple_votes"] is False

    def test_multiple_choice_template_creates_correct_structure(self, user):
        """Test that multiple choice template creates correct poll structure."""
        poll_data = create_poll_from_template(
            template_id="multiple_choice",
            title="What is your favorite color?",
        )

        assert poll_data["title"] == "What is your favorite color?"
        assert len(poll_data["options"]) == 4
        assert all(opt["text"].startswith("Option ") for opt in poll_data["options"])

    def test_rating_scale_template_creates_correct_structure(self, user):
        """Test that rating scale template creates correct poll structure."""
        poll_data = create_poll_from_template(
            template_id="rating_scale",
            title="Rate this product",
        )

        assert poll_data["title"] == "Rate this product"
        assert len(poll_data["options"]) == 5
        assert all("Star" in opt["text"] for opt in poll_data["options"])
        assert poll_data["settings"]["rating_scale"] is True

    def test_agreement_scale_template_creates_correct_structure(self, user):
        """Test that agreement scale template creates correct poll structure."""
        poll_data = create_poll_from_template(
            template_id="agreement_scale",
            title="I agree with this statement",
        )

        assert poll_data["title"] == "I agree with this statement"
        assert len(poll_data["options"]) == 5
        assert poll_data["options"][0]["text"] == "Strongly Disagree"
        assert poll_data["options"][4]["text"] == "Strongly Agree"
        assert poll_data["settings"]["agreement_scale"] is True

    def test_ranking_template_creates_correct_structure(self, user):
        """Test that ranking template creates correct poll structure."""
        poll_data = create_poll_from_template(
            template_id="ranking",
            title="Rank these items",
        )

        assert poll_data["title"] == "Rank these items"
        assert len(poll_data["options"]) == 5
        assert all(opt["text"].startswith("Item ") for opt in poll_data["options"])
        assert poll_data["settings"]["ranking_poll"] is True


@pytest.mark.django_db
class TestTemplateWithCustomOptions:
    """Test templates with custom options."""

    def test_template_with_custom_options(self, user):
        """Test template with custom options overrides defaults."""
        custom_options = [
            {"text": "Option 1", "order": 0},
            {"text": "Option 2", "order": 1},
            {"text": "Option 3", "order": 2},
        ]

        poll_data = create_poll_from_template(
            template_id="yes_no",
            title="Custom Poll",
            custom_options=custom_options,
        )

        assert len(poll_data["options"]) == 3
        assert poll_data["options"][0]["text"] == "Option 1"
        assert poll_data["options"][2]["text"] == "Option 3"

    def test_template_with_custom_settings(self, user):
        """Test template with custom settings merges with defaults."""
        custom_settings = {"show_results": False, "new_setting": True}

        poll_data = create_poll_from_template(
            template_id="yes_no",
            title="Custom Settings Poll",
            custom_settings=custom_settings,
        )

        assert poll_data["settings"]["show_results"] is False  # Overridden
        assert poll_data["settings"]["allow_multiple_votes"] is False  # From template
        assert poll_data["settings"]["new_setting"] is True  # Added

    def test_template_with_custom_options_and_settings(self, user):
        """Test template with both custom options and settings."""
        custom_options = [{"text": "A"}, {"text": "B"}]
        custom_settings = {"show_results": False}

        poll_data = create_poll_from_template(
            template_id="multiple_choice",
            title="Fully Custom Poll",
            custom_options=custom_options,
            custom_settings=custom_settings,
        )

        assert len(poll_data["options"]) == 2
        assert poll_data["options"][0]["text"] == "A"
        assert poll_data["settings"]["show_results"] is False


@pytest.mark.django_db
class TestTemplateAPI:
    """Test template API endpoints."""

    def test_list_templates_endpoint(self, user):
        """Test listing all templates."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("poll-list-templates")
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "yes_no" in response.data
        assert "multiple_choice" in response.data
        assert "rating_scale" in response.data
        assert "agreement_scale" in response.data
        assert "ranking" in response.data

    def test_get_template_endpoint(self, user):
        """Test getting specific template."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("poll-get-template", kwargs={"template_id": "yes_no"})
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == "yes_no"
        assert response.data["name"] == "Yes/No Poll"
        assert "default_options" in response.data

    def test_get_invalid_template_endpoint(self, user):
        """Test getting invalid template returns 404."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("poll-get-template", kwargs={"template_id": "invalid_template"})
        response = client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_poll_from_template_api(self, user):
        """Test creating poll from template via API."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("poll-create-from-template")
        data = {
            "template_id": "yes_no",
            "title": "Do you like pizza?",
            "description": "A simple yes/no question",
        }

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "Do you like pizza?"
        assert len(response.data["options"]) == 2
        assert response.data["options"][0]["text"] == "Yes"
        assert response.data["options"][1]["text"] == "No"

        # Verify poll in database
        poll = Poll.objects.get(id=response.data["id"])
        assert poll.created_by == user
        assert poll.options.count() == 2

    def test_create_poll_from_template_with_custom_options(self, user):
        """Test creating poll from template with custom options."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("poll-create-from-template")
        data = {
            "template_id": "yes_no",
            "title": "Custom Yes/No",
            "custom_options": [
                {"text": "Definitely Yes"},
                {"text": "Definitely No"},
            ],
        }

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data["options"]) == 2
        assert response.data["options"][0]["text"] == "Definitely Yes"
        assert response.data["options"][1]["text"] == "Definitely No"

    def test_create_poll_from_template_with_custom_settings(self, user):
        """Test creating poll from template with custom settings."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("poll-create-from-template")
        data = {
            "template_id": "yes_no",
            "title": "Custom Settings Poll",
            "custom_settings": {"show_results": False, "allow_multiple_votes": True},
        }

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        poll = Poll.objects.get(id=response.data["id"])
        assert poll.settings["show_results"] is False
        assert poll.settings["allow_multiple_votes"] is True


@pytest.mark.django_db
class TestInvalidTemplate:
    """Test invalid template handling."""

    def test_invalid_template_rejected(self, user):
        """Test that invalid template ID is rejected."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("poll-create-from-template")
        data = {
            "template_id": "invalid_template",
            "title": "Test Poll",
        }

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid template" in str(response.data).lower() or "not found" in str(response.data).lower()

    def test_template_with_invalid_custom_options(self, user):
        """Test that invalid custom options are rejected."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("poll-create-from-template")
        data = {
            "template_id": "yes_no",
            "title": "Test Poll",
            "custom_options": [{"text": "Only One Option"}],  # Less than minimum
        }

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "at least 2 options" in str(response.data).lower()

    def test_template_with_too_many_custom_options(self, user):
        """Test that too many custom options are rejected."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("poll-create-from-template")
        data = {
            "template_id": "yes_no",
            "title": "Test Poll",
            "custom_options": [{"text": f"Option {i}"} for i in range(101)],  # More than maximum
        }

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "more than 100 options" in str(response.data).lower()


@pytest.mark.unit
class TestTemplateValidation:
    """Test template validation functions."""

    def test_validate_template_options_valid(self):
        """Test that valid options pass validation."""
        options = [
            {"text": "Option 1", "order": 0},
            {"text": "Option 2", "order": 1},
        ]

        result = validate_template_options(options)
        assert result is True

    def test_validate_template_options_too_few(self):
        """Test that too few options fail validation."""
        options = [{"text": "Only One"}]

        with pytest.raises(ValueError) as exc_info:
            validate_template_options(options)

        assert "at least 2 options" in str(exc_info.value).lower()

    def test_validate_template_options_too_many(self):
        """Test that too many options fail validation."""
        options = [{"text": f"Option {i}"} for i in range(101)]

        with pytest.raises(ValueError) as exc_info:
            validate_template_options(options)

        assert "more than 100 options" in str(exc_info.value).lower()

    def test_validate_template_options_missing_text(self):
        """Test that options without text fail validation."""
        options = [{"order": 0}, {"text": "Option 2"}]

        with pytest.raises(ValueError) as exc_info:
            validate_template_options(options)

        assert "missing 'text' field" in str(exc_info.value).lower()


@pytest.mark.django_db
class TestTemplateIntegration:
    """Integration tests for templates."""

    def test_create_all_template_types(self, user):
        """Test creating polls from all template types."""
        client = APIClient()
        client.force_authenticate(user=user)

        templates = ["yes_no", "multiple_choice", "rating_scale", "agreement_scale", "ranking"]

        for template_id in templates:
            url = reverse("poll-create-from-template")
            data = {
                "template_id": template_id,
                "title": f"Test {template_id} Poll",
            }

            response = client.post(url, data, format="json")

            assert response.status_code == status.HTTP_201_CREATED
            assert response.data["title"] == f"Test {template_id} Poll"

            # Verify poll exists
            poll = Poll.objects.get(id=response.data["id"])
            assert poll.created_by == user
            assert poll.options.count() >= 2

    def test_template_poll_has_correct_settings(self, user):
        """Test that template polls have correct settings."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("poll-create-from-template")
        data = {
            "template_id": "rating_scale",
            "title": "Rate this",
        }

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        poll = Poll.objects.get(id=response.data["id"])
        assert poll.settings["rating_scale"] is True
        assert poll.settings["show_results"] is True

