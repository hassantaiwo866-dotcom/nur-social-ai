import unittest
from brand_tokens import PALETTE_HEX, PRIMARY_EMERALD, DEEP_FOREST, WARM_IVORY, MUTED_GOLD, CHARCOAL, rgb

class BrandTokenTests(unittest.TestCase):
    def test_palette_has_canonical_hex_values(self):
        self.assertEqual(PALETTE_HEX["primary_emerald"], "#0B5D3B")
        self.assertEqual(PALETTE_HEX["deep_forest"], "#064E3B")
        self.assertEqual(PALETTE_HEX["warm_ivory"], "#F5F0E1")
        self.assertEqual(PALETTE_HEX["muted_gold"], "#D4AF37")
        self.assertEqual(PALETTE_HEX["charcoal"], "#1C1C1C")
    def test_rgb_values_match_hex(self):
        self.assertEqual(PRIMARY_EMERALD, (11, 93, 59))
        self.assertEqual(DEEP_FOREST, (6, 78, 59))
        self.assertEqual(WARM_IVORY, (245, 240, 225))
        self.assertEqual(MUTED_GOLD, (212, 175, 55))
        self.assertEqual(CHARCOAL, (28, 28, 28))
    def test_rgb_rejects_unknown_palette_key(self):
        with self.assertRaises(KeyError): rgb("not-a-brand-colour")
if __name__ == "__main__": unittest.main()
