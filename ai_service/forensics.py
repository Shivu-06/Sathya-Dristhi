"""
SatyaDrishti - Computer Vision Image Forensics Module
Implements:
1. Error Level Analysis (ELA) for image splicing & retouching detection
2. EXIF Metadata consistency and digital tampering markers
3. Perceptual Hashing (dHash) for duplicate / reused complaint detection
"""

import os
import io
import base64
import numpy as np
from PIL import Image, ImageChops, ImageEnhance, ExifTags
from datetime import datetime

class ImageForensics:
    def __init__(self, ela_quality=90, ela_scale=15):
        self.ela_quality = ela_quality
        self.ela_scale = ela_scale
        self.tampering_software_keywords = [
            "photoshop", "gimp", "canva", "snapseed", "lightroom",
            "picsart", "facetune", "pixlr", "vsco", "afterlight",
            "meitu", "remini", "photodirector", "paint.net"
        ]

    def compute_ela(self, image_path: str):
        """
        Performs Error Level Analysis (ELA) by re-saving at a fixed JPEG quality
        and calculating the amplified absolute difference matrix.
        Returns:
            ela_score (float 0.0 - 1.0): suspicion score based on compression variance
            variance (float): raw statistical variance of compression residuals
            ela_base64 (str): base64-encoded visual heat map for investigator inspection
        """
        try:
            original = Image.open(image_path).convert('RGB')
            
            # Save temporary copy in memory at target quality
            buffer = io.BytesIO()
            original.save(buffer, 'JPEG', quality=self.ela_quality)
            buffer.seek(0)
            resaved = Image.open(buffer)

            # Compute pixel-by-pixel difference
            diff = ImageChops.difference(original, resaved)
            
            # Amplify difference to make compression boundaries visible
            extrema = diff.getextrema()
            max_diff = max([ex[1] for ex in extrema])
            if max_diff == 0:
                max_diff = 1
            scale = 255.0 / max_diff
            scale = min(scale, float(self.ela_scale))
            
            ela_img = ImageEnhance.Brightness(diff).enhance(scale)

            # Analyze statistical variance across 16x16 grid patches
            diff_arr = np.array(diff, dtype=np.float32)
            # Higher standard deviation between localized regions indicates localized splicing/tampering
            patch_size = 16
            h, w, _ = diff_arr.shape
            variances = []
            for y in range(0, h - patch_size, patch_size):
                for x in range(0, w - patch_size, patch_size):
                    patch = diff_arr[y:y+patch_size, x:x+patch_size]
                    variances.append(np.var(patch))
            
            if len(variances) > 0:
                var_array = np.array(variances)
                max_patch_var = float(np.max(var_array))
                mean_patch_var = float(np.mean(var_array))
                std_patch_var = float(np.std(var_array))
                
                # Spliced images exhibit sharp divergence between spliced area and background
                anomaly_ratio = (max_patch_var - mean_patch_var) / (mean_patch_var + 1e-5)
                # Map to [0, 1] range
                ela_score = min(1.0, max(0.0, float(anomaly_ratio / 6.0)))
            else:
                ela_score = 0.1
                variance = 0.0

            # Encode ELA preview to base64 for direct UI display
            out_buf = io.BytesIO()
            ela_img.save(out_buf, format='JPEG', quality=85)
            ela_base64 = base64.b64encode(out_buf.getvalue()).decode('utf-8')

            return {
                "ela_score": round(ela_score, 4),
                "max_patch_variance": round(max_patch_var if len(variances) else 0.0, 2),
                "ela_preview_base64": f"data:image/jpeg;base64,{ela_base64}",
                "suspicious": bool(ela_score > 0.45)
            }
        except Exception as e:
            return {
                "ela_score": 0.2,
                "error": str(e),
                "ela_preview_base64": None,
                "suspicious": False
            }

    def inspect_exif(self, image_path: str, submission_time=None):
        """
        Inspects EXIF metadata for:
        1. Tampering/editing software tags (Photoshop, Canva, etc.)
        2. Date mismatch between capture date and complaint filing date
        3. Missing metadata (common when downloading from web/social media)
        """
        flags = []
        suspicion_score = 0.0
        exif_data = {}

        try:
            img = Image.open(image_path)
            raw_exif = img._getexif()

            if not raw_exif:
                flags.append("No EXIF metadata present (often stripped by social media / web downloads)")
                suspicion_score += 0.35
                return {
                    "exif_score": round(suspicion_score, 4),
                    "flags": flags,
                    "metadata": {},
                    "tampering_detected": False
                }

            # Map tag IDs to human-readable names
            for tag_id, value in raw_exif.items():
                tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                if isinstance(value, (str, int, float)):
                    exif_data[tag_name] = str(value)

            # Check Software tag
            software = exif_data.get("Software", "").lower()
            if software:
                for kw in self.tampering_software_keywords:
                    if kw in software:
                        flags.append(f"Image edited using digital manipulation software: '{exif_data.get('Software')}'")
                        suspicion_score += 0.55
                        break

            # Check DateTime / DateTimeOriginal
            dt_str = exif_data.get("DateTimeOriginal") or exif_data.get("DateTime")
            if dt_str:
                try:
                    # Typical format: '2023:05:14 12:45:00'
                    photo_dt = datetime.strptime(dt_str[:19], "%Y:%m:%d %H:%M:%S")
                    current_dt = datetime.now()
                    diff_days = (current_dt - photo_dt).days
                    if diff_days > 180:
                        flags.append(f"Photo captured {diff_days} days ago ({photo_dt.strftime('%b %Y')}), possible reuse of archived photo")
                        suspicion_score += 0.40
                    elif diff_days > 30:
                        flags.append(f"Photo taken over {diff_days} days before filing complaint")
                        suspicion_score += 0.20
                except Exception:
                    pass
            else:
                flags.append("Original timestamp absent from EXIF tags")
                suspicion_score += 0.15

            # Camera make/model
            make = exif_data.get("Make", "")
            model = exif_data.get("Model", "")
            if not make and not model:
                flags.append("Camera hardware details missing")
                suspicion_score += 0.10

            suspicion_score = min(1.0, suspicion_score)

            return {
                "exif_score": round(suspicion_score, 4),
                "flags": flags,
                "metadata": {
                    "Make": make,
                    "Model": model,
                    "Software": exif_data.get("Software", "None"),
                    "DateTime": dt_str or "Not recorded"
                },
                "tampering_detected": bool(suspicion_score > 0.45)
            }
        except Exception as e:
            return {
                "exif_score": 0.25,
                "flags": [f"Metadata read error: {str(e)}"],
                "metadata": {},
                "tampering_detected": False
            }

    def compute_dhash(self, image_path: str, hash_size=8) -> str:
        """
        Computes 64-bit difference hash (dHash) for fast visual similarity and duplicate detection.
        """
        try:
            img = Image.open(image_path).convert('L').resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
            pixels = np.array(img, dtype=np.float32)
            # Compare adjacent pixels horizontally: True if left > right
            diff = pixels[:, 1:] > pixels[:, :-1]
            # Convert boolean array to hex string
            binary_str = "".join(["1" if b else "0" for b in diff.flatten()])
            hex_str = f"{int(binary_str, 2):016x}"
            return hex_str
        except Exception:
            return "0000000000000000"

    def compare_hashes(self, hash1: str, hash2: str) -> int:
        """
        Computes Hamming distance between two 64-bit hex hashes.
        0 means exact visual match, <= 6 means duplicate/near-duplicate.
        """
        try:
            val1 = int(hash1, 16)
            val2 = int(hash2, 16)
            xor_val = val1 ^ val2
            return bin(xor_val).count("1")
        except Exception:
            return 64

    def check_duplicate(self, target_hash: str, existing_complaints: list):
        """
        Scans existing complaints for duplicate photos.
        """
        best_match = None
        min_distance = 64

        for comp in existing_complaints:
            comp_hash = comp.get("image_hash")
            if comp_hash:
                dist = self.compare_hashes(target_hash, comp_hash)
                if dist < min_distance:
                    min_distance = dist
                    best_match = comp

        is_duplicate = min_distance <= 6
        dup_score = 0.0
        match_info = None

        if is_duplicate and best_match:
            # Distance 0 => score 0.95, Distance 6 => score 0.60
            dup_score = max(0.5, 1.0 - (min_distance / 12.0))
            match_info = {
                "matched_complaint_id": best_match.get("id"),
                "matched_title": best_match.get("title"),
                "hamming_distance": min_distance,
                "similarity_pct": round((1.0 - (min_distance / 64.0)) * 100, 1)
            }

        return {
            "duplicate_score": round(dup_score, 4),
            "is_duplicate": is_duplicate,
            "min_distance": min_distance,
            "match_info": match_info
        }

    def analyze_full_forensics(self, image_path: str, existing_complaints: list = None):
        """
        Aggregates ELA, EXIF, and Duplicate checks into composite forensic score s_for.
        Formula: s_for = 0.45 * ela_score + 0.30 * exif_score + 0.25 * duplicate_score
        """
        if existing_complaints is None:
            existing_complaints = []

        ela_res = self.compute_ela(image_path)
        exif_res = self.inspect_exif(image_path)
        dhash_str = self.compute_dhash(image_path)
        dup_res = self.check_duplicate(dhash_str, existing_complaints)

        # Weighted combination for forensic branch
        s_for = (
            0.45 * ela_res["ela_score"] +
            0.30 * exif_res["exif_score"] +
            0.25 * dup_res["duplicate_score"]
        )

        reasons = []
        if ela_res.get("suspicious"):
            reasons.append("ELA indicates high compression divergence (potential digital splicing or copy-move forgery)")
        if exif_res.get("flags"):
            reasons.extend(exif_res["flags"])
        if dup_res.get("is_duplicate"):
            reasons.append(f"Perceptual image hash matches existing complaint #{dup_res['match_info']['matched_complaint_id']} ({dup_res['match_info']['similarity_pct']}% visual match)")

        return {
            "s_for": round(min(1.0, max(0.0, s_for)), 4),
            "image_hash": dhash_str,
            "ela": ela_res,
            "exif": exif_res,
            "duplicate": dup_res,
            "reasons": reasons
        }
