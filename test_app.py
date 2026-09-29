import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app import app


class GenerateDocumentTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.profile = {
            "name": "Jordan Lee",
            "role": "Product designer",
            "skills": "Research, prototyping",
            "experience": "Design intern",
            "education": "Design degree",
        }

    def test_rejects_incomplete_profile(self):
        response = self.client.post("/api/generate", json={})

        self.assertEqual(response.status_code, 400)
        self.assertIn("name", response.get_json()["error"])

    def test_rejects_invalid_document_type(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            response = self.client.post(
                "/api/generate",
                json={**self.profile, "document_type": []},
            )

        self.assertEqual(response.status_code, 400)

    def test_reports_missing_api_key(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            response = self.client.post("/api/generate", json=self.profile)

        self.assertEqual(response.status_code, 503)
        self.assertIn("OPENAI_API_KEY", response.get_json()["error"])

    def test_includes_request_id_header(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("X-Request-ID", response.headers)
        self.assertRegex(response.headers["X-Request-ID"], r"^[0-9a-f-]{36}$")

    def test_returns_mocked_cover_letter(self):
        message = SimpleNamespace(content="Dear hiring team,\n\nA tailored draft.")
        completion = SimpleNamespace(choices=[SimpleNamespace(message=message)])

        with (
            patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_MODEL": "test-model"}),
            patch("app.OpenAI") as openai_client,
        ):
            openai_client.return_value.chat.completions.create.return_value = completion
            response = self.client.post("/api/generate", json=self.profile)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["document"], message.content)
        self.assertEqual(response.get_json()["document_type"], "cover_letter")
        self.assertEqual(
            openai_client.return_value.chat.completions.create.call_args.kwargs["model"],
            "test-model",
        )

    def test_home_page_includes_pdf_export_support(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("jsPDF", html)
        self.assertIn("Download PDF", html)


if __name__ == "__main__":
    unittest.main()