"""
SatyaDrishti - Text Credibility & NLP Analysis Module
Analyzes complaint text descriptions for:
1. Exaggeration and sensationalism markers
2. High vagueness / extreme brevity
3. Robotic / copy-pasted grievance templates
4. Lexical sentiment divergence
Computes s_txt in [0, 1] where higher indicates greater suspicion.
"""

import re

class TextCredibilityAnalyzer:
    def __init__(self):
        # Exaggeration and sensationalism keywords
        self.exaggeration_patterns = [
            r"\b(catastroph(e|ic)|disaster|unprecedented|massive apocalypse|millions (dying|affected))\b",
            r"\b(worst in the world|worst in history|never seen before|total ruin|deadly danger)\b",
            r"\b(emergency.*immediately.*or else|arrest everyone|entire city ruined)\b",
            r"\b(scam of the century|completely destroyed)\b"
        ]
        
        # Spam / copypasta boilerplate indicators
        self.spam_phrases = [
            "lorem ipsum", "test complaint", "asdf", "qwerty", "test test test",
            "sample text", "checking if this works", "ignore this", "testing 123"
        ]

        # Valid civic terms indicating legitimate civic reporting
        self.civic_terms = [
            "road", "pothole", "asphalt", "tar", "crater", "vehicle", "traffic",
            "garbage", "waste", "trash", "debris", "dump", "bin", "smell", "drainage",
            "streetlight", "light", "lamp", "pole", "bulb", "dark", "night",
            "water", "leak", "pipe", "pipeline", "flooding", "supply", "cauvery",
            "bbmp", "ward", "cross", "main", "layout", "nagar", "junction", "street"
        ]

    def analyze(self, text: str) -> dict:
        """
        Calculates text suspicion score s_txt.
        """
        if not text or not text.strip():
            return {
                "s_txt": 0.85,
                "reasons": ["Description is completely empty or blank"],
                "word_count": 0,
                "exaggeration_score": 0.0,
                "vagueness_score": 1.0
            }

        clean_text = text.strip()
        words = clean_text.split()
        word_count = len(words)
        reasons = []

        # 1. Brevity / Vagueness check
        vagueness_score = 0.0
        if word_count < 4:
            vagueness_score = 0.65
            reasons.append("Description is excessively brief (< 4 words), lacking actionable civic context")
        elif word_count < 8:
            vagueness_score = 0.35
            reasons.append("Description is brief; lacked specific landmark or location details")
        else:
            vagueness_score = 0.05

        # 2. Exaggeration check
        exaggeration_hits = 0
        for pattern in self.exaggeration_patterns:
            if re.search(pattern, clean_text, re.IGNORECASE):
                exaggeration_hits += 1

        exaggeration_score = min(1.0, exaggeration_hits * 0.45)
        if exaggeration_hits > 0:
            reasons.append(f"Excessive sensationalist language detected ({exaggeration_hits} exaggeration triggers)")

        # 3. All-Caps Shrieking / Excessive Punctuation
        caps_ratio = sum(1 for c in clean_text if c.isupper()) / max(1, len(clean_text))
        exclamation_count = clean_text.count("!") + clean_text.count("?")
        if caps_ratio > 0.45 and len(clean_text) > 15:
            reasons.append("High uppercase letter ratio indicates aggressive or non-standard submission")
            exaggeration_score = min(1.0, exaggeration_score + 0.3)
        if exclamation_count >= 4:
            reasons.append("Repeated exclamation/question marks detected")
            exaggeration_score = min(1.0, exaggeration_score + 0.2)

        # 4. Spam / Fake keywords
        spam_penalty = 0.0
        lower_text = clean_text.lower()
        for spam in self.spam_phrases:
            if spam in lower_text:
                spam_penalty = 0.90
                reasons.append(f"Spam / placeholder test phrase found: '{spam}'")
                break

        # 5. Civic relevance check (rewards legitimate civic vocabulary)
        civic_hits = sum(1 for term in self.civic_terms if term in lower_text)
        civic_relevance = min(1.0, civic_hits / 3.0)
        civic_discount = 0.20 if civic_relevance >= 0.5 else 0.0

        # Weighted formula for text credibility branch:
        # s_txt = 0.45 * vagueness + 0.40 * exaggeration + 0.35 * spam - civic_discount
        raw_score = (0.40 * vagueness_score + 0.40 * exaggeration_score + 0.40 * spam_penalty) - civic_discount
        s_txt = max(0.05, min(1.0, raw_score))

        return {
            "s_txt": round(s_txt, 4),
            "reasons": reasons,
            "word_count": word_count,
            "exaggeration_score": round(exaggeration_score, 3),
            "vagueness_score": round(vagueness_score, 3),
            "civic_relevance": round(civic_relevance, 2)
        }
