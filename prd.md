# Brain Tumor MRI Classification — Clinical Screening Prototype
## Product Requirements Document (PRD)

---

### 0. Document Metadata

| Field | Value |
|---|---|
| **Owner** | Solo Builder / ML Student |
| **Reviewers** | Academic Supervisor, (Future) Clinical Advisor |
| **Status** | Draft v0.2 |
| **Created** | 2026-05-05 |
| **Last Updated** | 2026-05-05 |
| **Target Ship** | v1.0 → 4 weeks from start |
| **Repo** | TBD (Open Source — GitHub) |
| **Designs** | TBD (Streamlit prototype → Figma for v2) |
| **Type** | ML/AI Model + Web App Prototype → Full-Stack App (v2) |

---

### 1. TL;DR

We are building an open-source, web-based prototype for Brain Tumor MRI binary classification (Tumor vs. No Tumor), designed as an initial clinical screening aid for doctors and radiologists. The system combines a transfer-learning CNN (EfficientNetB0), a dual-confidence threshold engine (flag high-confidence results decisively, reject uncertain ones for manual review), an Out-of-Distribution (OOD) gate that rejects non-brain-MRI uploads before they reach the classifier, and a Grad-CAM explainability layer that shows doctors *why* the model made its prediction. v1 ships as a Streamlit prototype; v2 evolves into a FastAPI + React full-stack open-source application, with the model retrained on doctor-validated multi-class tumor labels.

---

### 2. Intent & Background

**Intent:** Radiologists and clinicians face unsustainable caseload growth — AI cannot replace them, but it can act as a reliable, explainable "second opinion" that triages clear cases, highlights anomalies, and explicitly tells a doctor when it is not confident enough to be trusted. This project builds that tool.

**Background (Academic Context):** This project directly addresses the class objectives: studying and understanding the medical domain, building a robust image preprocessing and augmentation pipeline, applying transfer learning as the ML methodology, training and evaluating a binary classification model, and producing a full performance analysis (accuracy, precision, recall, F1, confusion matrix). It goes beyond the minimum to add clinical-grade features (OOD detection, Grad-CAM explainability, and a dual-threshold confidence engine) that demonstrate real-world ML engineering competence and serve as a strong portfolio artifact.

**Why Binary First:** Starting with Tumor vs. No-Tumor maximizes model accuracy before introducing complexity. Multi-class (Glioma, Meningioma, Pituitary) will follow in v2, but only after the model's binary performance is validated and real doctors have confirmed tumor type labels from the Kaggle classes — this avoids inheriting any mislabeling from the source dataset into clinical decisions.

**Why This Matters (the v2 Vision):** The v2 full-stack open-source app (FastAPI + React) will allow clinics to self-host the tool, maintain patient scan history, and eventually log doctor feedback per scan — creating a feedback loop that continuously improves the model's multi-class accuracy with real-world annotations.

---

### 3. Project Type & Description

**Type:** ML/AI Model + Web App Prototype (Browser-accessible, CPU-runnable)
→ Future: Full-Stack Web Application (open-source, self-hostable)

**v1 Description:** A deep-learning classification pipeline paired with a Streamlit web interface. A user drags and drops a 2D brain MRI slice (JPG/PNG). Before classification, the image passes through an OOD gate ("Is this a brain MRI?"). If it passes, the core EfficientNetB0 classifier produces a probability score. The dual-threshold engine then routes the result into one of three UX states: Tumor Detected, No Tumor Detected, or Manual Review Required. Every result (above threshold) includes a Grad-CAM heatmap overlay showing which brain regions influenced the prediction.

**v2 Description (Future):** A full-stack web application with a FastAPI backend, React frontend, PostgreSQL patient history database, user authentication, and a doctor feedback loop for multi-class annotation. Designed for open-source community hosting by small clinics or academic medical centers.

---

### 4. Objectives & Non-Goals

**User Goals (v1):**
1. Upload a brain MRI image without any technical knowledge — one drag, one click.
2. Receive an immediate, visually clear classification result with a confidence percentage.
3. See a heatmap overlay that shows *where* in the MRI the model detected anomalies.
4. Be explicitly warned and given raw probabilities when the model is uncertain (<90%).
5. Have the system reject the upload entirely if it is not a brain MRI image.

**Academic / Project Goals:**
1. Demonstrate end-to-end ML pipeline competency: EDA → preprocessing → augmentation → transfer learning → evaluation.
2. Achieve Recall ≥ 95% and F1 ≥ 0.90 on the hold-out test set (class requirement).
3. Produce a clean, well-documented, open-source codebase that can evolve into a full-stack SaaS product.
4. Create a modular training pipeline so swapping binary labels for multi-class labels requires changing one config file, not rewriting code.

**Non-Goals (v1):**
- No multi-class tumor type identification (Glioma, Meningioma, Pituitary) in v1. This requires doctor-validated labels first.
- No full-stack architecture (database, user authentication, patient history). Deferred to v2.
- No processing of raw 3D MRI volumes (DICOM/NIfTI format). MVP accepts 2D image slices only.
- No HIPAA/GDPR compliance implementation. Prototype uses only public, anonymized datasets.
- No real-time processing of multiple concurrent uploads. Single-image inference per session.
- No mobile-native app. Browser-accessible is sufficient.

---

### 5. Users, Personas & Permissions

**Personas:**

| Persona | Profile | Key Need | Pain Point |
|---|---|---|---|
| **Dr. Sarah** (Radiologist) | Experienced clinician, non-technical, high trust bar | Fast, honest second opinion | Does not want a "black box" that is confidently wrong — needs to see *why* |
| **Dr. Ahmed** (Resident/Junior Doctor) | Learning, higher caseload, less experience | Flag for review; identify which scans need senior attention | Cannot afford to miss a tumor; overwhelmed by volume |
| **Academic Reviewer / Recruiter** | Technical, evaluating code quality and ML methodology | Clean notebooks, sound evaluation metrics, thoughtful architecture | Generic class projects with no real-world application thought |
| **Future Clinic Admin (v2)** | Non-technical, manages self-hosted deployment | One-command setup, scan history dashboard | Cannot manage complex infrastructure |

