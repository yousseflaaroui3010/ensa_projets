# Brain Tumor MRI Classifier

An open-source clinical screening prototype that classifies brain MRI scans as **Tumor** or **No Tumor** using transfer learning, with visual explainability via Grad-CAM and an Out-of-Distribution safety gate.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download dataset (requires Kaggle account)
kaggle datasets download -d masoudnickparvar/brain-tumor-mri-dataset -p data --unzip

# 3. Run EDA + create splits
jupyter notebook notebooks/01_eda.ipynb

# 4. Train the model (Google Colab recommended for GPU)
# Open notebooks/02_training.ipynb in Colab
# Place the saved models/classifier_best.pt back in this folder

# 5. Tune threshold
jupyter notebook notebooks/03_threshold_tuning.ipynb

# 6. Evaluate
jupyter notebook notebooks/04_evaluation.ipynb

# 7. Launch the web app
streamlit run app.py
```

## Project Structure

```
├── app.py                     # Streamlit web interface
├── config.yaml                # All hyperparameters and thresholds
├── requirements.txt           # Python dependencies
├── src/
│   ├── data/
│   │   ├── preprocessing.py   # Image normalization pipeline
│   │   ├── augmentation.py    # Training data augmentation
│   │   └── dataset.py         # PyTorch Dataset + split utility
│   ├── model/
│   │   ├── classifier.py      # EfficientNetB0 wrapper
│   │   └── ood_gate.py        # Out-of-Distribution detection
│   ├── inference/
│   │   └── predict.py         # Full pipeline + threshold engine
│   └── explainability/
│       └── gradcam.py         # Grad-CAM heatmap generation
├── notebooks/
│   ├── 01_eda.ipynb           # Exploratory Data Analysis
│   ├── 02_training.ipynb      # Transfer learning training
│   ├── 03_threshold_tuning.ipynb
│   └── 04_evaluation.ipynb    # Full performance analysis
├── tests/
│   └── test_threshold_engine.py
└── docs/
    ├── report_progress.md     # Living project report
    └── model_limitations.md   # Known limitations + improvement ideas
```

## How the Confidence System Works

Every prediction is routed into one of three states:

| State | Condition | UI |
|---|---|---|
| Tumor Detected | P(tumor) ≥ 90% | Red card + Grad-CAM |
| No Tumor Detected | P(no tumor) ≥ 90% | Green card + Grad-CAM |
| Manual Review Required | Neither class ≥ 90% | Amber card, raw probabilities |

## Architecture

- **Base model:** EfficientNetB0 pretrained on ImageNet (5.3M parameters)
- **Training:** Two-phase transfer learning (10 + 5 epochs on Google Colab T4 GPU)
- **OOD gate:** MobileNetV2 binary classifier or statistical heuristic
- **Explainability:** Grad-CAM via `pytorch-grad-cam`
- **Dataset:** masoudnickparvar/brain-tumor-mri-dataset (7,023 images, 4 classes)

## Target Performance

| Metric | Target |
|---|---|
| Recall (Sensitivity) | ≥ 95% |
| F1-Score | ≥ 0.90 |
| Accuracy | ≥ 92% |
| AUC-ROC | ≥ 0.97 |
| Inference time (CPU) | < 3 seconds |

## Run Tests

```bash
python -m pytest tests/ -v
```

## Known Limitations

See [docs/model_limitations.md](docs/model_limitations.md) for a full list with explanations and improvement ideas.

## Medical Disclaimer

This tool is a research prototype for academic demonstration only. It has **not** been clinically validated and **must not** be used for actual patient diagnosis. Always consult a qualified radiologist.

## Dataset Attribution

- Primary: [masoudnickparvar/brain-tumor-mri-dataset](https://www.kaggle.com/datasets/masoudnickparvar/brain-tumor-mri-dataset) — CC BY 4.0
- External validation: [navoneel/brain-mri-images-for-brain-tumor-detection](https://www.kaggle.com/datasets/navoneel/brain-mri-images-for-brain-tumor-detection)
