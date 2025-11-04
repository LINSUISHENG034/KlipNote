"""
Test project scaffolding and structure - Story 1.1
Tests for AC1, AC3, AC4, AC5, AC7
"""

import pytest
import os
from pathlib import Path


class TestBackendStructure:
    """Test AC1: Backend directory structure and files"""

    def test_backend_directory_exists(self):
        """Verify backend directory exists (we're running from it)"""
        assert Path(".").exists()
        assert Path(".").is_dir()

    def test_app_directory_structure(self):
        """Verify all required backend directories exist"""
        required_dirs = [
            "app",
            "app/services",
            "app/tasks",
            "app/ai_services",
            "tests"
        ]
        for dir_path in required_dirs:
            assert Path(dir_path).exists(), f"Directory {dir_path} should exist"
            assert Path(dir_path).is_dir(), f"{dir_path} should be a directory"

    def test_core_files_exist(self):
        """Verify all required core files exist"""
        required_files = [
            "app/__init__.py",
            "app/main.py",
            "app/config.py",
            "app/celery_utils.py",
            "app/models.py",
            "app/services/__init__.py",
            "app/tasks/__init__.py"
        ]
        for file_path in required_files:
            assert Path(file_path).exists(), f"File {file_path} should exist"
            assert Path(file_path).is_file(), f"{file_path} should be a file"

    def test_ai_services_structure(self):
        """Verify AI services abstraction layer exists"""
        ai_services_files = [
            "app/ai_services/__init__.py",
            "app/ai_services/base.py",
            "app/ai_services/whisperx_service.py"
        ]
        for file_path in ai_services_files:
            assert Path(file_path).exists(), f"File {file_path} should exist"

    def test_docker_files_exist(self):
        """Verify Docker configuration files exist"""
        docker_files = [
            "Dockerfile",
            "docker-compose.yaml",
            ".env.example"
        ]
        for file_path in docker_files:
            assert Path(file_path).exists(), f"File {file_path} should exist"


class TestDependencies:
    """Test AC3: Dependencies configuration"""

    def test_requirements_file_exists(self):
        """Verify requirements.txt exists and is not empty"""
        requirements_path = Path("requirements.txt")
        assert requirements_path.exists()
        assert requirements_path.stat().st_size > 0

    def test_required_packages_in_requirements(self):
        """Verify all required packages are in requirements.txt"""
        requirements_path = Path("requirements.txt")
        content = requirements_path.read_text()

        required_packages = [
            "fastapi",
            "uvicorn",
            "celery",
            "redis",
            "pydantic",
            "pydantic-settings",
            "python-multipart",
            "pytest",
            "pytest-mock"
        ]

        for package in required_packages:
            assert package in content.lower(), f"{package} should be in requirements.txt"

    def test_docker_compose_services_defined(self):
        """Verify all required services are defined in docker-compose.yaml"""
        compose_path = Path("docker-compose.yaml")
        content = compose_path.read_text()

        required_services = ["redis", "web", "worker", "flower"]
        for service in required_services:
            assert service in content, f"Service '{service}' should be defined in docker-compose.yaml"


class TestGitConfiguration:
    """Test AC4, AC5: Git repository and submodule configuration"""

    def test_gitmodules_exists(self):
        """Verify .gitmodules file exists for WhisperX submodule"""
        gitmodules_path = Path("../.gitmodules")
        assert gitmodules_path.exists(), ".gitmodules file should exist"

    def test_whisperx_submodule_configured(self):
        """Verify WhisperX is configured as submodule"""
        gitmodules_path = Path("../.gitmodules")
        content = gitmodules_path.read_text()

        assert "whisperX" in content or "whisperx" in content.lower()
        assert "backend/app/ai_services/whisperx" in content

    def test_whisperx_submodule_directory_exists(self):
        """Verify WhisperX submodule directory exists"""
        whisperx_path = Path("app/ai_services/whisperx")
        assert whisperx_path.exists(), "WhisperX submodule directory should exist"

    def test_backend_gitignore_exists(self):
        """Verify backend .gitignore exists"""
        gitignore_path = Path(".gitignore")
        assert gitignore_path.exists(), "backend/.gitignore should exist"

    def test_gitignore_includes_common_patterns(self):
        """Verify .gitignore includes Python and Docker patterns"""
        gitignore_path = Path(".gitignore")
        content = gitignore_path.read_text()

        # Check for Python cache patterns (*.py[cod] is more comprehensive than *.pyc)
        assert "__pycache__" in content, "Pattern '__pycache__' should be in .gitignore"
        assert ".env" in content, "Pattern '.env' should be in .gitignore"
        assert "uploads/" in content, "Pattern 'uploads/' should be in .gitignore"
        assert ("*.py[cod]" in content or "*.pyc" in content), "Python compiled file pattern should be in .gitignore"


class TestingInfrastructure:
    """Test Task 7: Testing infrastructure setup"""

    def test_pytest_ini_exists(self):
        """Verify pytest.ini configuration exists"""
        pytest_ini = Path("pytest.ini")
        assert pytest_ini.exists(), "pytest.ini should exist"

    def test_tests_directory_exists(self):
        """Verify tests directory exists"""
        tests_dir = Path("tests")
        assert tests_dir.exists(), "tests/ directory should exist"
        assert tests_dir.is_dir()

    def test_conftest_exists(self):
        """Verify conftest.py exists with fixtures"""
        conftest_path = Path("tests/conftest.py")
        assert conftest_path.exists(), "tests/conftest.py should exist"

        # Verify it's not empty
        assert conftest_path.stat().st_size > 0, "conftest.py should not be empty"

    def test_conftest_has_required_fixtures(self):
        """Verify conftest.py defines required test fixtures"""
        conftest_path = Path("tests/conftest.py")
        content = conftest_path.read_text()

        required_fixtures = ["test_client", "mock_whisperx"]
        for fixture in required_fixtures:
            assert fixture in content, f"Fixture '{fixture}' should be defined in conftest.py"
