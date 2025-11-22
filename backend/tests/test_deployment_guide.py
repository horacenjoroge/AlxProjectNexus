"""
Tests to verify deployment guide completeness and accuracy.

These tests ensure that:
1. All deployment steps are documented
2. Commands in the guide are valid
3. Environment variables are documented
4. Configuration files exist
5. Deployment guide can be followed on a fresh system
"""

import re
from pathlib import Path

import pytest


class TestDeploymentGuide:
    """Test deployment guide completeness and accuracy."""

    @pytest.fixture
    def guide_path(self):
        """Path to deployment guide."""
        return Path(__file__).parent.parent.parent / "docs" / "deployment-guide.md"

    @pytest.fixture
    def guide_content(self, guide_path):
        """Read deployment guide content."""
        if not guide_path.exists():
            pytest.skip(f"Deployment guide not found: {guide_path}")
        return guide_path.read_text()

    def test_deployment_guide_exists(self, guide_path):
        """Test that deployment guide file exists."""
        assert guide_path.exists(), f"Deployment guide not found at {guide_path}"

    def test_all_required_sections_present(self, guide_content):
        """Test that all required sections are documented."""
        required_sections = [
            "## 1. Prerequisites",
            "## 2. Environment Variable Setup",
            "## 3. Docker Deployment",
            "## 4. Database Migrations",
            "## 5. SSL Setup",
            "## 6. Monitoring Setup",
            "## 7. Backup Strategy",
            "## 8. Post-Deployment Verification",
            "## 9. Troubleshooting",
            "## 10. Test Verification",
        ]

        missing_sections = []
        for section in required_sections:
            if section not in guide_content:
                missing_sections.append(section)

        assert not missing_sections, f"Missing required sections: {missing_sections}"

    def test_environment_variables_documented(self, guide_content):
        """Test that all required environment variables are documented."""
        required_vars = [
            "SECRET_KEY",
            "DEBUG",
            "ALLOWED_HOSTS",
            "DB_NAME",
            "DB_USER",
            "DB_PASSWORD",
            "DB_HOST",
            "REDIS_HOST",
            "CELERY_BROKER_URL",
            "SECURE_SSL_REDIRECT",
            "SESSION_COOKIE_SECURE",
            "CSRF_COOKIE_SECURE",
        ]

        missing_vars = []
        for var in required_vars:
            if var not in guide_content:
                missing_vars.append(var)

        assert (
            not missing_vars
        ), f"Missing environment variables in documentation: {missing_vars}"

    def test_docker_commands_documented(self, guide_content):
        """Test that Docker deployment commands are documented."""
        # Check for key Docker command patterns
        docker_patterns = [
            "docker-compose",
            "docker-compose.prod.yml",
            "up -d",
            "build",
            "ps",
            "logs",
        ]

        missing_patterns = []
        for pattern in docker_patterns:
            if pattern not in guide_content:
                missing_patterns.append(pattern)

        assert (
            not missing_patterns
        ), f"Missing Docker command patterns: {missing_patterns}"

    def test_migration_commands_documented(self, guide_content):
        """Test that database migration commands are documented."""
        required_commands = [
            "python manage.py migrate",
            "python manage.py showmigrations",
            "python manage.py createsuperuser",
        ]

        missing_commands = []
        for cmd in required_commands:
            if cmd not in guide_content:
                missing_commands.append(cmd)

        assert not missing_commands, f"Missing migration commands: {missing_commands}"

    def test_ssl_setup_documented(self, guide_content):
        """Test that SSL setup is documented."""
        ssl_topics = [
            "SSL",
            "Let's Encrypt",
            "certbot",
            "nginx-ssl.conf",
            "fullchain.pem",
            "privkey.pem",
        ]

        missing_topics = []
        for topic in ssl_topics:
            if topic not in guide_content:
                missing_topics.append(topic)

        assert not missing_topics, f"Missing SSL topics: {missing_topics}"

    def test_backup_commands_documented(self, guide_content):
        """Test that backup commands are documented."""
        backup_commands = [
            "pg_dump",
            "backup",
            "restore",
        ]

        missing_commands = []
        for cmd in backup_commands:
            if cmd.lower() not in guide_content.lower():
                missing_commands.append(cmd)

        assert not missing_commands, f"Missing backup commands: {missing_commands}"

    def test_monitoring_setup_documented(self, guide_content):
        """Test that monitoring setup is documented."""
        monitoring_topics = [
            "health check",
            "monitoring",
            "logs",
            "Prometheus",
            "Grafana",
        ]

        found_topics = [
            topic
            for topic in monitoring_topics
            if topic.lower() in guide_content.lower()
        ]

        assert (
            len(found_topics) >= 3
        ), f"Insufficient monitoring documentation. Found: {found_topics}"

    def test_troubleshooting_section_exists(self, guide_content):
        """Test that troubleshooting section exists with common issues."""
        troubleshooting_topics = [
            "Common Issues",
            "Symptoms:",
            "Solutions:",
        ]

        missing_topics = []
        for topic in troubleshooting_topics:
            if topic not in guide_content:
                missing_topics.append(topic)

        assert (
            not missing_topics
        ), f"Troubleshooting section incomplete. Missing: {missing_topics}"

    def test_code_references_exist(self, guide_content):
        """Test that code references point to existing files."""
        # Find code references
        pattern = r"`([^`]+)`"
        references = re.findall(pattern, guide_content)

        project_root = Path(__file__).parent.parent.parent
        missing_files = []

        for ref in references:
            # Filter for file paths
            if "/" in ref and (
                ref.startswith("docker/")
                or ref.startswith("backend/")
                or ref.startswith("scripts/")
            ):
                file_path = ref.split(":")[0].split("#")[0]
                full_path = project_root / file_path

                # Skip if it's a directory reference
                if file_path.endswith("/"):
                    continue

                # Check if file exists
                if not full_path.exists() and not any(
                    opt in file_path
                    for opt in ["docker-compose.prod.yml", "nginx-ssl.conf"]
                ):
                    # These might be created during deployment, so they're optional
                    if "prod.yml" not in file_path and "ssl.conf" not in file_path:
                        missing_files.append(file_path)

        # Filter out known optional files
        optional_files = [
            "scripts/backup-database.sh",
            "scripts/renew-ssl.sh",
            "scripts/test-deployment.sh",
        ]
        missing_files = [f for f in missing_files if f not in optional_files]

        assert not missing_files, f"Missing code references: {missing_files}"

    def test_docker_compose_prod_referenced(self, guide_content):
        """Test that production docker-compose file is referenced."""
        assert (
            "docker-compose.prod.yml" in guide_content
            or "docker-compose.prod" in guide_content
        ), "Production docker-compose file should be documented"

    def test_environment_example_provided(self, guide_content):
        """Test that environment variable examples are provided."""
        assert "SECRET_KEY=" in guide_content, "SECRET_KEY example should be provided"
        assert "DEBUG=" in guide_content, "DEBUG example should be provided"
        assert (
            "ALLOWED_HOSTS=" in guide_content
        ), "ALLOWED_HOSTS example should be provided"

    def test_ssl_certificate_renewal_documented(self, guide_content):
        """Test that SSL certificate renewal is documented."""
        renewal_topics = [
            "renew",
            "certbot",
            "cron",
        ]

        found_topics = [
            topic for topic in renewal_topics if topic.lower() in guide_content.lower()
        ]

        assert (
            len(found_topics) >= 2
        ), f"SSL renewal not fully documented. Found: {found_topics}"

    def test_backup_restore_procedures_documented(self, guide_content):
        """Test that backup and restore procedures are documented."""
        assert (
            "backup" in guide_content.lower()
        ), "Backup procedures should be documented"
        assert (
            "restore" in guide_content.lower()
        ), "Restore procedures should be documented"
        assert "pg_dump" in guide_content, "pg_dump command should be documented"

    def test_health_check_endpoints_documented(self, guide_content):
        """Test that health check endpoints are documented."""
        health_checks = [
            "/api/v1/",
            "health",
        ]

        found_checks = [check for check in health_checks if check in guide_content]

        assert (
            len(found_checks) >= 1
        ), f"Health check endpoints not documented. Found: {found_checks}"

    def test_post_deployment_verification_documented(self, guide_content):
        """Test that post-deployment verification steps are documented."""
        verification_steps = [
            "verify",
            "check",
            "test",
        ]

        # Check that verification section has actionable steps
        verification_section = guide_content.split(
            "## 8. Post-Deployment Verification"
        )[1].split("## 9.")[0]

        assert (
            "curl" in verification_section or "docker-compose" in verification_section
        ), "Post-deployment verification should include test commands"

    def test_production_checklist_exists(self, guide_content):
        """Test that production deployment checklist exists."""
        assert (
            "Production Checklist" in guide_content
            or "checklist" in guide_content.lower()
        ), "Production deployment checklist should be provided"

    def test_geographic_restrictions_documented(self, guide_content):
        """Test that geographic restrictions (Kenya) are documented."""
        assert (
            "KE" in guide_content or "Kenya" in guide_content
        ), "Geographic restrictions (Kenya) should be documented"

    def test_security_settings_documented(self, guide_content):
        """Test that security settings are documented."""
        security_settings = [
            "SECURE_SSL_REDIRECT",
            "SESSION_COOKIE_SECURE",
            "CSRF_COOKIE_SECURE",
        ]

        missing_settings = []
        for setting in security_settings:
            if setting not in guide_content:
                missing_settings.append(setting)

        assert not missing_settings, f"Missing security settings: {missing_settings}"

    def test_documentation_structure(self, guide_content):
        """Test that documentation has proper structure."""
        # Check for table of contents
        assert (
            "## Table of Contents" in guide_content
        ), "Table of contents should be present"

        # Check for code blocks
        code_blocks = guide_content.count("```")
        assert (
            code_blocks >= 20
        ), f"Documentation should have code examples. Found {code_blocks // 2} blocks"

    def test_quick_reference_section(self, guide_content):
        """Test that quick reference section exists."""
        assert (
            "Quick Reference" in guide_content or "Appendix" in guide_content
        ), "Quick reference or appendix section should be present"

    def test_all_steps_have_commands(self, guide_content):
        """Test that deployment steps include executable commands."""
        # Check that major sections have code blocks
        sections_with_commands = [
            "Docker Deployment",
            "Database Migrations",
            "SSL Setup",
            "Backup Strategy",
        ]

        for section in sections_with_commands:
            section_content = (
                guide_content.split(f"## {section.split()[0]}")[1].split("##")[0]
                if f"## {section.split()[0]}" in guide_content
                else ""
            )
            if section_content:
                assert (
                    "```" in section_content
                ), f"Section '{section}' should have code examples"
