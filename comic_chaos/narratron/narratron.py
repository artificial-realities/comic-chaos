"""NARRATRON - The comic creation engine.

This module contains the Narratron AI engine that orchestrates comic creation.
The LLM has creative control over the story, dynamically introducing locations
and characters while maintaining consistency with the comic's blueprint and rules.
"""

import os
from typing import Any, Optional, Dict, List

from openai import OpenAI
from pydantic import BaseModel

from pathlib import Path

from ..state.comic_state import (
    ComicState,
    RenderState,
)
from ..state.static_config import StaticConfig
from ..prompt_loader import load_prompt
from ..text_sanitizer import sanitize_text, sanitize_parsed_response

from .models import (
    NarratronResponseSchema,
    OpeningSequenceSchema,
    FALLBACK_RESPONSE,
    NarratronResponse,
    TitleCardPanel,
    OpeningSequenceResponse,
)

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


class Narratron:
    """The AI engine that orchestrates comic creation."""

    _NORWEGIAN_INSTRUCTION = (
        "\n\nLANGUAGE REQUIREMENT:"
        "\n- USER-FACING TEXT in Norwegian (Bokmål): All \"placeholder\" text and all "
        "\"text\" in auto-panels (pre-filled dialogue and narration) and \"title_treatment\" "
        "MUST be written in Norwegian (Bokmål)."
        "\n- INTERNAL FIELDS in English: scene_description, rolling_summary_update, "
        "short_term_narrative, long_term_narrative, and all scene_summary fields "
        "(scene_setting, characters_present, current_action) MUST remain in English. "
        "These feed into image generation and internal state — English keeps them consistent."
        "\n\nENCODING REQUIREMENT: Write Norwegian characters (æ, ø, å, Æ, Ø, Å) and "
        "all other special characters (€, é, ü, etc.) as literal UTF-8 characters "
        "directly in the JSON string values. Do NOT use Unicode escape sequences like "
        "\\u00e6 — write the actual character æ instead. Never output null bytes (\\u0000), "
        "raw hexadecimal byte sequences, or incomplete escape sequences."
    )

    def __init__(
        self,
        config: StaticConfig,
        api_key: Optional[str] = None,
        language: str = "no",
    ) -> None:
        self.config: StaticConfig = config
        self.client: OpenAI = OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY")
        )
        self.language: str = language

    def _build_system_prompt(self) -> str:
        """Build the system prompt with static comic information only."""
        blueprint = self.config.blueprint
        rules = " | ".join(self.config.blueprint.rules) if self.config.blueprint.rules else "None"

        return load_prompt(
            _PROMPTS_DIR / "narratron.system.md",
            title=blueprint.title,
            visual_style=blueprint.visual_style,
            rules=rules,
        )

    def _call_llm(self, messages: List[Dict[str, str]], response_model: type[BaseModel]) -> Dict[str, Any]:
        """Call the LLM with Structured Outputs and return the parsed response as a dict.

        The response is validated against *response_model* by the API, then
        every string in it is sanitized. Raises if the model refuses or the
        call fails; callers fall back to a safe panel.
        """
        cc = self.config.comic_config
        response = self.client.chat.completions.parse(
            model=cc.llm_model,
            messages=messages,
            temperature=cc.llm_temperature,
            top_p=cc.llm_top_p,
            max_tokens=cc.llm_max_tokens,
            response_format=response_model,
        )
        message = response.choices[0].message
        if message.parsed is None:
            raise ValueError(f"No structured response (refusal: {message.refusal!r})")
        return sanitize_parsed_response(message.parsed.model_dump())

    def _localize_fallback_placeholders(self, response: NarratronResponse) -> None:
        """Replace English fallback placeholders with localized versions."""
        if self.language != "no":
            return
        for panel in response.panels:
            for el in panel.elements:
                if el.get("placeholder") == "What happens next?":
                    el["placeholder"] = "Hva skjer videre?"

    def process_input(
        self, user_input: str, comic_state: ComicState
    ) -> NarratronResponse:
        """Process user input and create the next comic panel."""
        system_prompt = self._build_system_prompt()
        user_message = self._build_user_message(user_input, comic_state)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        try:
            response = NarratronResponse(self._call_llm(messages, NarratronResponseSchema))
        except Exception as e:
            print(f"[NARRATRON] Panel generation failed, using fallback panel: {type(e).__name__}: {e}")
            response = NarratronResponse(FALLBACK_RESPONSE)

        self._localize_fallback_placeholders(response)
        self._apply_state_changes(response, comic_state)

        return response

    def _build_user_message(self, user_input: str, comic_state: ComicState) -> str:
        """Build compact user message with all dynamic context."""
        main_char = f"{comic_state.main_character_name}: {comic_state.main_character_description}"

        # All blueprint characters (so the LLM never forgets species/descriptions)
        all_characters = ""
        if self.config.blueprint.characters and len(self.config.blueprint.characters) > 1:
            char_lines = [
                f"- {c.name}: {c.description}"
                for c in self.config.blueprint.characters[1:]  # Skip main char (already above)
            ]
            all_characters = "OTHER CHARACTERS:\n" + "\n".join(char_lines)

        # Recent panels (compact)
        recent_panels = ""
        if comic_state.narrative.panels:
            panel_lines = []
            for panel in comic_state.get_recent_panels(3):
                narrative = panel.narrative[:150] + "..." if len(panel.narrative) > 150 else panel.narrative
                panel_lines.append(f"P{panel.panel_number}: {narrative}")
            recent_panels = "RECENT:\n" + "\n".join(panel_lines)

        # Format story narrative direction
        story_narrative = ""
        direction = comic_state.narrative.direction
        if direction.short_term or direction.long_term:
            narrative_parts = []
            if direction.short_term:
                narrative_parts.append("SHORT-TERM: " + "; ".join(direction.short_term))
            if direction.long_term:
                narrative_parts.append("LONG-TERM: " + "; ".join(direction.long_term))
            story_narrative = "STORY NARRATIVE:\n" + "\n".join(narrative_parts)

        # Format narrative premise (if defined in blueprint)
        narrative_premise = ""
        if self.config.blueprint.narrative_premise:
            narrative_premise = self.config.blueprint.narrative_premise

        message = load_prompt(
            _PROMPTS_DIR / "panel.user.md",
            main_character=main_char,
            all_characters=all_characters,
            rolling_summary=comic_state.narrative.rolling_summary,
            story_narrative=story_narrative,
            narrative_premise=narrative_premise,
            recent_panels=recent_panels,
            user_input=user_input,
        )

        if self.language == "no":
            message += self._NORWEGIAN_INSTRUCTION

        return message

    def _apply_state_changes(
        self, response: NarratronResponse, comic_state: ComicState
    ) -> None:
        """Apply state changes from the response.

        All text values are sanitized before storing in state to prevent
        encoding corruption from propagating into subsequent LLM prompts.
        """
        # Update the rolling narrative summary
        if response.rolling_summary_update:
            comic_state.narrative.rolling_summary = sanitize_text(
                response.rolling_summary_update
            )

        # Update render state from scene summary for visual generation
        scene_summary = response.scene_summary
        if scene_summary:
            comic_state.render = RenderState(
                scene_setting=sanitize_text(scene_summary.get(
                    "scene_setting", comic_state.render.scene_setting
                )),
                characters_present=[
                    sanitize_text(c) for c in scene_summary.get(
                        "characters_present", comic_state.render.characters_present
                    )
                ],
                current_action=sanitize_text(scene_summary.get(
                    "current_action", comic_state.render.current_action
                )),
            )

        # Update story narrative direction
        if isinstance(response.short_term_narrative, list) and response.short_term_narrative:
            comic_state.narrative.direction.short_term = [
                sanitize_text(s) for s in response.short_term_narrative
            ]
        if isinstance(response.long_term_narrative, list) and response.long_term_narrative:
            comic_state.narrative.direction.long_term = [
                sanitize_text(s) for s in response.long_term_narrative
            ]

    def generate_opening_sequence(
        self, comic_state: ComicState
    ) -> OpeningSequenceResponse:
        """Generate the grand opening sequence: title card + first interactive panel."""
        if not self.config.blueprint:
            raise ValueError("Cannot generate opening without blueprint")

        blueprint = self.config.blueprint

        system_prompt = self._build_system_prompt()

        long_term_narrative_section = ""
        if blueprint.long_term_narrative:
            narrative_str = "; ".join(blueprint.long_term_narrative)
            long_term_narrative_section = f"LONG-TERM NARRATIVE (use these as-is for initial_narrative.long_term): {narrative_str}"

        narrative_premise_section = ""
        if blueprint.narrative_premise:
            narrative_premise_section = f"NARRATIVE PREMISE: {blueprint.narrative_premise}"

        # Use localized title/synopsis so the image model renders the
        # correct language on the title card.
        display_title = (blueprint.title_no or blueprint.title) if self.language == "no" else blueprint.title
        display_synopsis = (blueprint.synopsis_no or blueprint.synopsis) if self.language == "no" else blueprint.synopsis

        user_message = load_prompt(
            _PROMPTS_DIR / "opening_sequence.user.md",
            title=display_title,
            synopsis=display_synopsis,
            visual_style=blueprint.visual_style,
            starting_location=f"{blueprint.starting_location.name}: {blueprint.starting_location.description}",
            main_character=f"{blueprint.main_character.name}: {blueprint.main_character.description}",
            long_term_narrative_section=long_term_narrative_section,
            narrative_premise_section=narrative_premise_section,
        )

        if self.language == "no":
            user_message += self._NORWEGIAN_INSTRUCTION

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        try:
            response = OpeningSequenceResponse.from_raw(self._call_llm(messages, OpeningSequenceSchema))
        except Exception as e:
            print(f"[NARRATRON] Opening sequence failed, using fallback: {type(e).__name__}: {e}")
            response = OpeningSequenceResponse(
                title_card=TitleCardPanel(
                    scene_description=f"A dramatic establishing shot for {display_title}",
                    title_treatment=display_title,
                    atmosphere=display_synopsis,
                ),
                first_panel=NarratronResponse(FALLBACK_RESPONSE),
                initial_narrative={"short_term": [], "long_term": []},
            )

        self._localize_fallback_placeholders(response.first_panel)

        self._apply_state_changes(response.first_panel, comic_state)

        # Apply initial story narrative
        if response.initial_narrative:
            st = response.initial_narrative.get("short_term", [])
            if isinstance(st, list) and st:
                comic_state.narrative.direction.short_term = st
            # Only use LLM's long-term narrative if the blueprint didn't define any
            if not self.config.blueprint.long_term_narrative:
                lt = response.initial_narrative.get("long_term", [])
                if isinstance(lt, list) and lt:
                    comic_state.narrative.direction.long_term = lt

        return response