**Permissions (v1):** Open prototype — no authentication required. All users have identical access.

**Permissions (v2 — planned):**

| Capability | Admin | Doctor | Viewer |
|---|---|---|---|
| Upload & analyze MRI | ✅ | ✅ | ❌ |
| View own scan history | ✅ | ✅ | ✅ |
| View all clinic scans | ✅ | ❌ | ❌ |
| Submit doctor feedback / annotation | ✅ | ✅ | ❌ |
| Manage users | ✅ | ❌ | ❌ |
| Export reports | ✅ | ✅ | ❌ |

---

### 6. Workflow & User Experience

**Entry Point:** User opens the web interface URL (local: `http://localhost:8501` / hosted: HuggingFace Spaces or Streamlit Community Cloud).

**Core Experience (Happy Path):**

```
1. Landing page: Minimal UI — title, short disclaimer, drag-and-drop upload zone.
2. User drags a brain MRI image (JPG/PNG, <10MB) onto the upload zone.
3. [OOD Gate, <0.5s]: System checks "Is this a brain MRI?"
   → If NO: Immediate amber rejection card — "This does not appear to be a brain MRI.
     Please upload a 2D brain MRI slice in JPG or PNG format."
   → If YES: Proceed to classification.
4. [Classifier, <2.5s]: EfficientNetB0 runs inference. Dual-threshold engine evaluates result.
5. Result display — one of three states:
```

**State A — Tumor Detected (confidence ≥ 90%):**
> Red card: "⚠ Tumor Detected — 96% Confidence"
> Grad-CAM heatmap overlay: MRI with highlighted region the model focused on.
> Sub-text: "Recommend immediate clinical review. This result is provided as a screening aid only."

**State B — No Tumor Detected (confidence ≥ 90% on No-Tumor class):**
> Green card: "✓ No Tumor Detected — 94% Confidence"
> Grad-CAM heatmap overlay: Shows regions evaluated.
> Sub-text: "Routine follow-up recommended per clinical protocol."

**State C — Uncertain Result (neither class reaches 90%):**
> Amber card: "⚠ Uncertain Result — Manual Review Required"
> Raw probabilities displayed: "Tumor: 67% | No Tumor: 33%"
> No Grad-CAM shown (unreliable when model is uncertain).
> Sub-text: "The model's confidence is below the clinical safety threshold. A radiologist must review this scan."

**Edge Cases & Empty States:**

| Scenario | Behavior |
|---|---|
| Non-image file uploaded (PDF, DOCX, etc.) | Immediate format rejection before any processing |
| Corrupt or unreadable image file | Error message: "File could not be read. Please re-upload." |
| Image too small (<50×50px) | Rejection: "Image resolution too low for analysis." |
| Non-brain MRI (chest X-ray, CT scan, photo) | OOD gate rejects with specific message |
| Completely black or white image | OOD gate rejects |
| Slow network / inference timeout | Spinner with "Analyzing..." → timeout error after 10s |

---

### 7. Epics → User Stories

---

**Epic A: Domain Study & Data Pipeline** *(Priority: P0 | Release: v1.0)*
*Addresses class requirement: "Etudier et comprendre le métier" + "Prétraiter un dataset d'images"*

**Story A1** — Dataset Acquisition & EDA
> As an ML engineer, I want to acquire, explore, and understand the brain tumor MRI dataset so I can make informed preprocessing decisions.

Acceptance Criteria:
- [ ] Primary dataset downloaded from Kaggle (masoudnickparvar/brain-tumor-mri-dataset — 7,023 images, 4 classes)
- [ ] EDA notebook shows: class distribution bar chart, sample images per class (3×4 grid), image size distribution histogram, pixel intensity distribution
- [ ] Class imbalance documented: any class with <15% representation flagged as requiring augmentation
- [ ] At least 5 domain insights documented (e.g., "MRI scans show high variance in skull cropping", "glioma images tend to be darker")
- [ ] Binary label mapping defined: `{glioma, meningioma, pituitary} → "tumor"`, `{no_tumor} → "no_tumor"` and saved in `config.yaml`

**Story A2** — Preprocessing Pipeline
> As an ML engineer, I want a reproducible preprocessing pipeline so every image fed to the model is standardized regardless of source variation.

Acceptance Criteria:
- [ ] Pipeline function `preprocess_image(img_path) → tensor` implemented in `src/data/preprocessing.py`
- [ ] Steps applied in order: (1) read with OpenCV, (2) convert BGR→RGB, (3) resize to 224×224, (4) normalize to ImageNet mean/std `([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])`, (5) convert to PyTorch tensor
- [ ] Preprocessing is invertible for Grad-CAM visualization (denormalize function exists)
- [ ] Pipeline tested on 5 edge-case images (very dark, very bright, rotated, small, non-square)
- [ ] Processing time per image < 50ms on CPU

**Story A3** — Data Augmentation & Split Strategy
> As an ML engineer, I want data augmentation and a clean train/val/test split so the model generalizes beyond the training distribution.

Acceptance Criteria:
- [ ] Dataset split: 70% train / 15% val / 15% test — split is stratified (equal class ratios preserved across all three sets)
- [ ] Split is reproducible (fixed `random_seed = 42`) and saved as CSV index files
- [ ] Augmentation applied to training set only (never val/test): RandomHorizontalFlip(p=0.5), RandomRotation(±15°), ColorJitter(brightness=0.2, contrast=0.2), RandomAffine(translate=(0.1, 0.1))
- [ ] Augmented dataset size documented in notebook
- [ ] Class balance after augmentation verified — no class should be >2× another

---

**Epic B: OOD Detection Gate** *(Priority: P0 | Release: v1.0)*
*Addresses the "Users upload random, non-MRI images" failure mode identified in pre-mortem*

