"""
Обгортка над моделлю класифікації тональності.

ЗАВДАННЯ ЛР1 (крок 3): реалізувати клас SentimentClassifier так, щоб:
  1. Модель завантажувалась ОДИН РАЗ — у методі load(), а не при кожному запиті.
  2. predict() повертав кортеж (label, score), де score — впевненість
     моделі у передбаченій мітці (не сирий тензор, а звичайний float).

Документація transformers.pipeline:
https://huggingface.co/docs/transformers/main_classes/pipelines
"""


from __future__ import annotations

from transformers import pipeline


class SentimentClassifier:
    """Класифікатор тональності тексту."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._pipeline = None

    def load(self) -> None:
        """Завантаження моделі один раз."""
        if self._pipeline is None:
            self._pipeline = pipeline(
                "sentiment-analysis",
                model=self.model_name
            )

    def predict(self, text: str) -> tuple[str, float]:
        """Класифікація одного тексту."""
        if self._pipeline is None:
            raise RuntimeError("Модель не завантажена")

        result = self._pipeline(text)[0]

        label = result["label"]
        score = float(result["score"])

        return label, score

    @property
    def is_ready(self) -> bool:
        return self._pipeline is not None

    def predict_batch(
        self, texts: list[str]
    ) -> list[tuple[str, float]]:
        """Класифікація списку текстів."""
        if self._pipeline is None:
            raise RuntimeError("Модель не завантажена")

        results = self._pipeline(texts)

        return [
            (item["label"], float(item["score"]))
            for item in results
        ]
