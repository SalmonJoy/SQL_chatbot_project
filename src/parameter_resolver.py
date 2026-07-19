from __future__ import annotations

import re
import sqlite3
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import CONFIG, AppConfig


MONTHS = {
    "jan": "01",
    "january": "01",
    "feb": "02",
    "february": "02",
    "mar": "03",
    "march": "03",
    "apr": "04",
    "april": "04",
    "may": "05",
    "jun": "06",
    "june": "06",
    "jul": "07",
    "july": "07",
    "aug": "08",
    "august": "08",
    "sep": "09",
    "sept": "09",
    "september": "09",
    "oct": "10",
    "october": "10",
    "nov": "11",
    "november": "11",
    "dec": "12",
    "december": "12",
}


COUNTRY_ALIASES = {
    "america": "USA",
    "u s": "USA",
    "u s a": "USA",
    "united states": "USA",
    "united states of america": "USA",
    "us": "USA",
    "usa": "USA",
    "uk": "United Kingdom",
    "u k": "United Kingdom",
    "great britain": "United Kingdom",
    "britain": "United Kingdom",
}


GENRE_ALIASES = {
    "r and b": "R&B/Soul",
    "r b": "R&B/Soul",
    "rnb": "R&B/Soul",
    "hip hop": "Hip Hop/Rap",
    "hiphop": "Hip Hop/Rap",
    "dance": "Electronica/Dance",
    "electronic": "Electronica/Dance",
    "electronica": "Electronica/Dance",
    "scifi": "Sci Fi & Fantasy",
    "sci fi": "Sci Fi & Fantasy",
    "sci-fi": "Sci Fi & Fantasy",
}


ARTIST_ALIASES = {
    "rem": "R.E.M.",
}


@dataclass(frozen=True)
class ParameterResolution:
    status: str
    parameters: dict[str, Any]
    required_parameters: list[dict[str, Any]]
    missing_parameters: list[str]
    invalid_parameters: list[dict[str, Any]]
    ambiguous_parameters: list[dict[str, Any]]
    messages: list[str]

    @property
    def can_execute(self) -> bool:
        return self.status in {"not_required", "resolved"}

    def to_log(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "parameters": self.parameters,
            "required_parameters": self.required_parameters,
            "missing_parameters": self.missing_parameters,
            "invalid_parameters": self.invalid_parameters,
            "ambiguous_parameters": self.ambiguous_parameters,
            "messages": self.messages,
        }


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(character for character in normalized if not unicodedata.combining(character))
    ascii_text = ascii_text.lower()
    ascii_text = re.sub(r"[^a-z0-9]+", " ", ascii_text)
    return re.sub(r"\s+", " ", ascii_text).strip()


def phrase_matches(text: str, phrase: str) -> bool:
    if not phrase:
        return False
    return re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", text) is not None


