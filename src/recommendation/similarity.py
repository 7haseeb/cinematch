"""Similarity scoring utilities."""

from __future__ import annotations

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def build_vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(
        max_features=14000,
        stop_words="english",
        ngram_range=(1, 2),
        min_df=1,
        sublinear_tf=True,
    )


def build_similarity(tags: list[str] | np.ndarray) -> tuple[TfidfVectorizer, np.ndarray]:
    vectorizer = build_vectorizer()
    vectors = vectorizer.fit_transform(tags)
    similarity = cosine_similarity(vectors).astype("float32")
    return vectorizer, similarity
