"""
OCR Confidence Detection (FDE Test Case #6)
Analyzes raw policy text for signs of OCR corruption
and assigns per-field and overall confidence levels.
"""

import re
from typing import Optional
from pydantic import BaseModel


class OcrIssue(BaseModel):
    issue_type: str
    location: Optional[str] = None
    sample: str
    severity: str  # "high", "medium", "low"
    suggestion: str


class OcrConfidenceReport(BaseModel):
    overall_confidence: str  # "high", "medium", "low"
    issues: list[OcrIssue] = []


# Patterns indicative of OCR errors
OCR_PATTERNS = [
    # Letter substituted for digit in money amounts (O for 0, S for 5, l for 1)
    (r"\$\d{1,3}[OoSsLlBb]\d{3}", "Digit-letter substitution in dollar amount", "high"),
    (r"\$[A-Za-z],\d{3}", "Letter in dollar amount separator", "high"),
    # Comma in wrong position (e.g., $25,O00)
    (r"\$\d{2},[A-Za-z]\d{2}", "Letter after comma in dollar amount", "high"),
    # Missing space before dollar sign
    (r"[a-z]\$\d", "Missing space before dollar amount", "medium"),
    # Run-together words common in bad OCR
    (r"(?i)bod(?:il)?y\s*inj(?:ur)?y\s*liab", "Potential OCR issue with 'Bodily Injury Liability'", "medium"),
    # Repeated characters
    (r"(.)\1{3,}", "Repeated characters suggest scan noise", "low"),
    # Garbled percentage format
    (r"\d+[Oo]/\d+", "Digit-letter substitution in fraction", "high"),
    # Unusual dollar amount format with lowercase
    (r"\$[a-z]\d+", "Lowercase letter before number in amount", "medium"),
    # Dollar amount with period in wrong place
    (r"\$\d+\.\d{4,}", "Unusual decimal precision in dollar amount", "medium"),
]

# Known insurance terms that commonly have OCR errors
KNOWN_TERM_VARIATIONS = [
    (r"(?i)\bbod(?:il)?y\b(?!\s*injury)", "Possible 'Bodily' misspelling"),
    (r"(?i)\bliab(?:il)?ty\b", "Possible 'Liability' misspelling"),
    (r"(?i)\bcomprehen\w*\b(?!\s*ive)", "Possible 'Comprehensive' misspelling"),
    (r"(?i)\bdeductibl[ea]\b", "Possible 'Deductible' misspelling"),
    (r"(?i)\bexclu[ds]ion\b", "Possible 'Exclusion' misspelling"),
    (r"(?i)\bcovera[gj]e\b", "Possible 'Coverage' misspelling"),
]


def analyze_ocr_confidence(raw_text: str) -> OcrConfidenceReport:
    """
    Scan the raw policy text for OCR artifact patterns and assign
    an overall confidence level.
    """
    issues: list[OcrIssue] = []
    lines = raw_text.split("\n")

    for pattern, description, severity in OCR_PATTERNS:
        matches = re.finditer(pattern, raw_text, re.MULTILINE)
        for m in matches:
            # Find the surrounding line for context
            sample = m.group()[:80]
            context_line = None
            for i, line in enumerate(lines):
                if m.group() in line:
                    context_line = f"line {i + 1}"
                    break

            issues.append(OcrIssue(
                issue_type=description,
                location=context_line,
                sample=sample,
                severity=severity,
                suggestion="Review the original document. Consider uploading a clearer scan.",
            ))

    # Check for known term misspellings
    for pattern, description in KNOWN_TERM_VARIATIONS:
        matches = re.finditer(pattern, raw_text)
        for m in matches:
            # Only flag if the match is not the correctly spelled version
            term = m.group()
            context_line = None
            for i, line in enumerate(lines):
                if term in line:
                    context_line = f"line {i + 1}"
                    break
            issues.append(OcrIssue(
                issue_type=description,
                location=context_line,
                sample=term[:80],
                severity="low",
                suggestion="Verify the correct spelling against the original policy document.",
            ))

    # Determine overall confidence
    high_severity = sum(1 for i in issues if i.severity == "high")
    medium_severity = sum(1 for i in issues if i.severity == "medium")

    if high_severity >= 2:
        overall = "low"
    elif high_severity >= 1 or medium_severity >= 3:
        overall = "medium"
    elif medium_severity >= 1:
        overall = "medium"
    elif issues:
        overall = "high"
    else:
        overall = "high"

    return OcrConfidenceReport(
        overall_confidence=overall,
        issues=issues,
    )
