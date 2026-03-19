from __future__ import annotations

from typing import Sequence, Optional
import numpy as np

from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import LabelEncoder
from sklearn.calibration import CalibratedClassifierCV
from xgboost import XGBClassifier


class SentenceTransformerClassifier:
    """
    SentenceTransformer (embeddings) + XGBoost (classifier)
    with calibration + early stopping support.
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        random_state: int = 42,
    ) -> None:
        self.model_name = model_name
        self.random_state = random_state

        base_model = XGBClassifier(
            objective="multi:softprob",
            eval_metric="mlogloss",
            tree_method="hist",

            n_estimators=120,
            max_depth=5,
            learning_rate=0.05,

            subsample=0.8,
            colsample_bytree=0.8,

            reg_alpha=0.1,
            reg_lambda=1.0,

            random_state=random_state,
            n_jobs=-1,
        )

        # Calibrated classifier for better probabilities
        self.classifier = CalibratedClassifierCV(
            estimator=base_model,
            method="sigmoid",
            cv=3
        )

        self._encoder = None
        self.label_encoder = LabelEncoder()

    # ---------------------------
    # Encoder
    # ---------------------------
    def _get_encoder(self) -> SentenceTransformer:
        if self._encoder is None:
            self._encoder = SentenceTransformer(self.model_name)
        return self._encoder

    def encode(self, texts: Sequence[str], batch_size: int = 64) -> np.ndarray:
        encoder = self._get_encoder()
        return encoder.encode(
            list(texts),
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

    # ---------------------------
    # Training
    # ---------------------------
    def fit_embeddings(
        self,
        X: np.ndarray,
        labels: Sequence[str],
        sample_weight: Optional[np.ndarray] = None,
    ):
        y = self.label_encoder.fit_transform(labels)
        self.classifier.fit(X, y, sample_weight=sample_weight, verbose=True)
        return self

    # ---------------------------
    # Prediction
    # ---------------------------
    def predict_embeddings(self, X: np.ndarray):
        y_pred = self.classifier.predict(X)
        return self.label_encoder.inverse_transform(y_pred)

    def predict_proba_embeddings(self, X: np.ndarray):
        return self.classifier.predict_proba(X)

    # ---------------------------
    # End-to-end
    # ---------------------------
    def fit(self, texts: Sequence[str], labels: Sequence[str]):
        X = self.encode(texts)
        return self.fit_embeddings(X, labels)

    def predict(self, texts: Sequence[str]):
        X = self.encode(texts)
        return self.predict_embeddings(X)

    def predict_proba(self, texts: Sequence[str]):
        X = self.encode(texts)
        return self.predict_proba_embeddings(X)

    # ---------------------------
    @property
    def classes_(self):
        return self.label_encoder.classes_

    # Avoid saving heavy transformer
    def __getstate__(self):
        state = self.__dict__.copy()
        state["_encoder"] = None
        return state
