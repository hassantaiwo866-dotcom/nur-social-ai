import unittest
from unittest.mock import Mock, patch
import nur_generator as generator


class ProviderDiscoveryTests(unittest.TestCase):
    @patch("nur_generator.requests.get")
    def test_gemini_honours_listed_preference(self,get):
        r=Mock(); r.raise_for_status.return_value=None
        r.json.return_value={"models":[
            {"name":"models/gemini-2.5-flash","supportedGenerationMethods":["generateContent"]},
            {"name":"models/gemini-2.0-pro","supportedGenerationMethods":["generateContent"]},
            {"name":"models/embed","supportedGenerationMethods":["embedContent"]}]}
        get.return_value=r
        self.assertEqual(generator.discover_gemini_model("key","gemini-2.0-pro"),"gemini-2.0-pro")

    @patch("nur_generator.requests.get")
    def test_gemini_falls_back_to_available_flash(self,get):
        r=Mock(); r.raise_for_status.return_value=None
        r.json.return_value={"models":[
            {"name":"models/gemini-2.5-pro","supportedGenerationMethods":["generateContent"]},
            {"name":"models/gemini-2.5-flash","supportedGenerationMethods":["generateContent"]}]}
        get.return_value=r
        self.assertEqual(generator.discover_gemini_model("key","retired"),"gemini-2.5-flash")

    @patch("nur_generator.requests.get")
    def test_groq_honours_only_available_preference(self,get):
        r=Mock(); r.raise_for_status.return_value=None
        r.json.return_value={"data":[{"id":"llama-3.3-70b-versatile"},{"id":"llama-3.1-8b-instant"}]}
        get.return_value=r
        self.assertEqual(generator.discover_groq_model("key","llama-3.1-8b-instant"),"llama-3.1-8b-instant")
        self.assertEqual(generator.discover_groq_model("key","retired"),"llama-3.3-70b-versatile")

    def test_commons_accepts_cc0_by_and_public_domain(self):
        self.assertTrue(generator._commons_license_allowed("CC0","https://creativecommons.org/publicdomain/zero/1.0/"))
        self.assertTrue(generator._commons_license_allowed("CC BY-SA 4.0","https://creativecommons.org/licenses/by-sa/4.0/"))
        self.assertTrue(generator._commons_license_allowed("Public domain","https://commons.wikimedia.org/wiki/Commons:Licensing"))

    def test_commons_rejects_nc_nd_and_missing_url(self):
        self.assertFalse(generator._commons_license_allowed("CC BY-NC 4.0","https://creativecommons.org/licenses/by-nc/4.0/"))
        self.assertFalse(generator._commons_license_allowed("CC BY-ND 4.0","https://creativecommons.org/licenses/by-nd/4.0/"))
        self.assertFalse(generator._commons_license_allowed("CC BY 4.0",""))


if __name__ == "__main__":
    unittest.main()
