from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from services.gemini_service import (
    _build_prompt,
    get_procrastination_excuse,
    FALLBACK_EXCUSES,
    POSTPONE_HOURS,
)


# ── _build_prompt ────────────────────────────────────────────────────────────

class TestBuildPrompt:
    def test_contains_task_title(self):
        prompt = _build_prompt("Fix bug #42", "01/06/2025 10:00")
        assert "Fix bug #42" in prompt

    def test_contains_scheduled_date(self):
        prompt = _build_prompt("Deploy", "15/07/2025 14:30")
        assert "15/07/2025 14:30" in prompt

    def test_asks_for_portuguese(self):
        prompt = _build_prompt("x", "now")
        assert "português" in prompt.lower()


# ── get_procrastination_excuse ───────────────────────────────────────────────

class TestGetProcrastinationExcuse:
    @pytest.mark.asyncio
    async def test_returns_gemini_excuse_on_success(self):
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "  Desculpa genial  "
        mock_model.generate_content.return_value = mock_response

        with (
            patch("services.gemini_service.genai") as mock_genai,
            patch("services.gemini_service.random") as mock_random,
        ):
            mock_genai.GenerativeModel.return_value = mock_model
            mock_random.choice.return_value = 48
            mock_random.randint.return_value = 93

            result = await get_procrastination_excuse(
                "Deploy", datetime(2025, 6, 1, 10, 0)
            )

        assert result["excuse"] == "Desculpa genial"
        assert result["suggested_postpone_hours"] == 48
        assert result["confidence"] == 93

    @pytest.mark.asyncio
    async def test_falls_back_on_api_error(self):
        with (
            patch("services.gemini_service.genai") as mock_genai,
            patch("services.gemini_service.random") as mock_random,
        ):
            mock_genai.configure.side_effect = Exception("API down")
            fallback = FALLBACK_EXCUSES[0]
            mock_random.choice.side_effect = lambda seq: (
                48 if seq is POSTPONE_HOURS else fallback
            )
            mock_random.randint.return_value = 90

            result = await get_procrastination_excuse("Task", datetime(2025, 6, 1))

        assert result["excuse"] == fallback

    @pytest.mark.asyncio
    async def test_uses_utcnow_when_no_scheduled_at(self):
        with (
            patch("services.gemini_service.genai") as mock_genai,
            patch("services.gemini_service.random") as mock_random,
        ):
            mock_genai.configure.side_effect = Exception("skip")
            mock_random.choice.side_effect = lambda seq: (
                24 if seq is POSTPONE_HOURS else FALLBACK_EXCUSES[0]
            )
            mock_random.randint.return_value = 90

            result = await get_procrastination_excuse("Task")

        assert "suggested_new_date" in result
        assert result["suggested_postpone_hours"] == 24

    @pytest.mark.asyncio
    async def test_result_keys(self):
        with (
            patch("services.gemini_service.genai") as mock_genai,
            patch("services.gemini_service.random") as mock_random,
        ):
            mock_genai.configure.side_effect = Exception("skip")
            mock_random.choice.side_effect = lambda seq: (
                24 if seq is POSTPONE_HOURS else FALLBACK_EXCUSES[0]
            )
            mock_random.randint.return_value = 95

            result = await get_procrastination_excuse("T")

        assert set(result.keys()) == {
            "excuse",
            "suggested_postpone_hours",
            "suggested_new_date",
            "confidence",
        }
