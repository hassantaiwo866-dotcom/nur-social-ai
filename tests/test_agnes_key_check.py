import unittest
from unittest.mock import Mock, patch
import os
from scripts.agnes_key_check import check_models

class AgnesKeyCheckTests(unittest.TestCase):
    def test_missing_key_fails_without_request(self):
        with patch.dict(os.environ, {"AGNES_API_KEY": ""}):
            session = Mock()
            self.assertEqual(check_models(session), 2)
            session.get.assert_not_called()

    def test_auth_rejection_is_sanitized(self):
        with patch.dict(os.environ, {"AGNES_API_KEY": "secret-test"}):
            session = Mock()
            session.get.return_value.status_code = 401
            self.assertEqual(check_models(session), 2)
            session.get.assert_called_once()
            self.assertNotIn("secret-test", str(session.get.call_args))

    def test_success_reports_target_models_without_generation(self):
        with patch.dict(os.environ, {"AGNES_API_KEY": "secret-test"}):
            session = Mock()
            response = Mock(status_code=200)
            response.json.return_value = {"data": [
                {"id": "agnes-image-2.5-flash"},
                {"id": "agnes-video-2.5-flash"},
                {"id": "agnes-2.5-flash"},
            ]}
            session.get.return_value = response
            self.assertEqual(check_models(session), 0)
            session.get.assert_called_once()
            self.assertTrue(session.get.call_args.args[0].endswith("/models"))
            self.assertEqual(session.post.call_count, 0)

if __name__ == "__main__":
    unittest.main()
