import json
import re
import unittest
from pathlib import Path

import nur_generator

CONFIG = Path(__file__).resolve().parent.parent / "brand_config.json"


class BrandConfigTests(unittest.TestCase):
    def test_brand_config_is_valid_json(self):
        json.loads(CONFIG.read_text(encoding="utf-8"))

    def test_generator_loads_real_config_not_the_silent_default(self):
        brand = nur_generator.load_json(CONFIG, {"pillars": ["DEFAULT"]})
        self.assertNotEqual(brand.get("pillars"), ["DEFAULT"])
        self.assertEqual(brand["brand_name"], "Nūr")
        self.assertGreater(len(brand["pillars"]), 1)
        self.assertTrue(brand["tone_rules"])

    def test_palette_values_are_hex_and_emerald_is_primary(self):
        palette = json.loads(CONFIG.read_text(encoding="utf-8"))["palette"]
        for name, value in palette.items():
            self.assertRegex(value, r"^#[0-9A-Fa-f]{6}$", name)
        self.assertEqual(palette["primary_emerald"].upper(), "#0B5D3B")

    def test_non_shaming_rules_are_present(self):
        rules = " ".join(json.loads(CONFIG.read_text(encoding="utf-8"))["tone_rules"]).lower()
        self.assertIn("shame", rules)
        self.assertIn("privacy", rules)


if __name__ == "__main__":
    unittest.main()
