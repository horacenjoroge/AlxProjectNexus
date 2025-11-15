"""
Poll templates for common use cases.
Provides pre-made poll structures that can be customized.
"""

from typing import Dict, List, Optional

# Template definitions
POLL_TEMPLATES = {
    "yes_no": {
        "name": "Yes/No Poll",
        "description": "Simple binary choice poll",
        "default_options": [
            {"text": "Yes", "order": 0},
            {"text": "No", "order": 1},
        ],
        "settings": {
            "allow_multiple_votes": False,
            "show_results": True,
        },
    },
    "multiple_choice": {
        "name": "Multiple Choice Poll",
        "description": "Poll with multiple options (A/B/C/D)",
        "default_options": [
            {"text": "Option A", "order": 0},
            {"text": "Option B", "order": 1},
            {"text": "Option C", "order": 2},
            {"text": "Option D", "order": 3},
        ],
        "settings": {
            "allow_multiple_votes": False,
            "show_results": True,
        },
    },
    "rating_scale": {
        "name": "Rating Scale Poll",
        "description": "1-5 star rating poll",
        "default_options": [
            {"text": "1 Star", "order": 0},
            {"text": "2 Stars", "order": 1},
            {"text": "3 Stars", "order": 2},
            {"text": "4 Stars", "order": 3},
            {"text": "5 Stars", "order": 4},
        ],
        "settings": {
            "allow_multiple_votes": False,
            "show_results": True,
            "rating_scale": True,
        },
    },
    "agreement_scale": {
        "name": "Agreement Scale Poll",
        "description": "Likert scale from Strongly Disagree to Strongly Agree",
        "default_options": [
            {"text": "Strongly Disagree", "order": 0},
            {"text": "Disagree", "order": 1},
            {"text": "Neutral", "order": 2},
            {"text": "Agree", "order": 3},
            {"text": "Strongly Agree", "order": 4},
        ],
        "settings": {
            "allow_multiple_votes": False,
            "show_results": True,
            "agreement_scale": True,
        },
    },
    "ranking": {
        "name": "Ranking Poll",
        "description": "Poll for ranking multiple items",
        "default_options": [
            {"text": "Item 1", "order": 0},
            {"text": "Item 2", "order": 1},
            {"text": "Item 3", "order": 2},
            {"text": "Item 4", "order": 3},
            {"text": "Item 5", "order": 4},
        ],
        "settings": {
            "allow_multiple_votes": False,
            "show_results": True,
            "ranking_poll": True,
        },
    },
}


def get_template(template_id: str) -> Optional[Dict]:
    """
    Get poll template by ID.

    Args:
        template_id: Template identifier (yes_no, multiple_choice, etc.)

    Returns:
        dict: Template definition or None if not found
    """
    return POLL_TEMPLATES.get(template_id)


def list_templates() -> Dict[str, Dict]:
    """
    List all available poll templates.

    Returns:
        dict: Dictionary of template_id -> template_info
    """
    return {
        template_id: {
            "id": template_id,
            "name": template["name"],
            "description": template["description"],
            "option_count": len(template["default_options"]),
        }
        for template_id, template in POLL_TEMPLATES.items()
    }


def create_poll_from_template(
    template_id: str,
    title: str,
    description: str = "",
    custom_options: Optional[List[Dict]] = None,
    custom_settings: Optional[Dict] = None,
    starts_at=None,
    ends_at=None,
    is_active: bool = True,
) -> Dict:
    """
    Create poll data structure from template.

    Args:
        template_id: Template identifier
        title: Poll title
        description: Poll description (optional)
        custom_options: Custom options to override template defaults
        custom_settings: Custom settings to merge with template defaults
        starts_at: Poll start date (optional)
        ends_at: Poll end date (optional)
        is_active: Whether poll is active

    Returns:
        dict: Poll data structure ready for creation

    Raises:
        ValueError: If template_id is invalid
    """
    template = get_template(template_id)
    if not template:
        raise ValueError(f"Invalid template ID: {template_id}")

    # Use custom options if provided, otherwise use template defaults
    options = custom_options if custom_options else template["default_options"]

    # Merge custom settings with template defaults
    settings = template["settings"].copy()
    if custom_settings:
        settings.update(custom_settings)

    poll_data = {
        "title": title,
        "description": description or template.get("description", ""),
        "options": options,
        "settings": settings,
        "is_active": is_active,
    }

    if starts_at:
        poll_data["starts_at"] = starts_at
    if ends_at:
        poll_data["ends_at"] = ends_at

    return poll_data


def validate_template_options(options: List[Dict]) -> bool:
    """
    Validate that template options meet requirements.

    Args:
        options: List of option dictionaries

    Returns:
        bool: True if valid

    Raises:
        ValueError: If options are invalid
    """
    from .serializers import MIN_OPTIONS, MAX_OPTIONS

    if len(options) < MIN_OPTIONS:
        raise ValueError(f"Template must have at least {MIN_OPTIONS} options. Provided: {len(options)}")

    if len(options) > MAX_OPTIONS:
        raise ValueError(f"Template cannot have more than {MAX_OPTIONS} options. Provided: {len(options)}")

    # Validate each option has required fields
    for i, option in enumerate(options):
        if "text" not in option:
            raise ValueError(f"Option {i} is missing 'text' field")

    return True

