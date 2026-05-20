# Model Limitations & Improvement Roadmap

This file is updated after each task where a limitation is discovered.
**Plain English — every acronym explained. Brief entries only.**

---

## Project Scaffold — 2026-05-05

**Limitation found:** The model is trained only on 2D image slices from a single Kaggle dataset. Real hospitals use 3D MRI volumes (called DICOM files) that have many more dimensions of information.

**Why it happens:** Processing 3D DICOM volumes requires much more memory and compute than a standard laptop or free Google Colab (a free cloud GPU service) can provide. Converting 3D to 2D slices loses some spatial context — the relationship between adjacent slices that a radiologist would naturally consider.

**How to fix it (future):**
- In v2, use the BraTS dataset (Brain Tumor Segmentation — a high-quality 3D medical imaging dataset) after extracting 2D slices with proper 3D context features.
- Consider a 3D CNN (3D Convolutional Neural Network) architecture when more compute is available.

---

**Limitation found:** The OOD (Out-of-Distribution) gate — which checks whether the uploaded image is actually a brain MRI — currently uses simple visual statistics (color, brightness, edge density) as a fallback. This is less reliable than a trained classifier.

**Why it happens:** Training a proper OOD classifier requires assembling a dataset of "not brain MRI" images (chest X-rays, random photos, etc.), which takes extra time. The heuristic fallback requires zero extra training.

**How to fix it (future):**
- Train the MobileNetV2 (a small, fast neural network) OOD gate using ~1,000 brain MRI images and ~1,000 non-MRI images to achieve >98% rejection accuracy.
- This is already designed in `src/model/ood_gate.py` — it just needs the training data and a Colab training run.

---

**Limitation found:** The model is trained on binary labels (tumor / no tumor) and does not distinguish between tumor types like Glioma, Meningioma, or Pituitary tumors.

**Why it happens:** Binary classification was chosen for v1 to maximize accuracy with limited data. Multi-class classification (predicting the specific tumor type) is harder and requires that the class labels are clinically verified — the Kaggle dataset labels have not been confirmed by a doctor for this project yet.

**How to fix it (future):**
- Have a radiologist confirm or correct the tumor type labels from the Kaggle dataset.
- Retrain the same EfficientNetB0 architecture with 4 output classes (no_tumor, glioma, meningioma, pituitary) — the code already supports this via `config.yaml` (`num_classes`).

---

**Limitation found:** The model may perform noticeably worse on MRI images from hospitals or machines that were not represented in the Kaggle training data. This is called "domain shift."

**Why it happens:** Every MRI machine brand (Siemens, GE, Philips) produces slightly different image textures, contrasts, and resolutions. A model trained on one set of machines may not generalize perfectly to another — even if both show brain tumors.

**How to fix it (future):**
- Test the model on the BRISC 2025 dataset (6,000 expert-annotated scans from different sources) to measure real-world generalization.
- Apply test-time augmentation (TTA): run each image through the model multiple times with slight variations and average the predictions for a more robust result.

---

<!-- Add new entries below after each task where a limitation is discovered. -->
