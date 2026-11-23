# Nūr Media — cinematic visual strategy

**Status:** Approved direction; Stage 1 implemented on the feature branch (pending CI and merge); full redesign remains in progress  
**Scope:** Social video and supporting editorial graphics produced by Nūr Media Production

## 1. Creative direction

Nūr Media's visual identity is **cinematic**. Each piece should feel like a deliberately directed short film: human, emotionally legible, visually composed and grounded in the story. Cinematic does not mean dark, dramatic for its own sake, expensive-looking effects, or constant camera movement.

The strategy combines the previously selected visual ideas with the latest decisions. They are complementary parts of one visual grammar:

1. **Cinematic identity** sets the overall visual language: lighting, framing, pacing, atmosphere, camera perspective and emotional progression.
2. **Bento-grid and modular composition** organise information into purposeful visual modules. In video these may become animated panels, split compositions, sequential cards or modular editorial layouts—not merely screenshots of an app interface.
3. **3D glassmorphism and tactile surrealism** add selective depth, dimensional objects, translucent surfaces and carefully chosen visual metaphors. Use only when they clarify or strengthen the story.
4. **Brutalist and hyperbold typography** creates decisive editorial hierarchy, strong hooks and readable key statements. Typography must remain legible on a phone and must not obscure faces or important action.
5. **Balanced stock footage** uses real footage when it is the most truthful and useful way to show a scene, while making room for original generated imagery, designed motion graphics and mixed-media treatments.
6. **Consistent character continuity** preserves a character's recognisable identity and visual details across scenes whenever a story uses a recurring character.

Do not force all six elements into every scene. The visual director should choose the treatment that best serves the story.

## 2. Cinematic direction

- Begin with a meaningful human moment, action or visual question; do not begin with a logo animation by default.
- Use purposeful shot progression: establish, develop, reframe or reveal, then resolve.
- Vary shot scale and camera angle to create editorial rhythm. Movement should reveal information or add feeling, not exist as decoration.
- Prefer believable environments, naturalistic light and coherent physical details. Use stylised or surreal imagery deliberately, not as generic filler.
- Let scenes breathe. Avoid constant transitions, overlays, zooms and animated accents.
- Preserve natural source-footage colour. Nūr branding belongs in considered typography, framing, graphic elements and selected colour accents—not an indiscriminate green tint.
- A cinematic sequence may be documentary, designed, mixed-media or stylised. The treatment must remain consistent with the subject and the truth of the story.

## 3. Balanced visual-source policy

Stock footage is neither the automatic default nor something to avoid categorically.

Choose the source per scene:

| Source | Use when | Guardrails |
|---|---|---|
| Licensed stock video or photography | A real-world action, place or human moment is best communicated with genuine footage | Check relevance, framing, licence, creator/source metadata, representation and whether the same asset or performer can support continuity |
| AI-generated still or video | A specific scene is unavailable, a coherent visual world is needed, or a fictional character must be directed consistently | Label and record AI-generated media accurately; review anatomy, artefacts, likeness, rights and provider terms |
| Original motion graphics / 2D or 3D design | Explaining a process, visualising an abstract idea, or creating a distinctive transition or metaphor | Keep the design purposeful, readable and visually connected to the film |
| Hybrid composition | Real footage benefits from a designed information layer or a restrained surreal/editorial element | Preserve the source scene's integrity; overlays must not mislead or hide important action |

The editorial plan should select a preferred source type for each scene and allow a documented fallback. A fallback must not silently turn a character-led scene into unrelated stock footage. If a suitable source is unavailable, use an honest designed visual or revise the scene.

All external assets must retain available provider, asset ID, creator, source page and licence metadata. Human review remains mandatory. Do not add a paid provider or make a paid request without explicit approval and a verified cost configuration.

## 4. Character continuity

Character continuity means more than repeating a textual description. When a story intentionally uses a recurring character, preserve:

- Face and overall identity, age presentation and other non-sensitive visible characteristics appropriate to the fictional role.
- Hair, clothing, accessories and other defining visual details.
- Setting, time of day, lighting direction and colour treatment unless the story intentionally changes them.
- Physical plausibility, screen direction and action progression between shots.
- The same character identity across all scenes in one video and across later episodes when the editorial plan explicitly reuses that character.

