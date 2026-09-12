#train_classifier.py
# Train a DISTILBERT classifier on hand-labeled findings
# 4s modes:
# mode 2class  high (critical+major) vs low (minor)
# mode 3class  critical / major / minor
# mode 2class_filter  not_a_bug / low / high                
# mode 4class not_a_bug / minor / major / critical  

# Evaluated against two baselines on the SAME test set:
#  1. majority class
#  2. the LLM's own severity (findings.severity)

import argparse
import json
import os
import random
import re
import sqlite3
import torch
import matplotlib
import matplotlib.pyplot as plt

from collections import Counter
from sklearn.metrics import classification_report, accuracy_score, f1_score, confusion_matrix
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification


import numpy as np

MODEL_NAME = "distilbert-base-uncased"
MAX_SEQ_LENGTH = 128

# Only 'skip' is dropped 

EXCLUDED_LABELS = {"skip"}

NOT_A_BUG = "not_a_bug"

# The *_filter modes keep not_a_bug as a trainable class, so the classifier
# assigns severity AND reduces the Vision Agent's false positives
# (findings that report correct behaviour as a defect).

CLASSIFICATION_MODES = {
    "2class": {"label_column": "label12", "class_names": ["low", "high"],
                "keep_not_a_bug": False},
    "3class": {"label_column": "label13", "class_names": ["minor", "major", "critical"],
               "keep_not_a_bug": False},
    "2class_filter": {"label_column": "label12", "class_names": ["not_a_bug", "low", "high"],
                      "keep_not_a_bug": True},
    "4class": {"label_column": "label13", "class_names": ["not_a_bug", "minor", "major", "critical"],
                "keep_not_a_bug": True},
}

DEFAULT_SKIP_RUNS = [16]

HIGH_SEVERITY = {"critical", "major"}

def set_random_seed(seed_value):
    random.seed(seed_value)
    np.random.seed(seed_value)
    try:
        torch.manual_seed(seed_value)
    except ImportError:
        pass    

# DATA 

def tokenize_for_grouping(text):
    cleaned = re.sub(r"[^a-z\s]", " ", str(text).lower())
    stopwords = {"the", "a", "an", "is", "are", "to", "of", "for", "and", "or",
                 "in", "on", "with", "that", "which", "this", "it", "its", "be",
                 "as", "by", "not", "no", "has", "have", "could", "may", "might",
                 "should", "would", "can", "also", "some", "their"}
    return {w for w in cleaned.split() if w not in stopwords and len(w) > 2}


