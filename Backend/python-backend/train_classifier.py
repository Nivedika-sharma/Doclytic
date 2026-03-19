import os
import time
import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from st_classifier import SentenceTransformerClassifier
from preprocessing import preprocess_for_model


TRAIN_CSV = "dataset_pipeline/output/train.csv"
VAL_CSV = "dataset_pipeline/output/val.csv"

MODEL_OUT = "models/doc_clf.joblib"

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

    clf = SentenceTransformerClassifier()

    # ---------------------------
    # Prepare inputs
    # ---------------------------
    train_texts = [preprocess_for_model(t) for t in train_df["text"]]
    val_texts = [preprocess_for_model(t) for t in val_df["text"]]

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
    sample_weight = None
    # Example placeholder:
    # sample_weight = np.ones(len(train_df))
    # sample_weight[hard_indices] = 2.0

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
    errors.to_csv("errors.csv", index=False)

    low_conf = val_df.copy()
    low_conf["pred"] = preds
    low_conf["confidence"] = confidences
    low_conf = low_conf[low_conf["confidence"] < 0.6]
    low_conf.to_csv("low_confidence.csv", index=False)

    print(f"Saved {len(errors)} misclassified samples")
    print(f"Saved {len(low_conf)} low-confidence samples")

    # ---------------------------
    # Save model
    # ---------------------------
    joblib.dump(clf, MODEL_OUT)
    print("\n[8] Model saved to:", MODEL_OUT)


if __name__ == "__main__":
    train()
