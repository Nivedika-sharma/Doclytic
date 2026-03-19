import json
import os
import time
import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from st_classifier import SentenceTransformerClassifier
from preprocessing import build_keyword_dict, preprocess_for_model


TRAIN_CSV = "dataset_pipeline/output/train.csv"
VAL_CSV = "dataset_pipeline/output/val.csv"

MODEL_OUT = "models/doc_clf.joblib"
KEYWORD_DICT_OUT = "models/keyword_dict.json"
ERRORS_CSV = "errors.csv"
LOW_CONF_CSV = "low_confidence.csv"

os.makedirs("models", exist_ok=True)


# ---------------------------
# Load dataset
# ---------------------------
def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    if "text" not in df.columns or "label" not in df.columns:
        raise ValueError("CSV must contain text and label columns")

    df["text"] = df["text"].fillna("").astype(str)
    df["label"] = df["label"].fillna("").astype(str).str.strip().str.lower()

    df = df[(df["text"].str.len() > 0) & (df["label"].str.len() > 0)]

    return df


def analyze_errors(path: str, top_k: int = 10):
    if not os.path.exists(path):
        print("\n[analysis] errors.csv not found, skipping.")
        return
    df = pd.read_csv(path)
    if not {"label", "pred", "text"}.issubset(df.columns):
        print("\n[analysis] errors.csv missing required columns, skipping.")
        return

    df["label"] = df["label"].astype(str).str.strip().str.lower()
    df["pred"] = df["pred"].astype(str).str.strip().str.lower()
    conf = df.groupby(["label", "pred"]).size().reset_index(name="count")
    conf = conf.sort_values("count", ascending=False)
    top_pairs = conf.head(top_k)

    print("\n[analysis] Top confusion pairs:")
    print(top_pairs.to_string(index=False))

    print("\n[analysis] Examples per pair:")
    for _, row in top_pairs.iterrows():
        pair = df[(df["label"] == row["label"]) & (
            df["pred"] == row["pred"])].head(2)
        examples = [str(t)[:140].replace("\n", " ")
                    for t in pair["text"].tolist()]
        print(f"- {row['label']} -> {row['pred']} ({row['count']}):")
        for ex in examples:
            print(f"  {ex}")


def build_sample_weights(train_df: pd.DataFrame, errors_path: str) -> np.ndarray:
    weights = np.ones(len(train_df), dtype=float)
    if not os.path.exists(errors_path):
        return weights

    errors = pd.read_csv(errors_path)
    if "label" not in errors.columns:
        return weights
    errors["label"] = errors["label"].astype(str).str.strip().str.lower()
    top_labels = (
        errors["label"].value_counts().head(5).index.tolist()
    )
    if not top_labels:
        return weights

    label_series = train_df["label"].astype(str).str.strip().str.lower()
    for idx, label in enumerate(label_series):
        if label in top_labels:
            weights[idx] = 2.0
    return weights


def print_confidence_histogram(confidences: np.ndarray):
    bins = np.linspace(0, 1.0, 11)
    hist, edges = np.histogram(confidences, bins=bins)
    print("\nConfidence Histogram:")
    for i in range(len(hist)):
        print(f"{edges[i]:.1f}-{edges[i+1]:.1f}: {hist[i]}")


def print_accuracy_per_class(labels, preds):
    df = pd.DataFrame({"label": labels, "pred": preds})
    per_class = (df["label"] == df["pred"]).groupby(
        df["label"]).mean().sort_values(ascending=False)
    print("\nAccuracy per class:")
    for label, acc in per_class.items():
        print(f"{label}: {acc:.3f}")


# ---------------------------
# Training
# ---------------------------
def train():
    print("\n[1] Loading data...")
    train_df = load_csv(TRAIN_CSV)
    val_df = load_csv(VAL_CSV)

    print(f"Train size: {len(train_df)}")
    print(f"Val size: {len(val_df)}")

    print("\n[2] Label distribution:")
    print(train_df["label"].value_counts())

    analyze_errors(ERRORS_CSV)

    print("\n[2.1] Building keyword dictionary...")
    keyword_dict = build_keyword_dict(
        train_df["text"].tolist(), train_df["label"].tolist())
    os.makedirs("models", exist_ok=True)
    with open(KEYWORD_DICT_OUT, "w", encoding="utf-8") as f:
        json.dump(keyword_dict, f, indent=2)
    print(f"Saved keyword dict to {KEYWORD_DICT_OUT}")

    clf = SentenceTransformerClassifier()

    # ---------------------------
    # Prepare inputs
    # ---------------------------
    train_texts = [preprocess_for_model(
        t, keyword_dict=keyword_dict) for t in train_df["text"]]
    val_texts = [preprocess_for_model(
        t, keyword_dict=keyword_dict) for t in val_df["text"]]

    # ---------------------------
    # Encode
    # ---------------------------
    print("\n[3] Encoding train data...")
    start = time.time()
    X_train = clf.encode(train_texts)
    print(f"Done in {round(time.time() - start, 2)} sec")

    print("\n[4] Encoding val data...")
    start = time.time()
    X_val = clf.encode(val_texts)
    print(f"Done in {round(time.time() - start, 2)} sec")

    # Save embeddings (optional reuse)
    np.save("X_train.npy", X_train)
    np.save("X_val.npy", X_val)

    # ---------------------------
    # Optional: Hard sample weighting (future use)
    # ---------------------------
    sample_weight = build_sample_weights(train_df, ERRORS_CSV)

    # ---------------------------
    # Train
    # ---------------------------
    print("\n[5] Training...")
    clf.fit_embeddings(
        X_train,
        train_df["label"].tolist(),
        sample_weight=sample_weight
    )

    # ---------------------------
    # Predict
    # ---------------------------
    print("\n[6] Predicting...")
    preds = clf.predict_embeddings(X_val)
    probs = clf.predict_proba_embeddings(X_val)

    confidences = np.max(probs, axis=1)

    # ---------------------------
    # Evaluate
    # ---------------------------
    acc = accuracy_score(val_df["label"], preds)

    print("\nValidation Accuracy:", f"{acc:.4f}")
    print("\nClassification Report:\n")
    print(classification_report(val_df["label"], preds, digits=4))

    print("\nConfidence Stats:")
    print("Avg confidence:", round(confidences.mean(), 4))
    print("Low confidence (<0.6):", int((confidences < 0.6).sum()))
    print_confidence_histogram(confidences)
    print_accuracy_per_class(val_df["label"], preds)

    # ---------------------------
    # Confusion Matrix
    # ---------------------------
    print("\nConfusion Matrix:")
    cm = confusion_matrix(val_df["label"], preds, labels=clf.classes_)
    print(cm)

    # ---------------------------
    # Save error analysis
    # ---------------------------
    print("\n[7] Saving error analysis...")

    errors = val_df.copy()
    errors["pred"] = preds
    errors["confidence"] = confidences
    errors = errors[errors["label"] != errors["pred"]]
    errors.to_csv(ERRORS_CSV, index=False)

    low_conf = val_df.copy()
    low_conf["pred"] = preds
    low_conf["confidence"] = confidences
    low_conf = low_conf[low_conf["confidence"] < 0.6]
    low_conf.to_csv(LOW_CONF_CSV, index=False)

    print(f"Saved {len(errors)} misclassified samples")
    print(f"Saved {len(low_conf)} low-confidence samples")

    # ---------------------------
    # Save model
    # ---------------------------
    joblib.dump(clf, MODEL_OUT)
    print("\n[8] Model saved to:", MODEL_OUT)


if __name__ == "__main__":
    train()
