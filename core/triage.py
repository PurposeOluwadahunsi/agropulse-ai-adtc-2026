"""
core/triage.py  (Sprint 4 — upgraded)

Rule-based symptom triage engine for AgroPulse AI.

Improvements over Sprint 2:
    - Distinguishing symptom bonuses (high-specificity symptoms score higher)
    - Alias matching (local names, abbreviations)
    - Confidence explanation (why a disease was selected)
    - Severity pulled directly from vetdb.json
    - Runner-up disease reported for transparency
    - Same external interface — fully backward compatible
"""

from __future__ import annotations

import json
import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

VETDB_PATH           = Path(__file__).parent.parent / "knowledge" / "vetdb.json"
CONFIDENCE_THRESHOLD = 4
DISTINGUISHING_BONUS = 3   # Extra weight for distinguishing symptoms


@dataclass
class TriageResult:
    """
    Result from the triage engine.

    Fields are identical to Sprint 2 plus:
        explanation     — human-readable string explaining the match
        runner_up       — second-best disease name (or None)
        runner_up_score — score of the runner-up
        biosecurity     — list of biosecurity actions from vetdb
        when_to_call_vet — veterinary intervention guidance string
    """
    matched:           bool        = False
    disease_name:      str | None  = None
    disease_id:        str | None  = None
    severity:          str | None  = None
    score:             float       = 0.0
    matched_symptoms:  list[str]   = field(default_factory=list)
    distinguishing_matched: list[str] = field(default_factory=list)
    first_aid:         str         = ""
    treatment:         str         = ""
    prevention:        str         = ""
    biosecurity:       list[str]   = field(default_factory=list)
    when_to_call_vet:  str         = ""
    vet_referral:      bool        = False
    sources:           list[str]   = field(default_factory=list)
    confidence:        str         = "none"
    explanation:       str         = ""
    runner_up:         str | None  = None
    runner_up_score:   float       = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "matched":               self.matched,
            "disease_name":          self.disease_name,
            "disease_id":            self.disease_id,
            "severity":              self.severity,
            "score":                 self.score,
            "matched_symptoms":      self.matched_symptoms,
            "distinguishing_matched": self.distinguishing_matched,
            "first_aid":             self.first_aid,
            "treatment":             self.treatment,
            "prevention":            self.prevention,
            "biosecurity":           self.biosecurity,
            "when_to_call_vet":      self.when_to_call_vet,
            "vet_referral":          self.vet_referral,
            "sources":               self.sources,
            "confidence":            self.confidence,
            "explanation":           self.explanation,
            "runner_up":             self.runner_up,
            "runner_up_score":       self.runner_up_score,
        }


