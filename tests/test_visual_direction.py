import unittest

from visual_direction import (
    build_character_direction,
    build_visual_direction_manifest,
    normalise_video_visual_direction,
)


class VisualDirectionTests(unittest.TestCase):
    def video(self):
        return {
            "scenes": [
                {"beat": "HOOK / OPEN LOOP"},
                {"beat": "DEVELOPMENT"},
                {"beat": "RE-HOOK"},
                {"beat": "PAYOFF"},
            ]
        }

    def test_legacy_scenes_receive_balanced_safe_source_defaults(self):
        video = normalise_video_visual_direction(self.video())
        sources = [scene["visual_source"] for scene in video["scenes"]]
        self.assertEqual(
            sources,
            ["stock_video", "generated_still", "stock_video", "designed_visual"],
        )
        self.assertEqual(sources.count("stock_video"), 2)
        self.assertIn("bento_modular", [s["composition"] for s in video["scenes"]])
        self.assertIn("hyperbold_brutalist", [s["typography_treatment"] for s in video["scenes"]])

    def test_explicit_scene_direction_is_preserved(self):
        video = self.video()
        video["scenes"][0]["visual_source"] = "stock_photo"
        video["scenes"][0]["composition"] = "hybrid_editorial"
        normalise_video_visual_direction(video)
        self.assertEqual(video["scenes"][0]["visual_source"], "stock_photo")
        self.assertEqual(video["scenes"][0]["composition"], "hybrid_editorial")

    def test_known_legacy_source_alias_is_normalised(self):
        video = self.video()
        video["scenes"][0]["visual_source"] = "stock_footage"
        normalise_video_visual_direction(video)
        self.assertEqual(video["scenes"][0]["visual_source"], "stock_video")

    def test_unknown_source_is_rejected(self):
        video = self.video()
        video["scenes"][0]["visual_source"] = "paid_video_api"
        with self.assertRaisesRegex(ValueError, "Unknown visual_source"):
            normalise_video_visual_direction(video)

    def test_character_ids_must_be_unique_and_descriptive(self):
        video = self.video()
        video["characters"] = [
            {"id": "main_person", "visual_description": "A fictional adult with short dark hair and a navy jacket."},
            {"id": "main_person", "visual_description": "A different fictional adult with long hair and a grey coat."},
        ]
        with self.assertRaisesRegex(ValueError, "Duplicate character id"):
            normalise_video_visual_direction(video)

    def test_scene_character_ids_must_resolve(self):
        video = self.video()
        video["scenes"][0]["character_ids"] = ["unknown_person"]
        with self.assertRaisesRegex(ValueError, "unknown character id"):
            normalise_video_visual_direction(video)

    def test_character_description_is_reused_in_prompt_direction(self):
        video = self.video()
        video["characters"] = [
            {"id": "main_person", "visual_description": "A fictional adult with short dark hair and a navy jacket."}
        ]
        video["scenes"][0]["character_ids"] = ["main_person"]
        video["scenes"][1]["character_ids"] = ["main_person"]
        normalise_video_visual_direction(video)
        first = build_character_direction(video["scenes"][0], video["characters"])
        second = build_character_direction(video["scenes"][1], video["characters"])
        self.assertEqual(first, second)
        self.assertIn("short dark hair", first)
        self.assertIn("TEXT-GUIDED CHARACTER CONTINUITY", first)

    def test_recurring_character_uses_still_chain_instead_of_local_illustration(self):
        video = self.video()
        video["characters"] = [
            {"id": "main_person", "visual_description": "A fictional adult with short dark hair and a navy jacket."}
        ]
        video["scenes"][3]["character_ids"] = ["main_person"]
        normalise_video_visual_direction(video)
        self.assertEqual(video["scenes"][3]["visual_source"], "generated_still")
        self.assertIn("recurring character", video["scenes"][3]["source_adjustment"])

    def test_manifest_discloses_text_only_continuity_and_stock_risk(self):
        video = self.video()
        video["characters"] = [
            {"id": "main_person", "visual_description": "A fictional adult with short dark hair and a navy jacket."}
        ]
        video["scenes"][0]["character_ids"] = ["main_person"]
        normalise_video_visual_direction(video)
        manifest = build_visual_direction_manifest(video)
        self.assertEqual(manifest["character_continuity_mode"], "text_guided_only")
        self.assertFalse(manifest["provider_reference_image_support"])
        self.assertTrue(manifest["scenes"][0]["same_performer_unverified"])
        self.assertTrue(manifest["limitations"])


if __name__ == "__main__":
    unittest.main()
