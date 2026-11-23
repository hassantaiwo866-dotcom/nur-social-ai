import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import r2_temp_storage


class TemporaryR2StorageTests(unittest.TestCase):
    def setUp(self):
        self.settings = {
            "account_id": "account-test",
            "access_key": "access-test",
            "secret_key": "secret-test",
            "bucket": "nur-temporary",
        }
        self.client = Mock()
        self.client.generate_presigned_url.return_value = (
            "https://bucket.account.r2.cloudflarestorage.com/object?signature=test"
        )

    def image(self, folder, name="scene.png", content=b"\x89PNG\r\n\x1a\n" + b"x" * 128):
        path = Path(folder) / name
        path.write_bytes(content)
        return path

    def test_uploads_private_image_yields_signed_url_and_deletes_object(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.image(folder)
            with patch.object(r2_temp_storage, "_settings", return_value=self.settings), patch.object(
                r2_temp_storage, "_client", return_value=self.client
            ):
                with r2_temp_storage.temporary_image_url(path) as url:
                    self.assertTrue(url.startswith("https://"))
                    self.client.upload_file.assert_called_once()
                    self.client.generate_presigned_url.assert_called_once_with(
                        "get_object",
                        Params={
                            "Bucket": "nur-temporary",
                            "Key": self.client.upload_file.call_args.args[2],
                        },
                        ExpiresIn=600,
                    )
                    self.client.delete_object.assert_not_called()
                self.client.delete_object.assert_called_once()

    def test_cleanup_runs_when_consumer_raises(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.image(folder)
            with patch.object(r2_temp_storage, "_settings", return_value=self.settings), patch.object(
                r2_temp_storage, "_client", return_value=self.client
            ):
                with self.assertRaisesRegex(RuntimeError, "Agnes failed"):
                    with r2_temp_storage.temporary_image_url(path):
                        raise RuntimeError("Agnes failed")
            self.client.delete_object.assert_called_once()

    def test_disabled_by_default_does_not_create_client(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.image(folder)
            with patch.dict("os.environ", {"ENABLE_R2_TEMP_STORAGE": ""}), patch.object(
                r2_temp_storage, "_client"
            ) as make_client:
                with self.assertRaisesRegex(RuntimeError, "disabled"):
                    with r2_temp_storage.temporary_image_url(path):
                        pass
                make_client.assert_not_called()

    def test_requires_free_tier_confirmation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.image(folder)
            with patch.dict("os.environ", {
                "ENABLE_R2_TEMP_STORAGE": "true",
                "R2_FREE_TIER_CONFIRMED": "",
            }), patch.object(r2_temp_storage, "_client") as make_client:
                with self.assertRaisesRegex(RuntimeError, "free-tier"):
                    with r2_temp_storage.temporary_image_url(path):
                        pass
                make_client.assert_not_called()

    def test_rejects_images_larger_than_ten_megabytes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.image(folder, content=b"x" * (10 * 1024 * 1024 + 1))
            with patch.object(r2_temp_storage, "_settings", return_value=self.settings), patch.object(
                r2_temp_storage, "_client"
            ) as make_client:
                with self.assertRaisesRegex(ValueError, "10 MB"):
                    with r2_temp_storage.temporary_image_url(path):
                        pass
                make_client.assert_not_called()

    def test_rejects_unsupported_file_type(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.image(folder, name="scene.gif")
            with patch.object(r2_temp_storage, "_settings", return_value=self.settings), patch.object(
                r2_temp_storage, "_client"
            ) as make_client:
                with self.assertRaisesRegex(ValueError, "PNG, JPEG and WebP"):
                    with r2_temp_storage.temporary_image_url(path):
                        pass
                make_client.assert_not_called()

    def test_url_lifetime_is_bounded(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.image(folder)
            with self.assertRaisesRegex(ValueError, "60 and 900"):
                with r2_temp_storage.temporary_image_url(path, ttl_seconds=3600):
                    pass


if __name__ == "__main__":
    unittest.main()
