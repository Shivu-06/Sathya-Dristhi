# SatyaDrishti: Fake Complaint Detection Using Computer Vision

**Autonomous Grievance Redressal and Evidence Verification Platform for BBMP Bengaluru**  
*Department of CSE (Data Science), Dayananda Sagar University, Bengaluru, India*  
*Authors: Vamshi Reddy, Ullas B K, Shivakumar S, Prof. Kishor Malakar, Thejas*

---

## 🌟 Overview

**SatyaDrishti** is an AI-powered complaint verification platform engineered for Bruhat Bengaluru Mahanagara Palike (BBMP) to eliminate fake, reused, and manipulated civic grievance submissions.

When citizens report potholes, garbage mounds, water leakages, or broken streetlights, SatyaDrishti’s 4-branch multimodal AI engine analyzes photographic and textual evidence in real-time, assigning a composite **Fraud Score ($S$)**:
- **Genuine Complaints ($S < 0.38$)**: Fast-tracked directly to the front of the resolution queue (`Verified-low`).
- **Suspicious Submissions ($S \ge 0.60$)**: Routed to a prioritized, ranked investigator queue (`Flagged`) accompanied by plain-language diagnostic explanations.

---

## 📐 Multimodal Mathematical Architecture

### Composite Fraud Score (Equation 3):
$$S = w_1 s_{img} + w_2 s_{for} + w_3 s_x + w_4 s_{txt}$$
Where:
- $w_1 = 0.35$ — **CNN Image Authenticity Classifier ($s_{img}$)**: 8 forensic convolution kernels (Sobel, Laplacian, High-pass) capturing localized edge anomalies and synthetic artifacts.
- $w_2 = 0.25$ — **Image Forensics ($s_{for}$)**: Error Level Analysis (ELA) JPEG compression residual variance + EXIF digital tampering software tags (Photoshop/Canva) + Perceptual difference hashing (dHash) duplicate detection.
- $w_3 = 0.25$ — **Cross-Modal Matching ($s_x$)**: Vision-language semantic cosine distance $s_x = 1 - \cos(e_{img}, e_{txt})$ detecting contradictions between photographic category and written text.
- $w_4 = 0.15$ — **NLP Text Credibility ($s_{txt}$)**: Lexical hyperbole triggers, extreme brevity, and automated boilerplate detection.

---

## 🚀 Key Features

1. **Citizen Portal (`/dashboard`)**:
   - Photographic grievance submission with client-side drag-and-drop preview.
   - **Voice Assistant**: Integrated Web Speech API speech-to-text dictation.
   - **GPS Auto-Detection**: HTML5 Geolocation coordinates tagging + Bengaluru BBMP Ward selector.
   - Instant AI triage assessment modal with live branch score visualization.
   - Track status history: `Submitted` → `Verified-low` → `Under action` → `Closed`.

2. **BBMP Investigator Workspace (`/investigator`)**:
   - **Ranked Queue**: Auto-sorted by Fraud Score $S$ descending (high-risk first).
   - **Deep Forensic Inspection**: Side-by-side comparison of original evidence vs **Error Level Analysis (ELA) heatmap**.
   - **Explainable Diagnostics**: Plain-language reasoning explaining why evidence was flagged.
   - Status actions: Accept/Verify, Issue Work Order, Reject as Fraud, Flag for Field Audit.

3. **IEEE Paper Live Evaluation Dashboard (`/evaluation`)**:
   - Table I (Related Directions Comparison), Table II (Tech Stack), Table III (Server Routes), Table IV (Lifecycle States), Table VI (Evaluation Metrics).
   - Figure 6 Binary Confusion Matrix (TP, TN, FP, FN).
   - Workload Reduction Analysis: $T_{triage} = N \cdot t_a + p \cdot N \cdot t$.

4. **Distribution & Model Checkpoint Tools**:
   - **1-Click Project ZIP Export**: Download clean standalone project ZIP via `/api/download-zip` or `python export_project.py`.
   - **Model Downloader**: `python ai_service/download_models.py` for downloading open-source MobileNetV2/ResNet/CLIP checkpoints.
   - **Evaluation Benchmarking**: `python ai_service/train_and_evaluate.py` to retrain and validate metrics.

---

## ⚡ Quick Start & Setup

### Prerequisites:
- Node.js (v18+)
- Python (v3.10+) with `numpy`, `pillow`, `fastapi`, `uvicorn`

### 1. Launch the Platform (1-Click on Windows):
Double-click `run_project.bat` or run:
```bash
# Terminal 1: Start Python AI Microservice (port 5001)
python ai_service/ai_engine.py

# Terminal 2: Start Express Backend (port 5000)
node server/server.js
```
Open **[http://localhost:5000](http://localhost:5000)** in your browser!

### 2. Demo User Credentials:
- **Citizen Account**:
  - Email: `citizen@bbmp.gov.in`
  - Password: `password123`
- **BBMP Investigator Account**:
  - Email: `investigator@bbmp.gov.in`
  - Password: `admin123`
*(Both accounts are pre-seeded and have 1-click auto-fill buttons on `/login`)*

---

## 📊 Experimental Results (IEEE Table VI)

| Configuration | Accuracy (%) | Precision (%) | Recall (%) | F1-Score (%) |
| :--- | :---: | :---: | :---: | :---: |
| **CNN Only** | 78.50% | 76.20% | 81.00% | 78.53% |
| **+ Image Forensics** | 88.75% | 89.10% | 87.50% | 88.29% |
| **+ Text + Cross-Modal (Multimodal)** | **96.25%** | **97.40%** | **95.00%** | **96.18%** |

---

## 📦 Exporting Project Archive
To package the complete project into a distribution zip:
```bash
python export_project.py
```
Outputs `SatyaDrishti_Project_Distribution.zip` ready for sharing, submission, or deployment.