class ParameterResolver:
    def __init__(self, config: AppConfig = CONFIG) -> None:
        self.config = config
        self.available_years = self._fetch_values("SELECT DISTINCT strftime('%Y', InvoiceDate) FROM Invoice")
        self.available_months = self._fetch_values("SELECT DISTINCT strftime('%Y-%m', InvoiceDate) FROM Invoice")
        self.available_countries = self._fetch_values(
            """
            SELECT DISTINCT Country FROM Customer WHERE Country IS NOT NULL
            UNION
            SELECT DISTINCT BillingCountry FROM Invoice WHERE BillingCountry IS NOT NULL
            """
        )
        self.available_genres = self._fetch_values("SELECT Name FROM Genre")
        self.available_artists = self._fetch_values("SELECT Name FROM Artist WHERE Name IS NOT NULL")

    def _fetch_values(self, sql: str) -> set[str]:
        db_path = Path(self.config.sqlite_path).resolve()
        connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            return {str(row[0]) for row in connection.execute(sql) if row[0] is not None}
        finally:
            connection.close()

    def resolve(self, repository_entry: dict[str, Any], question: str) -> ParameterResolution:
        required_parameters = repository_entry.get("parameters", [])
        if not required_parameters:
            return ParameterResolution("not_required", {}, [], [], [], [], [])

        values: dict[str, Any] = {}
        missing: list[str] = []
        invalid: list[dict[str, Any]] = []
        ambiguous: list[dict[str, Any]] = []
        messages: list[str] = []

        for parameter in required_parameters:
            name = parameter["name"]
            parameter_type = parameter["type"]
            result = self._resolve_one(parameter_type, question)
            if result["status"] == "resolved":
                values[name] = result["value"]
                continue
            if result["status"] == "missing":
                missing.append(name)
            elif result["status"] == "invalid":
                invalid.append({"name": name, **result})
            elif result["status"] == "ambiguous":
                ambiguous.append({"name": name, **result})
            messages.append(result["message"])

        status = "resolved"
        if missing:
            status = "missing"
        if invalid:
            status = "invalid"
        if ambiguous:
            status = "ambiguous"

        return ParameterResolution(
            status=status,
            parameters=values,
            required_parameters=required_parameters,
            missing_parameters=missing,
            invalid_parameters=invalid,
            ambiguous_parameters=ambiguous,
            messages=messages,
        )

    def _resolve_one(self, parameter_type: str, question: str) -> dict[str, Any]:
        if parameter_type == "year":
            return self._resolve_year(question)
        if parameter_type == "month":
            return self._resolve_month(question)
        if parameter_type == "country":
            return self._resolve_named_value(question, self.available_countries, COUNTRY_ALIASES, "country")
        if parameter_type == "genre_name":
            return self._resolve_named_value(question, self.available_genres, GENRE_ALIASES, "genre")
        if parameter_type == "artist_name":
            return self._resolve_named_value(question, self.available_artists, ARTIST_ALIASES, "artist")
        return {
            "status": "invalid",
            "value": None,
            "message": f"Unsupported parameter type: {parameter_type}",
        }

    def _resolve_year(self, question: str) -> dict[str, Any]:
        years = sorted(set(re.findall(r"\b(?:19|20)\d{2}\b", question)))
        if not years:
            return {"status": "missing", "value": None, "message": "Please include a four-digit year."}
        if len(years) > 1:
            return {
                "status": "ambiguous",
                "value": None,
                "candidates": years,
                "message": f"Please ask for one year at a time. Found: {', '.join(years)}.",
            }
        year = years[0]
        if year not in self.available_years:
            return {
                "status": "invalid",
                "value": year,
                "allowed_values": sorted(self.available_years),
                "message": f"Year {year} is not present in the invoice data.",
            }
        return {"status": "resolved", "value": year, "message": f"Resolved year={year}."}

    def _resolve_month(self, question: str) -> dict[str, Any]:
        direct_months = sorted(
            {
                f"{match.group(1)}-{int(match.group(2)):02d}"
                for match in re.finditer(r"\b((?:19|20)\d{2})[-/](0?[1-9]|1[0-2])\b", question)
            }
        )
        if direct_months:
            return self._validate_single_month(direct_months)

        normalized = normalize_text(question)
        month_values = sorted(
            {
                MONTHS[token]
                for token in re.findall(r"[a-z]+", normalized)
                if token in MONTHS
            }
        )
        years = sorted(set(re.findall(r"\b(?:19|20)\d{2}\b", question)))

        if not month_values or not years:
            return {
                "status": "missing",
                "value": None,
                "message": "Please include a specific month and year, for example December 2025 or 2025-12.",
            }
        if len(month_values) > 1 or len(years) > 1:
            return {
                "status": "ambiguous",
                "value": None,
                "candidates": [f"{year}-{month}" for year in years for month in month_values],
                "message": "Please ask for one month at a time.",
            }
        return self._validate_single_month([f"{years[0]}-{month_values[0]}"])

    def _validate_single_month(self, months: list[str]) -> dict[str, Any]:
        if len(months) > 1:
            return {
                "status": "ambiguous",
                "value": None,
                "candidates": months,
                "message": "Please ask for one month at a time.",
            }
        month = months[0]
        if month not in self.available_months:
            return {
                "status": "invalid",
                "value": month,
                "allowed_values": sorted(self.available_months),
                "message": f"Month {month} is not present in the invoice data.",
            }
        return {"status": "resolved", "value": month, "message": f"Resolved month={month}."}

    def _resolve_named_value(
        self,
        question: str,
        allowed_values: set[str],
        aliases: dict[str, str],
        label: str,
    ) -> dict[str, Any]:
        normalized_question = normalize_text(question)
        candidates: list[tuple[int, str, str]] = []

        for value in allowed_values:
            normalized_value = normalize_text(value)
            if phrase_matches(normalized_question, normalized_value):
                candidates.append((len(normalized_value), value, normalized_value))

        for alias, value in aliases.items():
            if value in allowed_values and phrase_matches(normalized_question, normalize_text(alias)):
                candidates.append((len(normalize_text(alias)), value, alias))

        if not candidates:
            return {
                "status": "missing",
                "value": None,
                "allowed_values": sorted(allowed_values),
                "message": f"Please include a valid {label}.",
            }

        candidates.sort(key=lambda item: (-item[0], item[1]))
        best_length = candidates[0][0]
        best_values = sorted({value for length, value, _ in candidates if length == best_length})
        if len(best_values) > 1:
            return {
                "status": "ambiguous",
                "value": None,
                "candidates": best_values,
                "message": f"Please choose one {label}: {', '.join(best_values)}.",
            }

        value = best_values[0]
        return {"status": "resolved", "value": value, "message": f"Resolved {label}={value}."}
