"""Localization helpers for the CatLink integration."""

import json
import os
from functools import lru_cache
from typing import Any, Iterable

LANGUAGE_FILE_MAP = {
    "zh_CN": "zh-Hans.json",
}
DEFAULT_LANGUAGE_FILE = "en.json"


def _resolve_language_file(language: str) -> str:
    """Return the filename for the given language."""
    return LANGUAGE_FILE_MAP.get(language, DEFAULT_LANGUAGE_FILE)


@lru_cache(maxsize=None)
def _load_translations(language: str) -> dict[str, Any]:
    """Load translations for the given language with fallback to English."""
    filename = _resolve_language_file(language)
    translations_dir = os.path.join(os.path.dirname(__file__), "translations")
    path = os.path.join(translations_dir, filename)

    try:
        with open(path, encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        if filename != DEFAULT_LANGUAGE_FILE:
            return _load_translations("en_GB")
        raise


class TranslationManager:
    """Helper class to translate entity metadata and values."""

    def __init__(self, language: str) -> None:
        self.language = language
        self._translations = _load_translations(language)

    def translate_entity_name(
        self, entity_type: str | None, translation_key: str
    ) -> str | None:
        """Return the translated entity name if available."""
        if not entity_type:
            return None

        entity_translations = self._translations.get("entity", {}).get(entity_type, {})
        entry = entity_translations.get(translation_key)
        if isinstance(entry, dict):
            return entry.get("name")
        return None

    def translate_selector_option(
        self, translation_key: str | None, value: str | None
    ) -> str | None:
        """Translate a selector option."""
        if not translation_key or not isinstance(value, str):
            return None

        return (
            self._translations.get("selector", {})
            .get(translation_key, {})
            .get("options", {})
            .get(value)
        )

    def translate_state(self, translation_key: str | None, value: Any) -> Any:
        """Translate a state value if possible."""
        if isinstance(value, str):
            translated = self.translate_selector_option(translation_key, value)
            if translated is not None:
                return translated
        return value

    def get_selector_option_translations(
        self, translation_key: str | None, options: Iterable[str]
    ) -> tuple[list[str], dict[str, str], dict[str, str]]:
        """Return localized options and mapping dictionaries."""
        localized_options: list[str] = []
        native_to_localized: dict[str, str] = {}
        localized_to_native: dict[str, str] = {}

        for option in options:
            if not isinstance(option, str):
                localized = option
            else:
                translated = self.translate_selector_option(translation_key, option)
                localized = translated if translated is not None else option

            localized_options.append(localized)

            if isinstance(option, str):
                native_to_localized[option] = localized
                localized_to_native.setdefault(localized, option)

        return localized_options, native_to_localized, localized_to_native
