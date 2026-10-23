"""Deterministic baseline for the August message router. No model call.

Rules are checked in order; the first match wins. These rules were written
after reading the August SAMPLE labels, so accuracy on that sample is
optimistic. Treat it as a floor, not a result: a real submission needs a
held-out check.
"""

import re

INJECTION = re.compile(r"ignore (all )?(previous|prior) (routing )?rules|mark this message as", re.I)
SCAM = re.compile(
    r"\botp\b|password|login code|verify now|confirm .*account|account will expire"
    r"|profile will be blocked|temp(orarily)? (blocked|suspended)|security alert|\.in\b|bit\.ly",
    re.I,
)
PROMO = re.compile(r"% ?off|\boffer\b|discount|promo|shopping|won'?t wait|selected products|\bTRY\d+", re.I)
FORWARD = re.compile(r"\bfwd\b|forwarded|as received", re.I)
GREETING = re.compile(r"good (morning|night|evening)|stay positive|share blessings", re.I)
URGENT = re.compile(r"urgent|\bnow\b|escalation|last-minute|pulled to|join|today|can you|\bcall\b|come online", re.I)
EVENT = re.compile(r"circular|form is open|timing|event|bus|cultural|appointment|health-related|registration", re.I)


def decide(row):
    text = (row.get("message_text") or "").strip()
    media = (row.get("media_type") or "").strip()
    if not text and media == "voice":
        # No transcript is available to this baseline: say so, with low confidence.
        return {"action": "digest", "message_type": "unknown",
                "reason": "voice note with no transcript; defaulted to digest",
                "confidence": 0.3, "evidence_message_ids": "none"}
    if INJECTION.search(text):
        return {"action": "mute", "message_type": "scam",
                "reason": "embedded instruction to override routing; treated as scam",
                "confidence": 0.9, "evidence_message_ids": "none"}
    if SCAM.search(text):
        return {"action": "mute", "message_type": "scam",
                "reason": "asks for OTP, password or login code under urgency",
                "confidence": 0.85, "evidence_message_ids": "none"}
    if FORWARD.search(text):
        return {"action": "mute", "message_type": "forward",
                "reason": "forwarded or unverified content",
                "confidence": 0.7, "evidence_message_ids": "none"}
    if GREETING.search(text):
        return {"action": "mute", "message_type": "greeting",
                "reason": "generic greeting", "confidence": 0.7, "evidence_message_ids": "none"}
    if PROMO.search(text):
        return {"action": "mute", "message_type": "promotion",
                "reason": "promotional offer with no personal relevance",
                "confidence": 0.7, "evidence_message_ids": "none"}
    if URGENT.search(text):
        return {"action": "notify", "message_type": "urgent",
                "reason": "time-sensitive request or change",
                "confidence": 0.6, "evidence_message_ids": "none"}
    if EVENT.search(text):
        soon = "tomorrow" in text.lower() or "today" in text.lower()
        return {"action": "notify" if soon else "digest", "message_type": "event",
                "reason": "event or schedule information", "confidence": 0.6,
                "evidence_message_ids": "none"}
    return {"action": "digest", "message_type": "personal",
            "reason": "no urgency or risk signal", "confidence": 0.5,
            "evidence_message_ids": "none"}