def assign_groups(data_points, similarity_threshold=0.3):
    # Group similar findings by Jaccard token similarity so the same defect,
    # even when worded differently across runs, stays on one side of the split.
    # A fixed fingerprint does not work here because the wording varies.
    token_sets = [tokenize_for_grouping(item["text"]) for item in data_points]
    parent = list(range(len(data_points)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(data_points)):
        for j in range(i + 1, len(data_points)):
            set_i, set_j = token_sets[i], token_sets[j]
            if not set_i or not set_j:
                continue
            jaccard = len(set_i & set_j) / len(set_i | set_j)
            if jaccard >= similarity_threshold:
                root_i, root_j = find(i), find(j)
                if root_i != root_j:
                    parent[max(root_i, root_j)] = min(root_i, root_j)

    for i, item in enumerate(data_points):
        item["group"] = f"g{find(i)}"
    return data_points

def fetch_training_data(db_path, skip_run_ids=None):
    # Join my_labels with findings

    skip_run_ids = skip_run_ids or set()
    connection = sqlite3.connect(db_path)
    records = connection.execute("""
        SELECT f.id, f.run_id, f.issue_type, f.description, f.severity AS ai_severity, m.severity AS label
        FROM my_labels m
        JOIN findings f ON f.id = m.finding_id
        """).fetchall()
    connection.close()

    data_points = []
    drop_counts = Counter()
    for finding_id, run_id, issue_type, description, ai_sev, label in records: 
        label = (label or "").strip().lower()
        if label in EXCLUDED_LABELS:
            drop_counts[label] += 1
            continue
        if run_id in skip_run_ids:
            drop_counts["excluded_run"] += 1
            continue
        if not description or not str(description).strip():
            drop_counts["no_description"] += 1
            continue
        if label not in {"critical", "major", "minor", NOT_A_BUG}:
            drop_counts["invalid_label"] += 1
            continue
        data_points.append({
            "id": finding_id,
            "run_id": run_id,
            "issue_type": issue_type,
            "text": str(description).strip(),
            "label13": label,
            "label12": (NOT_A_BUG if label == NOT_A_BUG else ("high" if label in HIGH_SEVERITY else "low")),
            "ai_severity": (ai_sev or "").strip().lower(),
            "group": None,
        })  
    return data_points, drop_counts

def split_by_group(data_points, label_column, test_fraction=0.2, random_seed=42):
    
    # Split by fingerprint group so the same defect stays on one side.

    # Groups are shuffled and assigned to the test set while keeping the label
    # distribution close to the overall distribution.
    ""
    rng = random.Random(random_seed)
    grouped_data = {}
    for item in data_points: 
        grouped_data.setdefault(item["group"], []).append(item)

    target_size = int(round(len(data_points) * test_fraction))
    overall_dist = Counter(item[label_column] for item in data_points)
    label_classes = sorted(overall_dist)
    target_proportions = {c: overall_dist[c] / len(data_points) for c in label_classes}

    group_keys = list(grouped_data)
    rng.shuffle(group_keys)

    test_keys = []
    test_size = 0
    test_label_counts = Counter()

    for key in group_keys:
        if test_size >= target_size:
            break
        group_items = grouped_data[key]
        if test_size + len(group_items) > target_size * 1.25 and test_size > target_size * 0.6:
            continue
        # prefer groups that pull the test set closer to the overall distribution

        candidate_counts = test_label_counts + Counter(item[label_column] for item in group_items)
        candidate_total = sum(candidate_counts.values())
        candidate_drift = sum(abs(candidate_counts[c] / candidate_total - target_proportions[c]) for c in label_classes)
        current_total = sum(test_label_counts.values())
        current_drift = sum(abs(test_label_counts[c] / current_total - target_proportions[c]) for c in label_classes) if current_total else 99

        if current_total == 0 or candidate_drift <= current_drift + 0.15:
            test_keys.append(key)
            test_label_counts = candidate_counts
            test_size += len(group_items)

    test_set = set(test_keys)

    # Guarantee every class is represented in test where the data allows it

    for cls in label_classes:
        needed = max(5, int(round(overall_dist[cls] * test_fraction)))
        while True:
            have = sum(1 for item in data_points
                       if item["group"] in test_set and item[label_column] == cls)
            if have >= needed:
                break
            candidates = [key for key in grouped_data if key not in test_set and any(item[label_column] == cls for item in grouped_data[key])]
            if len(candidates) < 2:
                continue
            candidates.sort(key=lambda key: len(grouped_data[key]))
            test_set.add(candidates[0])
            print(f" moved group {candidates[0][:40]} to test set to ensure class {cls} is represented")

    train_data = [item for item in data_points if item["group"] not in test_set]
    test_data = [item for item in data_points if item["group"] in test_set]
    return train_data, test_data

# METRICS

def compute_metrics(true_labels, predicted_labels, label_classes, heading):
    
    # Compute accuracy, precision, recall and F1
    
    accuracy = accuracy_score(true_labels, predicted_labels)
    macro_f1 = f1_score(true_labels, predicted_labels, average="macro", labels=label_classes, zero_division=0)
    print(f"\n{heading}  accuracy={accuracy:.3f}  macro-F1={macro_f1:.3f}")
    print(classification_report(true_labels, predicted_labels, labels=label_classes, zero_division=0, digits=3))
    confusion = confusion_matrix(true_labels, predicted_labels, labels=label_classes)
    return {
        "accuracy": round(float(accuracy), 4),
        "macro_f1": round(float(macro_f1), 4),
        "report": classification_report(true_labels, predicted_labels, labels=label_classes, zero_division=0, digits=3, output_dict=True),
        "confusion_matrix": confusion.tolist(),
        "classes": label_classes,
    }

def save_confusion_plot(confusion_matrix, label_classes, save_path, plot_title):
    try:
        matplotlib.use("Agg")
    except ImportError:
        print("matplotlib not available, skipping confusion matrix plot")
        return
    matrix = np.array(confusion_matrix)
    fig, axis = plt.subplots(figsize=(1.6 * len(label_classes) + 2.2,
                                      1.4 * len(label_classes) + 2.0))
    axis.imshow(matrix, cmap="Blues")
    axis.set_xticks(range(len(label_classes)), label_classes)
    axis.set_yticks(range(len(label_classes)), label_classes)
    axis.set_xlabel("Predicted")
    axis.set_ylabel("True (human label)")
    axis.set_title(plot_title)
    threshold = matrix.max() / 2 if matrix.max() else 0
    for i in range(len(label_classes)):
        for j in range(len(label_classes)):
            axis.text(j, i, str(matrix[i, j]), ha="center", va="center",
                      color="white" if matrix[i, j] > threshold else "black")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    print(f" confusion matrix plot saved to {save_path}")


def generate_llm_baseline_predictions(test_data, mode):

    # Use the LLM's own severity as a baseline classifier
    #In *_filter modes, the LLM cannot predict not_a_bug because it only outputs findings it considers real. 
    # Its recall for this class is therefore 0 by design. 
    # The filter classifier handles this by detecting and suppressing false positives.

    valid_severities = {"critical", "major", "minor"}
    label_col = CLASSIFICATION_MODES[mode]["label_column"]
    if label_col == "label12":
        return [("high" if item["ai_severity"] in HIGH_SEVERITY else "low") if item["ai_severity"] in valid_severities else "low" for item in test_data]
    return [item["ai_severity"] if item["ai_severity"] in valid_severities else "minor" for item in test_data]

# TRAINING
def train_distilbert(train_data, test_data, label_classes, label_column, num_epochs, learning_rate, batch_size, random_seed):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"ndevice: {device}")

    class_to_idx = {cls: i for i, cls in enumerate(label_classes)}
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    class CustomDataset(Dataset):
        def __init__(self, records):
            self.records = records
        def __len__(self):
            return len(self.records)
        def __getitem__(self, index):
            record = self.records[index]
            encoding = tokenizer(record["text"], truncation=True, max_length=MAX_SEQ_LENGTH,
                                 padding="max_length", return_tensors="pt")
            return {
                "input_ids": encoding["input_ids"][0],
                "attention_mask": encoding["attention_mask"][0],
                "labels": torch.tensor(class_to_idx[record[label_column]]),
            }

    generator = torch.Generator()
    generator.manual_seed(random_seed)
    train_loader = DataLoader(CustomDataset(train_data), batch_size=batch_size, shuffle=True, generator=generator)
    test_loader = DataLoader(CustomDataset(test_data), batch_size=batch_size)

    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=len(label_classes)).to(device)

    class_counts = Counter(record[label_column] for record in train_data)
    class_weights = torch.tensor([len(train_data) / (len(label_classes) * max(class_counts[cls], 1))
                                  for cls in label_classes], dtype=torch.float).to(device)
    print("class weights:", {cls: round(float(weight), 2) for cls, weight in zip(label_classes, class_weights)})

    loss_function = torch.nn.CrossEntropyLoss(weight=class_weights)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)

    for epoch in range(1, num_epochs + 1):
        model.train()
        total_loss = 0.0
        for batch in train_loader:
            optimizer.zero_grad()
            batch = {key: value.to(device) for key, value in batch.items()}
            outputs = model(input_ids=batch["input_ids"],
                            attention_mask=batch["attention_mask"])
            loss = loss_function(outputs.logits, batch["labels"])
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        print(f"epoch {epoch}/{num_epochs}  train loss {total_loss / len(train_loader):.4f}")

    model.eval()
    predictions = []
    with torch.no_grad():
        for batch in test_loader:
            batch = {key: value.to(device) for key, value in batch.items()}
            outputs = model(input_ids=batch["input_ids"],
                            attention_mask=batch["attention_mask"])
            predictions += outputs.logits.argmax(-1).cpu().tolist()

    return model, tokenizer, [label_classes[pred] for pred in predictions]

