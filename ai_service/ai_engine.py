"""
SatyaDrishti - Complete AI Multimodal Verification Microservice
Implements Section VII & Equation (3):
  S = w1*s_img + w2*s_for + w3*s_x + w4*s_txt
With weights:
  w1 = 0.35 (CNN Image Classifier)
  w2 = 0.25 (Image Forensics: ELA + EXIF + Duplicate Hash)
  w3 = 0.25 (Cross-Modal Image-Text Matching)
  w4 = 0.15 (NLP Text Credibility)
"""

import os
import sys
import json
import argparse
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import SatyaDrishti verification branches
from forensics import ImageForensics
from cnn_model import ComplaintCNNClassifier
from text_nlp import TextCredibilityAnalyzer
from cross_modal import CrossModalMatcher

app = FastAPI(title="SatyaDrishti AI Verification Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SatyaDrishtiEngine:
    def __init__(self):
        # Initialize the 4 multimodal branches
        self.forensics = ImageForensics(ela_quality=90, ela_scale=15)
        self.cnn = ComplaintCNNClassifier()
        self.nlp = TextCredibilityAnalyzer()
        self.cross_modal = CrossModalMatcher()

        # Weights specified in Section VII, Eq. (3)
        self.w1 = 0.35  # s_img
        self.w2 = 0.25  # s_for
        self.w3 = 0.25  # s_x
        self.w4 = 0.15  # s_txt

    def verify(self, image_path: str, description: str, category: str = "", existing_complaints: list = None) -> dict:
        """
        Executes full multimodal pipeline and fuses branch signals into fraud score S.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at {image_path}")

        # Branch 1: CNN Image Classifier (s_img)
        cnn_res = self.cnn.predict(image_path)
        s_img = cnn_res["s_img"]

        # Branch 2: Image Forensics (s_for: ELA + EXIF + Perceptual Hash)
        for_res = self.forensics.analyze_full_forensics(image_path, existing_complaints or [])
        s_for = for_res["s_for"]

        # Branch 3: Cross-Modal Matching (s_x)
        cm_res = self.cross_modal.compute_cross_modal(image_path, description, category)
        s_x = cm_res["s_x"]

        # Branch 4: Text NLP Credibility (s_txt)
        txt_res = self.nlp.analyze(description)
        s_txt = txt_res["s_txt"]

        # Fused Fraud Score S (Eq. 3)
        S = (self.w1 * s_img) + (self.w2 * s_for) + (self.w3 * s_x) + (self.w4 * s_txt)
        S = round(min(1.0, max(0.0, S)), 4)

        # Plain language explanation synthesis
        explanations = []
        if cnn_res["is_fake"]:
            explanations.append(f"CNN anomaly filter detected synthetic/forged patterns (confidence {cnn_res['confidence_pct']}%)")
        
        explanations.extend(for_res["reasons"])
        explanations.extend(cm_res["reasons"])
        explanations.extend(txt_res["reasons"])

        if not explanations:
            explanations.append("All multimodal authenticity checks passed. Photographic and textual evidence are fully consistent.")

        # Determine complaint triage state
        if S < 0.38:
            status = "Verified-low"
            risk_label = "Low Risk (Genuine Evidence)"
            queue_priority = "Front of Queue (Priority Processing)"
        elif S < 0.60:
            status = "Under review"
            risk_label = "Medium Risk (Standard Review)"
            queue_priority = "Standard Queue"
        else:
            status = "Flagged"
            risk_label = "High Risk (Suspicious / Manipulated)"
            queue_priority = "Flagged Review Queue (Immediate Audit)"

        return {
            "fraud_score": S,
            "status": status,
            "risk_label": risk_label,
            "queue_priority": queue_priority,
            "explanations": explanations,
            "branches": {
                "s_img": {
                    "score": s_img,
                    "weight": self.w1,
                    "weighted_score": round(self.w1 * s_img, 4),
                    "label": cnn_res["label"],
                    "confidence": cnn_res["confidence_pct"],
                    "metrics": cnn_res["metrics"]
                },
                "s_for": {
                    "score": s_for,
                    "weight": self.w2,
                    "weighted_score": round(self.w2 * s_for, 4),
                    "ela_score": for_res["ela"]["ela_score"],
                    "exif_score": for_res["exif"]["exif_score"],
                    "duplicate_score": for_res["duplicate"]["duplicate_score"],
                    "duplicate_match": for_res["duplicate"]["match_info"],
                    "exif_metadata": for_res["exif"]["metadata"]
                },
                "s_x": {
                    "score": s_x,
                    "weight": self.w3,
                    "weighted_score": round(self.w3 * s_x, 4),
                    "cosine_similarity": cm_res["cosine_similarity"],
                    "visual_detected": cm_res["visual_category"],
                    "text_declared": cm_res["text_category"],
                    "is_mismatch": cm_res["is_mismatch"]
                },
                "s_txt": {
                    "score": s_txt,
                    "weight": self.w4,
                    "weighted_score": round(self.w4 * s_txt, 4),
                    "word_count": txt_res["word_count"],
                    "exaggeration": txt_res["exaggeration_score"],
                    "vagueness": txt_res["vagueness_score"]
                }
            },
            "ela_preview_base64": for_res["ela"].get("ela_preview_base64"),
            "image_hash": for_res["image_hash"]
        }

# Global singleton
engine = SatyaDrishtiEngine()

@app.get("/")
def home():
    return {
        "service": "SatyaDrishti AI Verification Engine",
        "version": "1.0.0",
        "status": "active",
        "description": "Multimodal fake complaint detection using Computer Vision, ELA Forensics, and Cross-Modal NLP"
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/verify")
def api_verify(payload: dict = Body(...)):
    """
    JSON endpoint: receives image_path, description, category, and historical complaints.
    """
    image_path = payload.get("image_path")
    description = payload.get("description", "")
    category = payload.get("category", "")
    existing_complaints = payload.get("existing_complaints", [])

    if not image_path:
        raise HTTPException(status_code=400, detail="image_path is required")

    try:
        result = engine.verify(image_path, description, category, existing_complaints)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SatyaDrishti AI Engine")
    parser.add_argument("--port", type=int, default=5001, help="Port to run FastAPI service")
    parser.add_argument("--image", type=str, help="Single image verification path")
    parser.add_argument("--text", type=str, default="", help="Complaint description text")
    parser.add_argument("--category", type=str, default="", help="Complaint category")
    args = parser.parse_args()

    if args.image:
        print(f"[*] Running CLI verification for {args.image}...")
        res = engine.verify(args.image, args.text, args.category)
        print(json.dumps(res, indent=2))
    else:
        print(f"[*] Starting SatyaDrishti AI Microservice on http://127.0.0.1:{args.port}...")
        uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="info")