### Required workflow for a recurring character

1. Create a character brief and visual reference sheet before generating the scene sequence.
2. Record a stable, non-personal character ID and the approved reference asset in the production manifest.
3. Pass the reference image or an equivalent supported identity reference to every provider call that needs to reproduce the character.
4. Review all scene outputs together, not as isolated images. Reject identity drift and continuity errors.
5. If a provider cannot accept reference images or cannot maintain identity reliably, do not claim consistent character generation. Use a coherent alternative such as a single continuous clip, licensed footage with a verified matching performer, a non-identifying point of view, or designed illustration.

A stock search result cannot guarantee the same performer across separate clips. Text-only prompt continuity is not proof of visual identity continuity. Character references should be stored and handled with privacy and rights in mind; do not use a real person's likeness without appropriate permission.

Not every Nūr video needs a named or recurring character. Use character continuity when it improves the story, not as a forced template.

## 5. Composition, typography and depth

### Bento and modular layouts
- Use a clear primary focal area and a small number of supporting modules.
- Animate modules only when the movement explains sequence, contrast, progress or choice.
- Keep safe margins for vertical 9:16 delivery and platform interface overlays.
- Do not turn every video into a grid. Full-frame cinematic scenes remain a valid and often preferable treatment.

### Typography
- Use hyperbold type for short hooks, decisive phrases and key statements; use restrained supporting type for explanation.
- Establish a clear hierarchy between hook, scene message and supporting detail.
- Keep line lengths short, contrast strong and text readable at typical mobile size.
- Avoid repeating the same lower-third caption treatment in every scene when a more natural editorial placement is possible.
- Never cover a face, essential gesture or story-relevant object with text.

### Glass, 3D and tactile surrealism
- Use glass surfaces, dimensional forms, depth and tactile materials as accents with a clear narrative purpose.
- Maintain believable lighting, shadows, reflections and perspective.
- Avoid excessive glow, floating interface clutter, generic gradients and effects that make the work look like a template.
- These treatments should complement documentary scenes rather than compete with them.

## 6. Nūr brand and editorial safeguards

Retain the established palette:
- Primary emerald: `#0B5D3B`
- Deep forest: `#064E3B`
- Warm ivory: `#F5F0E1`
- Muted gold: `#D4AF37`
- Charcoal: `#1C1C1C`
- Near black: `#080808`
- Earth bronze: `#A68A64`

Use colour as a recognisable signature, not a filter applied to every source image.

The visual strategy must preserve Nūr's core principles:
- Privacy-first and user-controlled.
- No shame, guilt, humiliation, fear-based messaging or manipulative urgency.
- No fabricated testimonials, statistics, religious quotations or app capabilities.
- Respectful and truthful representation of people and behaviour.
- AI-generated scenes must not be presented as documentary footage.
- No automatic public publishing. Existing human approval and rights review remain in force.

## 7. Production workflow target

The intended production flow is:

1. **Story and audience intent:** define the human insight, story arc and practical payoff.
2. **Visual direction:** choose cinematic treatment, composition, source type, character use and shot progression per scene.
3. **Character preparation:** create or load approved references only when recurring characters are required.
4. **Asset acquisition or generation:** use the chosen source and record provenance, provider and reference metadata.
5. **Scene assembly:** render footage, stills, modular graphics, typography, depth treatments and motion with consistent visual rules.
6. **Continuity and quality review:** inspect the full sequence for story coherence, character identity, visual quality, readability, rights and representation.
7. **Human approval:** review the rendered video and supporting graphic on a phone before publication.

## 8. Current implementation audit (stabilisation branch)

The following is an inspection of the existing code and documentation, not a claim that the revised strategy has been implemented.

### Existing foundations
- `nur_generator.py` already creates a four-scene Hook → Development → Re-hook → Payoff story.
- `visual_continuity.py` provides scene-position directions that encourage a coherent visual world and a meaningful progression.
- `visual_prompting.py` composes scene prompts with camera direction, movement, story beat and sequence direction.
- `visual_providers.py` supports optional Gemini-generated still images and Pixabay stock photos/video; Wikimedia Commons and local illustration are existing fallbacks in the generator.
- `media_quality.py` provides vertical scene frames and overlays, tactile collage caption treatments, photo finishing, FFmpeg transitions and narration processing.
- `nur_generator.py` renders 9:16 scenes and a 4:5 supporting poster. Production manifests, editorial quality checks and a human-review checklist are also present.