**Story B1** — OOD Classifier Training
> As a system architect, I want a lightweight binary gate model so non-brain-MRI images are rejected before reaching the main classifier.

Acceptance Criteria:
- [ ] OOD gate is a separate lightweight model (MobileNetV2 fine-tuned or image statistics heuristic) trained as "brain_mri" vs. "not_brain_mri"
- [ ] Negative dataset assembled: ~500 images of non-brain content (chest X-rays, natural photos, CT scans, random stock images) — sources documented
- [ ] OOD gate achieves ≥98% precision on brain MRI class (almost never rejects real MRIs)
- [ ] OOD gate achieves ≥90% recall on the "not brain MRI" class (catches most non-medical images)
- [ ] Gate inference time < 200ms on CPU
- [ ] Gate model saved separately as `models/ood_gate.pt`

**Story B2** — OOD Gate Integration
> As a user, I want the system to detect and reject non-MRI uploads immediately so the classifier never produces a misleading result on irrelevant images.

Acceptance Criteria:
- Given a user uploads a JPG of a cat, dog, or natural scene → OOD gate returns `is_brain_mri = False` → UI shows amber rejection card, classifier is never called
- Given a user uploads a chest X-ray → same rejection flow
- Given a user uploads a valid brain MRI → OOD gate returns `is_brain_mri = True` → classifier proceeds normally
- [ ] Rejection message is specific: "This does not appear to be a brain MRI scan."
- [ ] Gate result logged as event `ood_rejection_triggered` with `image_hash` (no PII)

---

**Epic C: Core Classification Model** *(Priority: P0 | Release: v1.0)*
*Addresses class requirement: "Extraire les caractéristiques pertinentes / Entraîner un modèle"*

**Story C1** — Transfer Learning Setup
> As an ML engineer, I want to use a pre-trained EfficientNetB0 as a feature extractor so the model trains in minutes on Colab, not days.

Acceptance Criteria:
- [ ] EfficientNetB0 loaded from `torchvision.models` with `weights=EfficientNet_B0_Weights.IMAGENET1K_V1`
- [ ] All base layers frozen in Phase 1 training; only classification head (`nn.Linear(1280, 2)`) is trainable
- [ ] Phase 1 training: 10 epochs, lr=1e-3, Adam optimizer, CrossEntropyLoss
- [ ] Phase 2 (fine-tuning): Unfreeze last 2 convolutional blocks, lr=1e-4, 5 additional epochs
- [ ] Model checkpoint saved after every epoch: `checkpoints/epoch_{n}_val_f1_{score}.pt`
- [ ] Training runs end-to-end on Google Colab T4 GPU in < 30 minutes total
- [ ] Training notebook cell outputs preserved (loss curves, accuracy per epoch)

**Story C2** — Recall Optimization
> As a doctor, I want the model to minimize missed tumors (False Negatives) above all else, because a missed tumor is far more dangerous than a false alarm.

Acceptance Criteria:
- [ ] Loss function uses class weights: `weight = [1.0, 2.5]` (penalizing missed tumors more heavily than false alarms)
- [ ] Threshold tuning notebook: plots Precision-Recall curve, identifies optimal classification threshold for Recall ≥ 95%
- [ ] Final classification threshold documented in `config.yaml` as `classification_threshold` (default 0.5 but tunable)
- [ ] On the hold-out test set: Recall ≥ 95%, F1 ≥ 0.90, Accuracy ≥ 92%
- [ ] Confusion matrix produced and annotated with clinical interpretation (which quadrant matters most and why)

**Story C3** — Dual-Confidence Threshold Engine
> As a doctor, I want the system to give me a decisive result when it is highly confident, and explicitly tell me it is uncertain when it is not.

Acceptance Criteria:
- Given `P(tumor) ≥ 0.90` → system returns `{"label": "Tumor Detected", "confidence": P(tumor), "state": "HIGH_CONFIDENCE_TUMOR"}`
- Given `P(no_tumor) ≥ 0.90` → system returns `{"label": "No Tumor Detected", "confidence": P(no_tumor), "state": "HIGH_CONFIDENCE_CLEAR"}`
- Given neither class reaches 0.90 → system returns `{"label": "Manual Review Required", "state": "UNCERTAIN", "probabilities": {"tumor": ..., "no_tumor": ...}}`
- [ ] Thresholds externalized in `config.yaml` as `high_confidence_threshold: 0.90` for easy tuning
- [ ] Unit tests for all three threshold states with mocked probability inputs

---

**Epic D: Explainability Layer (Grad-CAM)** *(Priority: P0 | Release: v1.0)*
*Addresses the "black box" trust problem — doctors need to see WHY the model predicted what it did*

**Story D1** — Grad-CAM Heatmap Generation
> As an ML engineer, I want to generate a Grad-CAM heatmap for every high-confidence prediction so the model's reasoning is visually interpretable.

Acceptance Criteria:
- [ ] `pytorch-grad-cam` library used (`pip install grad-cam`)
- [ ] Target layer: last convolutional layer of EfficientNetB0 (`features[-1]`)
- [ ] `generate_gradcam(model, image_tensor, target_class) → heatmap_array` function in `src/explainability/gradcam.py`
- [ ] Heatmap is resized to match original image dimensions (224×224)
- [ ] Heatmap applied as a semi-transparent color overlay (jet colormap, alpha=0.4) on the original MRI image
- [ ] Heatmap generation adds < 500ms to total inference time on CPU

**Story D2** — Heatmap Display in UI
> As a doctor, I want to see the Grad-CAM heatmap overlay next to the MRI image so I can verify whether the model is looking at the correct brain region.