# Main

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=list(CLASSIFICATION_MODES), default="2class",
                        help="2class/3class = severity only; "
                             "2class_filter/4class also learn not_a_bug")
    parser.add_argument("--db", default=None, help="defaults to config.DB_PATH")
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--lr", type=float, default=3e-5)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--test-frac", type=float, default=0.2)
    parser.add_argument("--exclude-runs", default=",".join(map(str, DEFAULT_SKIP_RUNS)))
    parser.add_argument("--out", default="classifier_out")
    parser.add_argument("--no-train", action="store_true",
                        help="data + baselines only, skip fine-tuning")
    arguments = parser.parse_args()

    set_random_seed(arguments.seed)
    os.makedirs(arguments.out, exist_ok=True)

    db_path = arguments.db
    if db_path is None:
        from config import DB_PATH
        db_path = DB_PATH

    skip_runs = {int(x) for x in arguments.exclude_runs.split(",") if x.strip()}

    #  load 
    all_data, drop_counts = fetch_training_data(db_path, skip_runs)
    all_data = assign_groups(all_data)
    mode_config = CLASSIFICATION_MODES[arguments.mode]
    label_column, label_classes = mode_config["label_column"], mode_config["class_names"]

    not_a_bug_count = sum(1 for item in all_data if item["label13"] == NOT_A_BUG)
    if not mode_config["keep_not_a_bug"]:
        all_data = [item for item in all_data if item["label13"] != NOT_A_BUG]
        drop_counts[NOT_A_BUG] = not_a_bug_count

    print(f"db: {db_path}")
    print(f"mode: {arguments.mode}   classes: {label_classes}")
    print(f"trainable findings: {len(all_data)}")
    if mode_config["keep_not_a_bug"]:
        print(f"not_a_bug KEPT as a trainable class: {not_a_bug_count} examples "
              f"({100 * not_a_bug_count / max(len(all_data), 1):.1f}% of the set)")
    print("excluded:", dict(drop_counts))
    print("label distribution:", dict(Counter(item[label_column] for item in all_data)))
    print(f"unique fingerprint groups: {len({item['group'] for item in all_data})}")

    if len(all_data) < 40:
        raise SystemExit("Too little data — check my_labels is populated.")

    #  split 
    train_data, test_data = split_by_group(all_data, label_column, arguments.test_frac, arguments.seed)
    print(f"\ntrain {len(train_data)}   test {len(test_data)}")
    print("train dist:", dict(Counter(item[label_column] for item in train_data)))
    print("test  dist:", dict(Counter(item[label_column] for item in test_data)))
    assert not ({item["group"] for item in train_data} & {item["group"] for item in test_data}), \
        "group leakage between train and test"

    true_labels = [item[label_column] for item in test_data]
    missing_classes = [cls for cls in label_classes if cls not in set(true_labels)]
    if missing_classes:
        print(f"\n!! WARNING: no test examples for {missing_classes}. That class cannot "
              f"be evaluated — a direct consequence of its sparsity, and "
              f"itself a reportable finding.")
    results = {
        "mode": arguments.mode,
        "seed": arguments.seed,
        "n_total": len(all_data),
        "n_train": len(train_data),
        "n_test": len(test_data),
        "excluded": dict(drop_counts),
        "label_distribution": dict(Counter(item[label_column] for item in all_data)),
        "n_groups": len({item["group"] for item in all_data}),
    }

    #  baseline 1: majority class 
    majority_label = Counter(item[label_column] for item in train_data).most_common(1)[0][0]
    results["baseline_majority"] = compute_metrics(
        true_labels, [majority_label] * len(test_data), label_classes,
        f"BASELINE 1 — majority class ('{majority_label}')")

    #  baseline 2: the LLM's own severity 
    llm_predictions = generate_llm_baseline_predictions(test_data, arguments.mode)
    results["baseline_llm"] = compute_metrics(
        true_labels, llm_predictions, label_classes,
        "BASELINE 2 — LLM severity (same test set)")

    if arguments.no_train:
        output_path = os.path.join(arguments.out, f"metrics_{arguments.mode}.json")
        with open(output_path, "w") as file_handle:
            json.dump(results, file_handle, indent=2)
        print(f"\nsaved {output_path}  (baselines only)")
        return

    #  DistilBERT 
    model, tokenizer, predictions = train_distilbert(
        train_data, test_data, label_classes, label_column,
        arguments.epochs, arguments.lr, arguments.batch_size, arguments.seed)

    results["distilbert"] = compute_metrics(
        true_labels, predictions, label_classes, f"DistilBERT ({arguments.mode})")

    #  filter view: can it suppress false positives? 
    if mode_config["keep_not_a_bug"]:
        from sklearn.metrics import precision_score, recall_score, f1_score
        binary_true = [NOT_A_BUG if y == NOT_A_BUG else "real_bug" for y in true_labels]
        binary_pred = [NOT_A_BUG if p == NOT_A_BUG else "real_bug" for p in predictions]
        fp_rate_before = binary_true.count(NOT_A_BUG) / len(binary_true)
        kept_predictions = [(true, pred) for true, pred in zip(binary_true, binary_pred) if pred == "real_bug"]
        fp_rate_after = ([true for true, _ in kept_predictions].count(NOT_A_BUG) / len(kept_predictions)
                         if kept_predictions else 0.0)
        filter_results = {
            "not_a_bug_precision": round(float(precision_score(
                binary_true, binary_pred, pos_label=NOT_A_BUG, zero_division=0)), 4),
            "not_a_bug_recall": round(float(recall_score(
                binary_true, binary_pred, pos_label=NOT_A_BUG, zero_division=0)), 4),
            "not_a_bug_f1": round(float(f1_score(
                binary_true, binary_pred, pos_label=NOT_A_BUG, zero_division=0)), 4),
            "pipeline_fp_rate_before": round(fp_rate_before, 4),
            "pipeline_fp_rate_after": round(fp_rate_after, 4),
            "findings_suppressed": int(binary_pred.count(NOT_A_BUG)),
            "findings_kept": len(kept_predictions),
        }
        results["false_positive_filter"] = filter_results
        print("\n--- FALSE-POSITIVE FILTER (binary view) ---")
        print(f"not_a_bug   precision {filter_results['not_a_bug_precision']:.3f}   "
              f"recall {filter_results['not_a_bug_recall']:.3f}   "
              f"F1 {filter_results['not_a_bug_f1']:.3f}")
        print(f"pipeline false-positive rate: "
              f"{100 * fp_rate_before:.1f}% -> {100 * fp_rate_after:.1f}% "
              f"after filtering")
        print(f"{filter_results['findings_suppressed']} of {len(binary_pred)} test findings "
              f"suppressed, {filter_results['findings_kept']} passed through")
        print("(the LLM baseline cannot score here: it never emits not_a_bug)")

    save_confusion_plot(results["distilbert"]["confusion_matrix"], label_classes,
                        os.path.join(arguments.out, f"confusion_{arguments.mode}.png"),
                        f"DistilBERT — {arguments.mode}")

    model_dir = os.path.join(arguments.out, f"model_{arguments.mode}")
    model.save_pretrained(model_dir)
    tokenizer.save_pretrained(model_dir)
    with open(os.path.join(model_dir, "classes.json"), "w") as file_handle:
        json.dump(label_classes, file_handle)
    print(f"saved model to {model_dir}/")

    #  summary 
    print("\n SUMMARY")
    print(f"{'model':<22}{'acc':>8}{'macroF1':>10}")
    for key, name in [("baseline_majority", "majority class"),
                      ("baseline_llm", "LLM severity"),
                      ("distilbert", "DistilBERT")]:
        result = results[key]
        print(f"{name:<22}{result['accuracy']:>8.3f}{result['macro_f1']:>10.3f}")

    output_path = os.path.join(arguments.out, f"metrics_{arguments.mode}.json")
    with open(output_path, "w") as file_handle:
        json.dump(results, file_handle, indent=2)
    print(f"\nsaved {output_path}")


if __name__ == "__main__":
    main()