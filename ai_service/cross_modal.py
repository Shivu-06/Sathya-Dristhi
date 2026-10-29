"""
SatyaDrishti - Cross-Modal Matching Engine
Implements Section VII Cross-Modal Branch:
Calculates alignment between visual evidence and textual description.
Formula: s_x = 1 - cos(e_img, e_txt)
where:
  e_img: visual category feature embedding vector
  e_txt: textual complaint intent embedding vector
  Larger s_x implies larger mismatch between photo and description.
"""

import numpy as np
from PIL import Image

class CrossModalMatcher:
    def __init__(self):
        # 5 primary civic categories
        self.categories = [
            "pothole",       # 0: Road damage, crater, asphalt hole
            "garbage",       # 1: Solid waste, plastic pile, trash dump
            "streetlight",   # 2: Lamp post, electrical pole, lighting defect
            "water_leak",    # 3: Pipeline burst, water logging, drainage
            "general_civic"  # 4: Encroachment, footpaths, signals
        ]
        
        # Text category lexicons
        self.category_lexicons = {
            "pothole": ["pothole", "crater", "road", "tar", "asphalt", "bump", "pavement", "tarmac", "cavity", "damaged road"],
            "garbage": ["garbage", "trash", "waste", "dump", "debris", "plastic", "smell", "rotting", "litter", "rubbish", "compost"],
            "streetlight": ["streetlight", "street light", "lamp", "pole", "bulb", "darkness", "wiring", "night light", "electric"],
            "water_leak": ["water", "leak", "pipe", "pipeline", "drainage", "sewage", "flooding", "waterlogging", "gutter", "overflow"],
            "general_civic": ["footpath", "signal", "traffic", "encroachment", "divider", "tree", "signboard", "bbmp"]
        }

    def extract_visual_embedding(self, image_path: str) -> np.ndarray:
        """
        Extracts visual semantic feature vector e_img using color histograms,
        entropy, edge gradients, and brightness distributions.
        """
        try:
            img = Image.open(image_path).convert('RGB').resize((128, 128))
            arr = np.array(img, dtype=np.float32)
            
            # Grayscale channel
            gray = 0.2989 * arr[:, :, 0] + 0.5870 * arr[:, :, 1] + 0.1140 * arr[:, :, 2]
            
            # Visual feature 1: Pothole indicators (dark asphalt gray/black, low saturation, texture roughness)
            mean_brightness = float(np.mean(gray))
            road_darkness = 1.0 - min(1.0, mean_brightness / 140.0)
            dx = np.diff(gray, axis=1)
            dy = np.diff(gray, axis=0)
            roughness = float((np.mean(np.abs(dx)) + np.mean(np.abs(dy))) / 30.0)
            pothole_cue = 0.5 * road_darkness + 0.5 * min(1.0, roughness)

            # Visual feature 2: Garbage indicators (high color entropy, chaotic multi-hue variance)
            r_std = float(np.std(arr[:, :, 0]))
            g_std = float(np.std(arr[:, :, 1]))
            b_std = float(np.std(arr[:, :, 2]))
            color_chaos = min(1.0, (r_std + g_std + b_std) / 120.0)
            garbage_cue = 0.6 * color_chaos + 0.4 * min(1.0, roughness)

            # Visual feature 3: Streetlight indicators (high contrast bright spots or vertical pole gradients)
            bright_hotspots = float(np.sum(gray > 220) / (128 * 128))
            vertical_edges = float(np.mean(np.abs(dx))) / 25.0
            streetlight_cue = min(1.0, 0.6 * vertical_edges + 0.4 * min(1.0, bright_hotspots * 10.0))

            # Visual feature 4: Water leak / Drainage (reflective patches, high blue channel ratio)
            blue_ratio = float(np.mean(arr[:, :, 2]) / (np.mean(arr[:, :, 0]) + np.mean(arr[:, :, 1]) + 1e-4))
            specular_highlights = float(np.sum((gray > 200) & (arr[:, :, 2] > 180)) / (128 * 128))
            water_cue = min(1.0, 0.5 * (blue_ratio - 0.3) * 2.0 + 0.5 * min(1.0, specular_highlights * 15.0))
            water_cue = max(0.05, water_cue)

            # Visual feature 5: General civic infrastructure
            general_cue = 0.25

            e_img = np.array([pothole_cue, garbage_cue, streetlight_cue, water_cue, general_cue], dtype=np.float32)
            # Normalize vector to unit length
            norm = np.linalg.norm(e_img)
            if norm > 0:
                e_img = e_img / norm
            return e_img
        except Exception:
            return np.ones(5, dtype=np.float32) / np.sqrt(5.0)

    def extract_text_embedding(self, text: str, category_hint: str = None) -> np.ndarray:
        """
        Extracts textual semantic intent vector e_txt based on keyword distributions
        and declared complaint category.
        """
        text_lower = (text or "").lower()
        cat_lower = (category_hint or "").lower()
        
        scores = []
        for i, cat in enumerate(self.categories):
            score = 0.1 # baseline smoothing
            # Priority if category hint matches
            if cat in cat_lower or (cat == "pothole" and "road" in cat_lower):
                score += 0.6
                
            # Lexicon occurrences
            for word in self.category_lexicons[cat]:
                if word in text_lower:
                    score += 0.35
            scores.append(score)

        e_txt = np.array(scores, dtype=np.float32)
        norm = np.linalg.norm(e_txt)
        if norm > 0:
            e_txt = e_txt / norm
        return e_txt

    def compute_cross_modal(self, image_path: str, text: str, category_hint: str = None) -> dict:
        """
        Calculates cosine similarity and returns cross-modal distance s_x = 1 - cos(e_img, e_txt).
        """
        e_img = self.extract_visual_embedding(image_path)
        e_txt = self.extract_text_embedding(text, category_hint)

        cos_sim = float(np.dot(e_img, e_txt))
        cos_sim = max(-1.0, min(1.0, cos_sim))
        
        # s_x = 1 - cos(e_img, e_txt), scaled to [0, 1]
        # High similarity (cos_sim ~ 0.9) -> s_x ~ 0.05 - 0.10
        # Disagreement (cos_sim ~ 0.2) -> s_x ~ 0.80
        s_x = (1.0 - cos_sim) / 2.0 * 1.5 # stretch dynamic range
        s_x = min(1.0, max(0.0, s_x))

        # Identify dominant visual vs textual predictions
        vis_top_idx = int(np.argmax(e_img))
        txt_top_idx = int(np.argmax(e_txt))
        vis_pred = self.categories[vis_top_idx]
        txt_pred = self.categories[txt_top_idx]

        reasons = []
        is_mismatch = False
        if s_x > 0.45 and vis_pred != txt_pred:
            is_mismatch = True
            reasons.append(
                f"Cross-modal contradiction: Description focuses on '{txt_pred.replace('_', ' ')}' "
                f"while visual analysis detects cues corresponding to '{vis_pred.replace('_', ' ')}'"
            )

        return {
            "s_x": round(s_x, 4),
            "cosine_similarity": round(cos_sim, 4),
            "visual_category": vis_pred,
            "text_category": txt_pred,
            "is_mismatch": is_mismatch,
            "reasons": reasons
        }
