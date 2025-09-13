from __future__ import annotations

import os
from typing import Any, Dict
import yaml


class Locales:
    def __init__(self, base_dir: str, default_locale: str = "ru") -> None:
        self.base_dir = base_dir
        self.default_locale = default_locale
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _load_locale_file(self, locale: str) -> Dict[str, Any]:
        if locale in self._cache:
            return self._cache[locale]
        path = os.path.join(self.base_dir, f"{locale}.yml")
        if not os.path.isfile(path):
            if locale != self.default_locale:
                return self._load_locale_file(self.default_locale)
            return {}
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        self._cache[locale] = data
        return data

    def t(self, locale: str, key: str, **kwargs: Any) -> str:
        data = self._load_locale_file(locale)
        parts = key.split(".")
        node: Any = data
        for part in parts:
            if not isinstance(node, dict) or part not in node:
                return key
            node = node[part]
        if not isinstance(node, str):
            return key
        try:
            return node.format(**kwargs)
        except Exception:
            return node
