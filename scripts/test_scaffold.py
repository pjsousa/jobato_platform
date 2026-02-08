from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DIRS = [
    "frontend",
    "api",
    "ml",
    "infra",
    "config",
    "data",
    "scripts",
    "data/db",
    "data/db/runs",
    "data/html",
    "data/html/raw",
    "data/html/canonical",
]

REQUIRED_FILES = [
    ".env.example",
    "docker-compose.yml",
    "frontend/.env.example",
    "frontend/package.json",
    "frontend/src/main.tsx",
    "api/.env.example",
    "api/build.gradle",
    "api/gradlew",
    "api/src/main/java/com/jobato/api/JobatoApiApplication.java",
    "api/src/main/resources/application.yml",
    "ml/.env.example",
    "ml/requirements.txt",
    "ml/app/main.py",
    "data/db/current-db.txt",
    "data/.gitignore",
]


class TestScaffoldLayout(unittest.TestCase):
    def test_required_directories_exist(self) -> None:
        missing = [path for path in REQUIRED_DIRS if not (ROOT / path).is_dir()]
        self.assertEqual(missing, [], f"Missing directories: {', '.join(missing)}")

    def test_required_files_exist(self) -> None:
        missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
        self.assertEqual(missing, [], f"Missing files: {', '.join(missing)}")

    def test_docker_compose_baseline(self) -> None:
        compose_path = ROOT / "docker-compose.yml"
        content = compose_path.read_text(encoding="utf-8")
        for service in ("frontend:", "api:", "ml:", "redis:"):
            self.assertIn(service, content)
        for volume in ("./config", "./data"):
            self.assertIn(volume, content)

    def test_ml_health_route(self) -> None:
        content = (ROOT / "ml/app/main.py").read_text(encoding="utf-8")
        self.assertIn("/health", content)

    def test_api_actuator_base_path(self) -> None:
        content = (ROOT / "api/src/main/resources/application.yml").read_text(encoding="utf-8")
        self.assertIn("management", content)
        self.assertIn("/api", content)

    def test_frontend_build_output(self) -> None:
        self.assertTrue((ROOT / "frontend/dist/index.html").is_file())

    def test_api_build_output(self) -> None:
        libs_dir = ROOT / "api/build/libs"
        jars = list(libs_dir.glob("*.jar")) if libs_dir.is_dir() else []
        self.assertTrue(jars)


if __name__ == "__main__":
    unittest.main()