### Stage 1 implementation (feature branch; pending CI and merge)
- Added `visual_direction.py` as a provider-independent schema for per-scene source, composition, depth and typography choices.
- Added a backward-compatible four-scene default mix: stock video, generated still, stock video, designed visual. Explicit editorial choices override these defaults.
- The generator now attempts Pixabay video only for scenes whose source preference is `stock_video`; other scenes follow their selected still/design path. A missing stock-video clip falls back to the existing still-image chain rather than triggering another stock-video search.
- Added recurring fictional-character profiles in `video.characters` and stable scene references through `character_ids`. The same visual description is passed into generation prompts for each scene using that character.
- The production run manifest now records the selected visual direction, character IDs, source preferences and continuity limitations.
- Composition and depth choices are included in prompt direction where relevant. Typography treatment is recorded as editorial intent; the renderer does not yet implement the new hyperbold type system.
- The provider cannot currently consume character reference images. Continuity is **text-guided only**, not guaranteed. The manifest explicitly records this limitation and flags stock scenes where the same performer is unverified.

### Remaining gaps against the approved direction
- **Bento / modular composition:** the schema and prompt guidance now support the choice, but the renderer does not yet build animated bento panels or modular layouts.
- **Glassmorphism / 3D:** the schema and prompt hints support selective depth treatments; there is no dedicated 3D or glass scene-rendering implementation yet.
- **Brutalist / hyperbold typography:** the scene plan now selects a typography treatment, but the current renderer still uses its existing caption and masthead treatment.
- **Reference-based character continuity:** no provider reference-image input, character-sheet storage or automated identity comparison is integrated. Text prompts alone cannot guarantee the same face.
- **Motion accent:** the current `motion_accent_filter` returns fixed drawbox coordinates. It does not implement the travelling animated accent described in parts of the visual-quality documentation. The documentation and implementation should be reconciled before relying on that claim.
- **Rendered proof:** unit tests validate mechanics, not the artistic quality or continuity of a complete generated video. A fresh output still needs human inspection.

### Test/documentation observation
The inspected `tests/test_media_quality.py` contains a collage-style test after the module's `if __name__ == "__main__": unittest.main()` block, indented inside that block rather than inside the test class. Under normal unittest discovery that test is not discovered. This should be corrected when the renderer is next changed; it is not changed by this documentation-only update.

## 9. Implementation sequence

1. <u>Stage 1 — per-scene visual direction and continuity metadata:</u> implemented on the current feature branch; CI and merge are pending.
2. **Reference-based character continuity:** add provider reference-image support only after a provider capability and cost review. Until then, text-guided continuity remains explicitly limited.
3. **Composition and typography prototypes:** implement one controlled bento composition and one hyperbold typography treatment, then selective glass/tactile depth elements.
4. **Cinematic scene rendering:** integrate treatments without sacrificing legibility, source integrity, restrained motion or the existing 9:16 output.
5. **Tests and visual QA:** cover schema compatibility, source selection, continuity metadata, fallback behaviour, rendering and mobile-safe text. Inspect a real four-scene output before broad rollout.

Do not combine this work with a provider migration or enable Agnes/other paid APIs. Provider integration and pricing verification are separate decisions.

## 10. Acceptance criteria

A pilot video should pass all of the following before the redesign is considered successful:

- The film feels intentionally directed and visually coherent from first frame to payoff.
- Stock, generated and designed visuals are balanced according to scene intent, not a blanket source preference.
- Recurring characters remain recognisable across scenes, or the plan uses an explicit alternative when reference continuity is unsupported.
- Bento, glass/3D and hyperbold typography are used selectively and do not become visual clutter.
- Every text element is readable on a phone and respects safe margins.
- Source footage remains truthful and natural; generated content is correctly labelled in the asset manifest.
- No unapproved paid API calls, new credentials or automatic publishing are introduced.
- Human review confirms story relevance, visual quality, rights, privacy and Nūr's non-shaming philosophy.

**Completion rule:** passing unit tests is necessary but insufficient. The revised visual system is not complete until a fresh rendered pilot has been reviewed and accepted.
