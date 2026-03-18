from __future__ import annotations

from typing import Sequence
import numpy as np

from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression


class SentenceTransformerClassifier:
    """
    SentenceTransformer (for embeddings) + LogisticRegression classifier.
    Optimized for precomputed embeddings.
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        max_iter: int = 2000,
        random_state: int = 42,
    ) -> None:
        self.model_name = model_name
        self.max_iter = max_iter
        self.random_state = random_state

        self.classifier = LogisticRegression(
            max_iter=max_iter,
            random_state=random_state,
            n_jobs=-1
        )

        self._encoder = None

    # ---------------------------
    # Encoder
    # ---------------------------
    def _get_encoder(self) -> SentenceTransformer:
        if self._encoder is None:
            self._encoder = SentenceTransformer(self.model_name)
        return self._encoder

    def encode(self, texts: Sequence[str], batch_size: int = 64) -> np.ndarray:
        encoder = self._get_encoder()
        embeddings = encoder.encode(
            list(texts),
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,   # 👈 enable progress bar
        )
        return embeddings

    # ---------------------------
    # Training on embeddings
    # ---------------------------
    def fit_embeddings(self, X: np.ndarray, labels: Sequence[str]):
        self.classifier.fit(X, labels)
        return self

    # ---------------------------
    # Prediction on embeddings
    # ---------------------------
    def predict_embeddings(self, X: np.ndarray):
        return self.classifier.predict(X)

    def predict_proba_embeddings(self, X: np.ndarray):
        return self.classifier.predict_proba(X)

    # ---------------------------
    # End-to-end (optional use)
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
        return self.classifier.classes_

    # Avoid saving heavy transformer
    def __getstate__(self):
        state = self.__dict__.copy()
        state["_encoder"] = None
        return state
