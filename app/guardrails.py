import re
from dataclasses import dataclass, field
from functools import lru_cache

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

ENTITY_LABELS = {
    "EMAIL_ADDRESS": "[REDACTED_EMAIL]",
    "PHONE_NUMBER": "[REDACTED_PHONE]",
    "CREDIT_CARD": "[REDACTED_CARD]",
}

ENTITIES = list(ENTITY_LABELS)

# Reservation dates must never be mistaken for phone numbers.
DATE_SPAN = re.compile(r"\d{4}-\d{2}-\d{2}(?:[ T]\d{1,2}:\d{2})?")

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+|any\s+)?(the\s+)?(previous|prior|above)\s+(instructions|rules|prompts?)",
    r"disregard\s+(all\s+|any\s+)?(the\s+)?(previous|prior|above)",
    r"(reveal|show|print|repeat)\s+(me\s+)?(your|the)\s+(system\s+)?(prompt|instructions)",
    r"you\s+are\s+now\s+",
    r"act\s+as\s+(an?\s+)?(admin|administrator|developer|dan)\b",
    r"jailbreak",
]

BLOCK_MESSAGE = (
    "I can only help with Hyderabad Central Parking questions, "
    "so I can't follow that request."
)
PRIVACY_NOTE = "Note: for your privacy, I removed sensitive details from your message."


@dataclass
class GuardResult:
    allowed: bool
    text: str
    flags: list[str] = field(default_factory=list)


@lru_cache(maxsize=1)
def _analyzer() -> AnalyzerEngine:
    provider = NlpEngineProvider(
        nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
        }
    )
    analyzer = AnalyzerEngine(
        nlp_engine=provider.create_engine(), supported_languages=["en"]
    )
    analyzer.registry.add_recognizer(
        PatternRecognizer(
            supported_entity="EMAIL_ADDRESS",
            name="PermissiveEmailRecognizer",
            patterns=[
                Pattern(
                    "permissive_email",
                    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+\b",
                    0.6,
                )
            ],
        )
    )
    return analyzer


@lru_cache(maxsize=1)
def _anonymizer() -> AnonymizerEngine:
    return AnonymizerEngine()


def _overlaps(result, spans) -> bool:
    return any(result.start < end and result.end > start for start, end in spans)


def redact(text: str) -> tuple[str, list[str]]:
    if not text.strip():
        return text, []

    results = _analyzer().analyze(text=text, language="en", entities=ENTITIES)
    date_spans = [m.span() for m in DATE_SPAN.finditer(text)]
    results = [
        r
        for r in results
        if not (r.entity_type == "PHONE_NUMBER" and _overlaps(r, date_spans))
    ]
    if not results:
        return text, []

    operators = {
        entity: OperatorConfig("replace", {"new_value": label})
        for entity, label in ENTITY_LABELS.items()
    }
    clean = _anonymizer().anonymize(
        text=text, analyzer_results=results, operators=operators
    ).text
    return clean, sorted({r.entity_type for r in results})


def check_input(text: str) -> GuardResult:
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return GuardResult(False, "", ["PROMPT_INJECTION"])
    clean, found = redact(text)
    return GuardResult(True, clean, found)


def check_output(text: str) -> str:
    clean, _ = redact(text)
    return clean