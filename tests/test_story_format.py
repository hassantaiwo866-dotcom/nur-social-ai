import unittest
from story_format import validate_story_plan, scene_defaults_for_beat, VISUAL_STYLES, complete_missing_captions

class StoryFormatTests(unittest.TestCase):
    def plan(self):
        beats=("HOOK / OPEN LOOP","DEVELOPMENT","RE-HOOK","PAYOFF")
        scenes=[]
        for beat in beats:
            scenes.append({"beat":beat,"voiceover":"Pause and choose one helpful step.","on_screen_text":"Choose one step","image_prompt":beat,**scene_defaults_for_beat({"beat":beat})})
        return {"video":{"visual_style":"hybrid_documentary_collage","scenes":scenes}}

    def test_missing_captions_are_completed(self):
        plan = {
            "graphic": {"headline": "A gentle reset", "subtext": "Pause and choose one step."},
            "video": {"title": "Return to what matters", "scenes": [{"voiceover": "Start small."}]},
        }
        complete_missing_captions(plan)
        self.assertIn("A gentle reset", plan["caption_image"])
        self.assertIn("Start small.", plan["caption_video"])
        self.assertIn("#Nūr", plan["caption_video"])

    def test_valid_story_arc(self):
        validate_story_plan(self.plan()); self.assertEqual(len(VISUAL_STYLES),3)
    def test_wrong_beat_rejected(self):
        plan=self.plan(); plan["video"]["scenes"][2]["beat"]="MIDPOINT"
        with self.assertRaisesRegex(ValueError,"scene 3"): validate_story_plan(plan)
    def test_missing_direction_rejected(self):
        plan=self.plan(); plan["video"]["scenes"][0]["movement"]=""
        with self.assertRaisesRegex(ValueError,"movement"): validate_story_plan(plan)
    def test_payoff_action_required(self):
        plan=self.plan(); plan["video"]["scenes"][3]["voiceover"]="Everything feels complicated."
        with self.assertRaisesRegex(ValueError,"practical next step"): validate_story_plan(plan)
if __name__ == "__main__": unittest.main()
