"""Majority and TF-IDF + logistic regression baselines (hypothesis-only and document+hypothesis)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.pipeline import make_pipeline  # noqa: E402

from clauseshift.data import load  # noqa: E402
from clauseshift.predictions import save_predictions  # noqa: E402

train, dev, test = load("train"), load("dev"), load("test")


def fit_predict(name, text_fn, C_grid=(0.1, 1.0, 10.0)):
    best = None
    for C in C_grid:                                   # model selection on dev only
        clf = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True),
                            LogisticRegression(C=C, max_iter=2000))
        clf.fit([text_fn(i) for i in train], [i["label"] for i in train])
        dev_acc = clf.score([text_fn(i) for i in dev], [i["label"] for i in dev])
        if best is None or dev_acc > best[0]:
            best = (dev_acc, C, clf)
    dev_acc, C, clf = best
    for split, items in (("dev", dev), ("test", test)):
        probs = clf.predict_proba([text_fn(i) for i in items])
        save_predictions(name, split, items, [dict(zip(clf.classes_, p)) for p in probs],
                         meta={"C": C, "selected_on": "dev accuracy"})
    print(name, "C=", C, "dev acc", round(dev_acc, 3))


majority = max(set(i["label"] for i in train), key=[i["label"] for i in train].count)
for split, items in (("dev", dev), ("test", test)):
    save_predictions("majority", split, items, [{majority: 1.0}] * len(items), meta={"class": majority})
fit_predict("tfidf_lr_hypothesis_only", lambda i: i["hypothesis"])
fit_predict("tfidf_lr_document_hypothesis", lambda i: i["premise"] + " [SEP] " + i["hypothesis"])