Acceptance Criteria:
- [ ] UI shows original MRI and Grad-CAM overlay side-by-side in HIGH_CONFIDENCE states (A and B)
- [ ] Heatmap NOT shown in UNCERTAIN state (model's attention is unreliable when confidence is low)
- [ ] Caption below heatmap: "Highlighted regions indicate areas of highest model focus. This is not a clinical segmentation."
- [ ] Color scale legend displayed (blue = low attention, red = high attention)
- [ ] User can toggle heatmap overlay on/off without re-running inference

---

**Epic E: Model Evaluation & Academic Analysis** *(Priority: P0 | Release: v1.0)*
*Directly addresses class requirement: "Analyser les performances du modèle"*

**Story E1** — Full Performance Analysis Notebook
> As an ML student, I want a comprehensive evaluation notebook so I can present all required metrics to the academic reviewer.

Acceptance Criteria:
- [ ] Evaluation run on held-out test set only (never seen during training or validation)
- [ ] Metrics computed and displayed: Accuracy, Precision, Recall (Sensitivity), Specificity, F1-Score, AUC-ROC
- [ ] Confusion matrix plotted as a heatmap with absolute counts and percentages
- [ ] Per-class metrics in a formatted table
- [ ] ROC curve plotted with AUC annotated
- [ ] Precision-Recall curve plotted with AUC annotated
- [ ] At least 5 misclassified examples shown with their Grad-CAM heatmaps and an analysis of *why* the model failed

**Story E2** — Generalization Test (External Validation)
> As an ML engineer, I want to test the final model on images from a source it has never seen so I can report honestly on real-world generalization.

Acceptance Criteria:
- [ ] At least 50 images sourced from a different dataset (e.g., Navoneel Brain MRI dataset on Kaggle, or manually downloaded from published papers with attribution)
- [ ] Model performance on external set documented: if Recall drops >10% vs. test set, this is flagged as an overfitting warning in the notebook
- [ ] Dataset source, image count, and any preprocessing differences documented
- [ ] Finding logged in the project README as a "Known Limitations" section

---

**Epic F: Web Prototype UI (Streamlit)** *(Priority: P1 | Release: v1.0)*
*Makes the project interactive and presentable without full-stack complexity*

**Story F1** — Upload & Analysis Flow
> As a user, I want to upload an MRI image and receive a result through a web browser without touching any code.

Acceptance Criteria:
- [ ] `streamlit run app.py` starts the application with zero additional configuration
- [ ] Drag-and-drop file uploader accepts JPG, PNG, JPEG only
- [ ] File size limit enforced: 10MB max
- [ ] "Analyze" button triggers the full pipeline: OOD gate → classifier → Grad-CAM → result display
- [ ] Spinner + "Analyzing..." text visible during processing
- [ ] Total time from button click to result display < 3 seconds on CPU (measured on 16GB RAM laptop)

**Story F2** — Three-State Result Cards
> As a doctor, I want visually distinct result cards for each confidence state so I can interpret the result at a glance without reading fine print.

Acceptance Criteria:
- [ ] State A (Tumor): Red-background card, ⚠ icon, bold confidence %, clinical disclaimer
- [ ] State B (No Tumor): Green-background card, ✓ icon, bold confidence %, routine follow-up note
- [ ] State C (Uncertain): Amber-background card, ⚠ icon, raw probability table, "manual review" instruction
- [ ] OOD Rejection: Amber card, no icon, rejection reason, file format instructions
- [ ] All cards readable on mobile browser (responsive layout)
- [ ] Disclaimer present on every result: "This tool is a screening prototype. It does not replace clinical diagnosis."

**Story F3** — Grad-CAM Display
> As a doctor, I want to see the original MRI and the heatmap side-by-side so I can judge whether the model's focus region is clinically meaningful.

Acceptance Criteria:
- [ ] Two columns: left = original uploaded MRI, right = Grad-CAM overlay
- [ ] Toggle checkbox: "Show heatmap overlay" (default: on)
- [ ] Caption and color scale legend rendered below heatmap
- [ ] Images scale to fit viewport without overflow

**Story F4** — Deployment to Free Hosting
> As a portfolio builder, I want the app hosted on a free public URL so anyone can access it without running code locally.

Acceptance Criteria:
- [ ] App deployed to Streamlit Community Cloud or HuggingFace Spaces (free tier)
- [ ] `requirements.txt` or `packages.txt` pinned to exact versions
- [ ] Model weights hosted via HuggingFace Hub or Git LFS (not committed directly to GitHub if >100MB)
- [ ] Deployment URL documented in README

---

**Epic G: Full-Stack Evolution** *(Priority: P2 | Release: v2.0 — Future)*

**Story G1** — FastAPI Backend
> As a developer, I want a REST API backend so the ML model is decoupled from the UI and can serve multiple frontends.

Acceptance Criteria:
- [ ] `POST /api/v1/analyze` endpoint accepts multipart image upload, returns JSON `{label, confidence, state, gradcam_url}`
- [ ] `POST /api/v1/feedback` accepts doctor annotation per scan (tumor_type, correct_prediction boolean)
- [ ] `GET /api/v1/history` returns paginated scan history for authenticated user
- [ ] OpenAPI docs auto-generated at `/docs`
- [ ] API client auto-generated from OpenAPI spec using Orval

**Story G2** — React Frontend
> As a clinic user, I want a modern web interface with scan history so I can track previous analyses.

**Story G3** — Database & Auth
> As a clinic admin, I want secure user accounts and persistent scan history.

**Story G4** — Doctor Feedback Loop
> As a doctor, I want to annotate whether the AI prediction was correct so the model can be retrained with real-world feedback.

---

### 8. Functional Requirements

| ID | Requirement |
|---|---|
| FR-01 | System must accept 2D image uploads in JPG/PNG/JPEG format only |
| FR-02 | System must reject non-image files before any ML processing |
| FR-03 | System must run the OOD gate before the main classifier on every upload |
| FR-04 | The ML pipeline must use EfficientNetB0 with ImageNet pre-trained weights |
| FR-05 | Classification must apply the dual-confidence threshold: `if max(P) ≥ 0.90: decisive result else: manual review` |
| FR-06 | Grad-CAM heatmap must be generated and displayed for every HIGH_CONFIDENCE result |
| FR-07 | Grad-CAM must NOT be displayed for UNCERTAIN results |
| FR-08 | The training scripts must support binary classification by default, switchable to multi-class via `config.yaml` without code changes |
| FR-09 | Model checkpoints must be saved after every training epoch |
| FR-10 | Evaluation notebook must produce: confusion matrix, precision, recall, F1, AUC-ROC on hold-out test set |
| FR-11 | All confidence thresholds must be externalized in `config.yaml` |
| FR-12 | No PII may be logged at any point (no file names, no patient identifiers) |
| FR-13 | The application must be launchable with a single command: `streamlit run app.py` |

---

### 9. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Performance** | Total inference pipeline (OOD gate + classifier + Grad-CAM) < 3 seconds on CPU (16GB RAM) |
| **Performance** | OOD gate alone < 200ms |
| **Performance** | Grad-CAM generation < 500ms |
| **Portability** | Application runnable on any OS via `pip install -r requirements.txt` + `streamlit run app.py` |
| **Portability** | Training reproducible on Google Colab Free Tier (T4 GPU, 12GB RAM) with `random_seed = 42` |
| **Maintainability** | Code separated into: `src/data/`, `src/model/`, `src/explainability/`, `src/inference/`, `app.py`, `train.ipynb`, `evaluate.ipynb` |
| **Maintainability** | All hyperparameters and thresholds in `config.yaml` — no magic numbers in code |
| **Reliability** | Model must handle corrupt, tiny, or monochrome images without crashing — graceful error messages only |
| **Explainability** | Every high-confidence result must include a Grad-CAM heatmap |
| **Accessibility** | UI must be usable on mobile browser without horizontal scroll |
| **Reproducibility** | `random_seed = 42` used for all splits, model initialization, and augmentation |
| **Privacy** | No uploaded images stored on server beyond the current session |
| **Observability** | Structured local logs for every inference event (no PII) |

---

### 10. Dependencies

**Datasets:**

| Dataset | Images | Classes | Access | Notes | Recommendation |
|---|---|---|---|---|---|
| **masoudnickparvar/brain-tumor-mri-dataset** | 7,023 | 4 (glioma, meningioma, pituitary, no_tumor) | Kaggle (free) | Merger of Figshare + SARTAJ (cleaned) + Br35H. Fixed known glioma mislabeling in SARTAJ. | **PRIMARY — use this** |
| sartajbhuvaji/brain-tumor-classification-mri | ~3,264 | 4 | Kaggle (free) | Older, smaller, known glioma class label errors. Superseded by masoudnickparvar. | Avoid as primary |
| navoneel/brain-mri-images-for-brain-tumor-detection | ~253 | 2 (yes/no) | Kaggle (free) | Binary only, very small. | Use as external validation set |
| BRISC (2025) | 6,000 | 4 + segmentation masks | Kaggle / Figshare / Zenodo | Expert-annotated by radiologists, highest clinical quality, includes axial/sagittal/coronal planes. | Consider for v2 retraining |
| BraTS | ~1,000+ patients | Multi-class + 3D | CBICA (registration required) | 3D DICOM volumes — requires 2D slice extraction. High effort. | Out of scope for v1 |

**Infrastructure:**

| Tool | Purpose | Cost |
|---|---|---|
| Google Colab (Free Tier) | GPU training (T4, 12GB VRAM) | Free (with session limits) |
| HuggingFace Hub | Model weights hosting (>100MB files) | Free |
| Streamlit Community Cloud | App hosting | Free |
| Standard Laptop (CPU, 16GB RAM) | Local development, inference, UI testing | Owned |

**ML / Python Libraries:**

| Library | Version | Purpose |
|---|---|---|
| `torch` | ≥2.2 | Core ML framework |
| `torchvision` | ≥0.17 | EfficientNetB0 pretrained weights, transforms |
| `grad-cam` (pytorch-grad-cam) | ≥1.5 | Grad-CAM heatmap generation |
| `streamlit` | ≥1.33 | Web prototype UI |
| `opencv-python` | ≥4.9 | Image reading, preprocessing |
| `Pillow` | ≥10.0 | Image format handling |
| `numpy` | ≥1.26 | Array operations |
| `matplotlib` / `seaborn` | latest | EDA plots, confusion matrix |
| `scikit-learn` | ≥1.4 | Metrics, confusion matrix, train/test split |
| `pyyaml` | ≥6.0 | Config file loading |
| `kaggle` | latest | Dataset download in Colab |

**License Note:** All datasets (masoudnickparvar, navoneel) are under CC BY 4.0 or equivalent open licenses. Attribution required in README.

---

### 11. Technical Considerations

**Compute Constraints:**
- Training from scratch on a CPU is infeasible within the project timeline. Transfer learning (freeze base, train head) is mandatory.
- Phase 1: freeze all EfficientNetB0 base layers → train only the 2-class head for 10 epochs (~15 min on Colab T4).
- Phase 2: unfreeze last 2 convolutional blocks → fine-tune with low lr for 5 epochs (~10 min on Colab T4).
- Total training time target: < 30 minutes on Colab T4 GPU. CPU-only training not recommended.

**Architecture Choice — EfficientNetB0:**
EfficientNetB0 is chosen over alternatives because:
- Smallest EfficientNet variant (~5.3M parameters) — fast CPU inference
- ImageNet-pretrained features transfer well to grayscale-converted MRI (MRI images are loaded as RGB with 3 identical channels)
- Achieves competitive accuracy on this dataset (literature reports 97–98% on masoudnickparvar with fine-tuning)
- `pytorch-grad-cam` has first-class support for EfficientNet target layers

**OOD Detection Architecture:**
- Option A (Preferred): Lightweight MobileNetV2 binary classifier ("brain_mri" vs. "not_brain_mri") trained on ~1,000 images per class. ~2.2M parameters, very fast CPU inference.
- Option B (Fallback, simpler): Image statistics heuristics — check aspect ratio, pixel intensity distribution, edge density. Less accurate but zero training required. Use if Option A is deprioritized due to time.

**Image Variance Problem:**
MRI scans vary significantly in brightness, contrast, skull cropping, and slice orientation. Mitigations:
- ImageNet normalization standardizes pixel value ranges.
- ColorJitter augmentation teaches the model to handle brightness/contrast variance.
- RandomAffine handles slight cropping differences.
- During evaluation, note that cross-institution generalization will likely drop ~5–10% — this is expected and must be documented.

**Grad-CAM Target Layer:**
For EfficientNetB0 in PyTorch (`torchvision`), the correct target layer for `pytorch-grad-cam` is: `model.features[-1]` (the last convolutional block before the adaptive average pooling layer). Using an earlier layer produces lower-resolution maps; the final layer provides the best spatial resolution for this model.

**v2 Integration Points (planned):**
- FastAPI backend will wrap `src/inference/` as a standalone service. No changes to ML code required.
- PostgreSQL via SQLAlchemy for scan history and doctor feedback.
- React frontend consuming OpenAPI-generated Orval client.
- Docker Compose for self-hosted deployment.

---

### 12. Success Metrics

**North Star:** Recall (Sensitivity) on the hold-out test set — because in clinical screening, missing a real tumor (False Negative) is the worst outcome.

**Technical Metrics (class requirement):**

| Metric | Target | Baseline | Measurement Window | Source |
|---|---|---|---|---|
| Recall (Sensitivity) | ≥ 95% | ~50% (random classifier) | Hold-out test set | `evaluate.ipynb` |
| F1-Score | ≥ 0.90 | — | Hold-out test set | `evaluate.ipynb` |
| Accuracy | ≥ 92% | — | Hold-out test set | `evaluate.ipynb` |
| AUC-ROC | ≥ 0.97 | — | Hold-out test set | `evaluate.ipynb` |
| Inference Time (end-to-end) | < 3s | — | CPU laptop, 5-run average | Manual timing |
| OOD Gate Precision (brain MRI class) | ≥ 98% | — | OOD test set | `evaluate.ipynb` |

**User / Clinical Metrics:**

| Metric | Target | Notes |
|---|---|---|
| Uncertainty Rate | < 20% on test set | If >20% of test images trigger UNCERTAIN state, the model's feature extraction is too weak for clinical use |
| Grad-CAM Clinical Relevance | Qualitative review | At least 5 high-confidence predictions verified manually: does the heatmap highlight the actual tumor region? |
| OOD Rejection Rate on valid MRIs | < 2% | OOD gate must not reject valid brain MRI uploads (false rejections destroy trust) |

**Guardrails (do not game the North Star):**
- Precision must not fall below 0.85 while optimizing for Recall. A model that flags everything as "Tumor" achieves 100% Recall but is clinically useless.
- Uncertainty Rate must not be reduced by lowering the confidence threshold below 0.80. Threshold must never go below 0.85.

---

### 13. Instrumentation & Telemetry

*Local structured logging for MVP (Python `logging` module writing to `logs/inference.log`). No external analytics service. No cloud telemetry.*

**Analytics Events:**

| Event | When | Properties |
|---|---|---|
| `ood_gate_executed` | OOD gate runs | `result: pass/reject`, `latency_ms`, `image_hash` (sha256, no filename) |
| `ood_rejection_triggered` | OOD gate rejects | `latency_ms`, `image_hash` |
| `inference_executed` | Main classifier runs | `predicted_class`, `confidence_score`, `threshold_state` (HIGH_CONF_TUMOR / HIGH_CONF_CLEAR / UNCERTAIN), `latency_ms` |
| `fallback_triggered` | UNCERTAIN state reached | `tumor_probability`, `no_tumor_probability`, `latency_ms` |
| `gradcam_generated` | Grad-CAM runs | `latency_ms`, `target_class` |
| `pipeline_error` | Any unhandled exception | `error_type`, `stage` (ood/classifier/gradcam/ui), `message` |

**What is explicitly NOT logged:**
- Uploaded file name or path
- Any pixel data from the uploaded image
- User IP address or session identifier

**System Telemetry:**
- Log file: `logs/inference.log` (rotated daily, max 7 days retention)
- Format: JSON structured logs `{"timestamp": ..., "event": ..., "properties": {...}}`
- Error budget: 0 crashes per 100 inference calls is the target; any crash must be caught and logged gracefully

---

### 14. Planning for Failure (Pre-Mortem)

*Imagine it is Week 5. The project failed. What happened?*

| Risk | Cagan Type | Likelihood | Impact | Detection Signal | Mitigation / Fallback |
|---|---|---|---|---|---|
| **Model overfits to Kaggle dataset** — 99% accuracy on test, ~60% on external images | Feasibility | Medium | High | >10% Recall drop on external validation (Story E2) | Heavy augmentation from day 1; test on navoneel dataset before claiming success; document in README |
| **OOD gate falsely rejects valid MRI scans** — doctors can't use the tool | Usability | Medium | High | OOD false-rejection rate >2% on real MRI test set | Set OOD threshold conservatively (high precision on brain MRI class); provide manual override with disclaimer |
| **Grad-CAM highlights skull or background, not tumor** — destroys doctor trust | Value | Medium | High | Manual qualitative review of 5+ heatmaps on known-tumor images | Choose correct target layer (last conv block); if poor, try GradCAM++ or ScoreCAM alternatives from pytorch-grad-cam |
| **Google Colab disconnects mid-training** — lose all progress | Feasibility | High | Medium | Training stops unexpectedly | Save checkpoint every epoch; store to Google Drive with `drive.mount()`; resume from last checkpoint |
| **EfficientNetB0 cannot achieve Recall ≥ 95%** on this dataset | Feasibility | Low | High | Recall < 90% after fine-tuning | Increase class weight for tumor class (from 2.5 to 4.0); try ResNet50V2 as alternative backbone |
| **Confidence threshold of 90% is too strict** — UNCERTAIN rate >40% | Value | Medium | Medium | Uncertainty rate on test set >40% | Lower threshold to 0.85 (document the clinical trade-off); or improve model first |
| **pytorch-grad-cam incompatible with torchvision EfficientNetB0** | Feasibility | Low | Medium | AttributeError on target layer | Use `model.features[-1]` as target; fallback: Captum library which has native torchvision support |
| **Streamlit deployment fails** — model file too large for git | Feasibility | Medium | Low | GitHub push rejected (>100MB) | Store weights on HuggingFace Hub; load with `huggingface_hub.hf_hub_download()` at app startup |
| **Dataset has mislabeled images** — model learns wrong patterns | Value | Medium | Medium | Unexpectedly poor precision on specific classes | Use masoudnickparvar (already cleaned) not sartajbhuvaji; visually inspect 10 random samples per class |
| **v2 full-stack scope creeps into v1** — nothing ships | Viability | High | High | Week 3 spent on React setup instead of Streamlit | Hard freeze: v1 = Streamlit only. All v2 stories tagged P2 and blocked until v1 ships |

---

### 15. Milestones & Sequencing

| Phase | Week | Deliverables | Compute |
|---|---|---|---|
| **Phase 1: Data & EDA** | Week 1 | Kaggle dataset downloaded + EDA notebook complete + preprocessing pipeline + augmentation strategy + stratified split | CPU laptop |
| **Phase 2: Model Training** | Week 2 | EfficientNetB0 transfer learning (Phase 1 + Phase 2 fine-tuning) + OOD gate trained + threshold tuning + model checkpoint saved | Google Colab GPU |
| **Phase 3: Explainability + UI** | Week 3 | Grad-CAM integration + Streamlit app (all 3 confidence states + OOD rejection + heatmap display) | CPU laptop |
| **Phase 4: Evaluation + Polish** | Week 4 | Evaluate notebook (all metrics) + external validation + README + deployment to Streamlit Community Cloud / HuggingFace Spaces + repo polish | CPU laptop |

**Hard Constraints:**
- Training must complete in Google Colab before local inference development begins (Week 2 → Week 3 handoff).
- Streamlit app must be functional before evaluation notebook is finalized — app serves as a live demonstration of evaluation results.
- v2 (FastAPI + React) work must not begin until v1 is deployed and all class requirements are met.

**Effort Estimates:**
- Phase 1: ~12–15 hours
- Phase 2: ~10–12 hours (mostly Colab runtime, not active work)
- Phase 3: ~15–18 hours (Grad-CAM integration is the highest-risk task)
- Phase 4: ~8–10 hours

---

### 16. Open Questions & Decision Log

**Open Questions:**

- [ ] **OOD Gate Approach:** Use MobileNetV2 (higher accuracy, more setup) or image statistics heuristics (faster to build, less accurate)? Decision needed by end of Week 1. *Recommendation: MobileNetV2 if time permits, heuristics as fallback.*
- [ ] **Confidence Threshold Calibration:** Should the 90% threshold be fixed or calibrated per class separately (e.g., 92% for tumor, 88% for no-tumor)? Requires threshold analysis after training. Decision needed in Week 2.
- [ ] **External Validation Dataset:** navoneel dataset (~253 images) may be too small for a statistically meaningful external validation. Should we merge it with a second external source? Open — revisit in Week 3.
- [ ] **Doctor Partnership for v2:** How will we find and onboard doctors to validate multi-class tumor labels? No concrete plan yet. Needed before v2 multi-class retraining can begin.

**Decision Log:**

| Date | Decision | Rationale |
|---|---|---|
| 2026-05-05 | Binary classification (Tumor / No Tumor) for v1 | Maximizes accuracy before multi-class complexity; v2 will use doctor-validated labels for specific tumor types |
| 2026-05-05 | Dual 90% confidence threshold (not single) | A 90%-confident "No Tumor" is as clinically important to communicate as a 90%-confident "Tumor" — both deserve decisive results |
| 2026-05-05 | masoudnickparvar dataset chosen over sartajbhuvaji | Larger (7,023 vs 3,264 images), cleaned glioma class labels, merger of multiple validated sources |
| 2026-05-05 | EfficientNetB0 chosen over ResNet50 | 2–3× faster CPU inference, smaller model size, comparable accuracy; critical for sub-3s inference on CPU |
| 2026-05-05 | PyTorch chosen over TensorFlow/Keras | Better community support for pytorch-grad-cam; EfficientNetB0 in torchvision has clean pretrained weights API |
| 2026-05-05 | OOD detection promoted to P0 (not v2) | A model that confidently predicts "Tumor" on a photo of a cat destroys clinical credibility immediately |
| 2026-05-05 | Grad-CAM promoted to P0 (not optional) | Doctors do not trust "black box" percentages; heatmap is the minimum viable explainability for a clinical prototype |
| 2026-05-05 | Streamlit for v1 UI, FastAPI + React for v2 | Streamlit is 20 lines vs. full-stack weeks; v1 proves the ML pipeline, v2 proves the engineering architecture |

---

### 17. Out of Scope (v1)

- Multi-class tumor type identification (Glioma, Meningioma, Pituitary). Requires doctor-validated labels. Deferred to v2.
- Database, user authentication, patient history, or session persistence of any kind.
- DICOM or NIfTI (3D MRI volume) processing. 2D slices only.
- HIPAA / GDPR compliance — prototype uses only public, anonymized, non-PHI datasets.
- Real-time video or multi-frame MRI sequence analysis.
- Ensemble models or model comparison dashboards.
- Batch processing of multiple MRI images in one session.
- A/B testing framework or feature flag system.
- Any v2 full-stack work (FastAPI, React, PostgreSQL, Docker) — strictly blocked until v1 ships.
- Integration with PACS (Picture Archiving and Communication Systems) used in hospitals.
- Automatic report generation (PDF diagnostic reports).

---

### 18. Glossary & Appendix

**Glossary:**

| Term | Definition |
|---|---|
| **Recall (Sensitivity)** | `TP / (TP + FN)` — percentage of actual tumors correctly identified. The most critical metric for clinical screening; a missed tumor is the worst outcome. |
| **Precision** | `TP / (TP + FP)` — of all cases flagged as tumors, how many actually are. A false alarm sends a healthy patient for unnecessary additional testing. |
| **F1-Score** | Harmonic mean of Precision and Recall. Balanced metric when both matter. |
| **AUC-ROC** | Area Under the ROC Curve. Threshold-independent measure of the model's ability to discriminate between classes. ≥0.97 is excellent. |
| **Transfer Learning** | Using a CNN pre-trained on ImageNet (millions of natural images) and retraining only the final classification layer on brain MRI images. Saves weeks of compute. |
| **EfficientNetB0** | The smallest model in the EfficientNet family (B0–B7). ~5.3M parameters. Excellent accuracy-to-speed ratio. Suitable for CPU inference. |
| **Grad-CAM** | Gradient-weighted Class Activation Mapping. Produces a heatmap showing which pixels most influenced the model's classification decision. |
| **OOD Detection** | Out-of-Distribution Detection. A pre-classifier gate that checks "Is this input similar to what the model was trained on?" Rejects images outside the expected distribution. |
| **Dual-Confidence Threshold** | The decision engine in this system: a decisive result is only shown when either the Tumor OR the No-Tumor probability exceeds 90%. Below that, a manual review warning is displayed. |
| **BraTS** | Brain Tumor Segmentation Challenge. Gold-standard dataset with 3D MRI volumes and expert segmentation masks. Requires 3D→2D extraction. |
| **BRISC** | Brain Image Segmentation and Classification (2025). New expert-annotated dataset of 6,000 MRI scans. Candidate for v2 retraining. |
| **Confusion Matrix** | Table comparing predicted labels vs. actual labels: True Positives (TP), False Positives (FP), False Negatives (FN), True Negatives (TN). |
| **False Negative (FN)** | Model predicted "No Tumor" but the patient has a tumor. The most dangerous error type in this system. |
| **False Positive (FP)** | Model predicted "Tumor" but the patient is healthy. Causes unnecessary stress and follow-up testing. Less dangerous than FN in screening. |

**Appendix A — Recommended Project File Structure:**
```
brain-tumor-classifier/
├── config.yaml                    # All thresholds, hyperparameters, paths
├── app.py                         # Streamlit web application
├── requirements.txt               # Pinned dependencies
├── README.md                      # Setup, methodology, results, limitations
├── notebooks/
│   ├── 01_eda.ipynb               # Exploratory Data Analysis
│   ├── 02_training.ipynb          # Transfer learning training (Colab)
│   ├── 03_threshold_tuning.ipynb  # Precision-Recall threshold analysis
│   └── 04_evaluation.ipynb        # Full evaluation + confusion matrix
├── src/
│   ├── data/
│   │   ├── preprocessing.py       # preprocess_image(), denormalize_image()
│   │   ├── augmentation.py        # get_train_transforms(), get_val_transforms()
│   │   └── dataset.py             # PyTorch Dataset class
│   ├── model/
│   │   ├── classifier.py          # EfficientNetB0 wrapper, load_model()
│   │   └── ood_gate.py            # OOD gate model, is_brain_mri()
│   ├── inference/
│   │   └── predict.py             # run_full_pipeline() → ThresholdResult
│   └── explainability/
│       └── gradcam.py             # generate_gradcam(), overlay_heatmap()
├── models/                        # .pt weight files (or HuggingFace Hub pointers)
│   ├── classifier_best.pt
│   └── ood_gate.pt
├── logs/
│   └── inference.log              # Structured JSON inference logs
└── tests/
    └── test_threshold_engine.py   # Unit tests for confidence threshold states
```

**Appendix B — Confidence Threshold State Machine:**
```python
# config.yaml
high_confidence_threshold: 0.90

# src/inference/predict.py
def apply_threshold(tumor_prob: float, no_tumor_prob: float, threshold: float):
    if tumor_prob >= threshold:
        return {"state": "HIGH_CONFIDENCE_TUMOR", "label": "Tumor Detected",
                "confidence": tumor_prob, "show_gradcam": True}
    elif no_tumor_prob >= threshold:
        return {"state": "HIGH_CONFIDENCE_CLEAR", "label": "No Tumor Detected",
                "confidence": no_tumor_prob, "show_gradcam": True}
    else:
        return {"state": "UNCERTAIN", "label": "Manual Review Required",
                "probabilities": {"tumor": tumor_prob, "no_tumor": no_tumor_prob},
                "show_gradcam": False}
```

**Appendix C — Dataset Sources:**
- Primary: [masoudnickparvar/brain-tumor-mri-dataset](https://www.kaggle.com/datasets/masoudnickparvar/brain-tumor-mri-dataset) — 7,023 images, 4 classes, cleaned
- External Validation: [navoneel/brain-mri-images-for-brain-tumor-detection](https://www.kaggle.com/datasets/navoneel/brain-mri-images-for-brain-tumor-detection) — 253 images, binary
- Future (v2): [BRISC Dataset](https://www.nature.com/articles/s41597-026-06753-y) — 6,000 expert-annotated MRI scans

Sources:
- [Brain Tumor MRI Dataset (masoudnickparvar)](https://www.kaggle.com/datasets/masoudnickparvar/brain-tumor-mri-dataset)
- [BRISC: Annotated Dataset for Brain Tumor Segmentation and Classification](https://www.nature.com/articles/s41597-026-06753-y)
- [Deep Learning Approaches for Brain Tumor Detection: Systematic Review 2020–2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC12092918/)
- [Optimized deep learning for brain tumor detection with attention and Grad-CAM](https://www.nature.com/articles/s41598-025-04591-3)