class TriageEngine:
    """
    Loads vetdb.json once and provides fast weighted symptom matching.
    Instantiate once at application startup.
    """

    def __init__(self) -> None:
        self._diseases: list[dict[str, Any]] = []
        self._load_rules()

    def _load_rules(self) -> None:
        if not VETDB_PATH.exists():
            raise FileNotFoundError(
                f"vetdb.json not found at {VETDB_PATH}."
            )
        with open(VETDB_PATH, encoding="utf-8") as f:
            db = json.load(f)
        self._diseases = db.get("diseases", [])
        if not self._diseases:
            raise ValueError("vetdb.json contains no disease entries.")
        logger.info(f"TriageEngine loaded {len(self._diseases)} disease rules.")

    @staticmethod
    def _normalise(text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _score_disease(
        self,
        query_norm: str,
        disease: dict[str, Any],
    ) -> tuple[float, list[str], list[str]]:
        """
        Score a disease against the normalised query.

        Returns:
            (score, matched_symptom_phrases, distinguishing_matched)
        """
        weights:           dict[str, int]  = disease.get("symptom_weights", {})
        symptoms:          list[str]       = disease.get("symptoms", [])
        distinguishing:    list[str]       = disease.get("distinguishing_symptoms", [])
        confidence_kws:    list[str]       = disease.get("confidence_keywords", [])
        aliases:           list[str]       = disease.get("aliases", [])

        distinguishing_set = {self._normalise(d) for d in distinguishing}

        total_score  = 0.0
        matched:     list[str] = []
        dist_matched: list[str] = []

        # Regular symptom matching with weights
        for symptom in symptoms:
            symptom_norm = self._normalise(symptom)
            if symptom_norm in query_norm:
                weight = weights.get(symptom, 1)
                # Add distinguishing bonus
                if symptom_norm in distinguishing_set:
                    weight += DISTINGUISHING_BONUS
                    dist_matched.append(symptom)
                total_score += weight
                matched.append(symptom)

        # Alias matching
        for alias in aliases:
            alias_norm = self._normalise(alias)
            if alias_norm in query_norm and alias not in matched:
                total_score += 3
                matched.append(f"alias:{alias}")

        # Confidence keyword bonus
        for kw in confidence_kws:
            kw_norm = self._normalise(kw)
            if kw_norm in query_norm:
                total_score += 2

        return total_score, matched, dist_matched

    def _build_explanation(
        self,
        disease: dict[str, Any],
        matched: list[str],
        dist_matched: list[str],
        score: float,
        confidence: str,
        runner_up: str | None,
        runner_up_score: float,
    ) -> str:
        """Build a human-readable explanation of why this disease was selected."""
        parts = []

        clean_matched = [s for s in matched if not s.startswith("alias:")]
        aliases_hit   = [s.replace("alias:", "") for s in matched if s.startswith("alias:")]

        if clean_matched:
            parts.append(
                f"The following reported symptoms match {disease['name']}: "
                f"{', '.join(clean_matched)}."
            )
        if dist_matched:
            parts.append(
                f"Particularly significant indicators include: "
                f"{', '.join(dist_matched)} — these are distinguishing symptoms "
                f"strongly associated with {disease['name']}."
            )
        if aliases_hit:
            parts.append(f"Disease name recognised: {', '.join(aliases_hit)}.")

        parts.append(
            f"Match confidence is {confidence} (score {score:.1f})."
        )

        if runner_up and runner_up_score >= CONFIDENCE_THRESHOLD:
            parts.append(
                f"Alternative condition to consider: {runner_up} "
                f"(score {runner_up_score:.1f}). "
                f"A veterinarian can distinguish between these."
            )

        parts.append(
            "This is a possible diagnosis based on reported symptoms only. "
            "A confirmed diagnosis requires veterinary examination."
        )

        return " ".join(parts)

    def match(self, query: str) -> TriageResult:
        """
        Run triage on a farmer's free-text query.

        Args:
            query: Raw text from the farmer.

        Returns:
            TriageResult with full explanation and biosecurity guidance.
        """
        if not query or not query.strip():
            return TriageResult(matched=False)

        query_norm = self._normalise(query)

        scores: list[tuple[float, dict[str, Any], list[str], list[str]]] = []

        for disease in self._diseases:
            score, matched, dist_matched = self._score_disease(
                query_norm, disease
            )
            scores.append((score, disease, matched, dist_matched))

        # Sort descending by score
        scores.sort(key=lambda x: x[0], reverse=True)

        best_score, best_disease, best_matched, best_dist = scores[0]

        # Runner-up (second best with a meaningful score)
        runner_up_name  = None
        runner_up_score = 0.0
        if len(scores) > 1 and scores[1][0] >= CONFIDENCE_THRESHOLD:
            runner_up_name  = scores[1][1]["name"]
            runner_up_score = scores[1][0]

        if best_score < CONFIDENCE_THRESHOLD:
            return TriageResult(
                matched=False,
                score=best_score,
                explanation=(
                    "No disease pattern matched the reported symptoms with "
                    "sufficient confidence. Please consult a veterinarian "
                    "or provide more specific symptom details."
                ),
            )

        # Confidence band
        if best_score >= 10:
            confidence = "high"
        elif best_score >= 5:
            confidence = "medium"
        else:
            confidence = "low"

        explanation = self._build_explanation(
            best_disease, best_matched, best_dist,
            best_score, confidence, runner_up_name, runner_up_score,
        )

        result = TriageResult(
            matched               = True,
            disease_name          = best_disease["name"],
            disease_id            = best_disease["id"],
            severity              = best_disease["severity"],
            score                 = best_score,
            matched_symptoms      = [s for s in best_matched if not s.startswith("alias:")],
            distinguishing_matched= best_dist,
            first_aid             = best_disease.get("first_aid", ""),
            treatment             = best_disease.get("treatment", ""),
            prevention            = best_disease.get("prevention", ""),
            biosecurity           = best_disease.get("biosecurity_actions", []),
            when_to_call_vet      = best_disease.get("when_to_call_vet", ""),
            vet_referral          = best_disease.get("vet_referral", False),
            sources               = best_disease.get("references", []),
            confidence            = confidence,
            explanation           = explanation,
            runner_up             = runner_up_name,
            runner_up_score       = runner_up_score,
        )

        logger.info(
            f"Triage: {result.disease_name} "
            f"(score={best_score:.1f}, conf={confidence})"
        )
        return result

    def format_for_prompt(self, result: TriageResult) -> str:
        """
        Format a TriageResult as a structured block for LLM system prompt injection.
        """
        if not result.matched:
            return ""

        vet_note = (
            f"\nVETERINARY REFERRAL: {result.when_to_call_vet}"
            if result.vet_referral or result.when_to_call_vet
            else ""
        )

        biosec = (
            "\nBIOSECURITY ACTIONS REQUIRED:\n" +
            "\n".join(f"- {a}" for a in result.biosecurity)
            if result.biosecurity else ""
        )

        runner_up_note = (
            f"\nALTERNATIVE TO CONSIDER: {result.runner_up} "
            f"(score {result.runner_up_score:.1f}) — "
            f"mention this in your response."
            if result.runner_up else ""
        )

        return (
            f"TRIAGE MATCH (confidence={result.confidence}, score={result.score}):\n"
            f"Possible Disease: {result.disease_name}\n"
            f"Severity: {result.severity.upper()}\n"
            f"Matching symptoms: {', '.join(result.matched_symptoms)}\n"
            f"Distinguishing symptoms confirmed: {', '.join(result.distinguishing_matched)}\n"
            f"\nFIRST AID:\n{result.first_aid}\n"
            f"\nTREATMENT:\n{result.treatment}\n"
            f"\nPREVENTION:\n{result.prevention}"
            f"{biosec}"
            f"{vet_note}"
            f"{runner_up_note}\n"
            f"\nSources: {', '.join(result.sources)}"
        )


# ── Module-level singleton ────────────────────────────────────────

_engine: TriageEngine | None = None


def get_triage_engine() -> TriageEngine:
    global _engine
    if _engine is None:
        _engine = TriageEngine()
    return _engine


def triage(query: str) -> TriageResult:
    """Convenience function using the singleton engine."""
    return get_triage_engine().match(query)


# ── Self-test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    print("=" * 70)
    print("AgroPulse AI — Sprint 4 Triage Engine Test")
    print("=" * 70)

    engine = TriageEngine()

    test_cases = [
        ("My chickens have twisted necks, are circling and showing green diarrhoea", "Newcastle Disease"),
        ("Chicks are picking at their own vents and have white watery diarrhoea",     "Gumboro Disease"),
        ("Blood in droppings and pale combs in 3-week-old chicks",                    "Coccidiosis"),
        ("Adult birds dying with sulphur yellow droppings and shrunken pale combs",   "Fowl Typhoid"),
        ("Progressive leg paralysis, one leg forward one leg back, grey eye",         "Marek's Disease"),
        ("Sudden death, blue comb, swollen wattles, mucous from mouth",               "Fowl Cholera"),
        ("Drop in egg production, misshapen eggs and watery egg white with coughing", "Infectious Bronchitis"),
        ("Foul smelling nasal discharge and swollen face sinuses",                    "Infectious Coryza"),
        ("Young chicks gasping with neck extended, brooder pneumonia suspected",      "Aspergillosis"),
        ("Sudden drop in egg production, shell-less eggs, birds appear healthy",      "Egg Drop Syndrome"),
        ("General question about feed formulation",                                   None),
    ]

    passed = 0
    for query, expected in test_cases:
        result = engine.match(query)
        got    = result.disease_name
        ok     = "PASS" if got == expected else "FAIL"
        if ok == "PASS":
            passed += 1
        print(f"\n  [{ok}] Expected: {expected}")
        print(f"        Got     : {got} (score={result.score:.1f}, conf={result.confidence})")
        if result.distinguishing_matched:
            print(f"        Dist.   : {result.distinguishing_matched}")
        if ok == "FAIL":
            print(f"        Query   : {query}")
            print(f"        Explain : {result.explanation[:120]}")

    print(f"\n{'=' * 70}")
    print(f"Results: {passed}/{len(test_cases)} passed")
    print("=" * 70)
    sys.exit(0 if passed == len(test_cases) else 1)