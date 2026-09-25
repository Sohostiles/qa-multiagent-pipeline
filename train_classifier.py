# train_classifier.py
# Train DistilBERT using the findings I labelled
#
# Modes:
# 2class: low / high
# 3class: minor / major / critical
# 2class_filter: not_a_bug / low / high
# 4class: not_a_bug / minor / major / critical
#
# Compare against the majority class and saved AI severity
# All three models use the same test set within each run

# Imports
import argparse
import json
import os
import random
import re
import sqlite3
from collections import Counter

import matplotlib

# Save plots without opening a window
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)


# Model settings
MODEL_NAME = "distilbert-base-uncased"
MAX_SEQ_LENGTH = 128

EXCLUDED_LABELS = {"skip"}
NOT_A_BUG = "not_a_bug"
HIGH_SEVERITY = {"critical", "major"}
DEFAULT_SKIP_RUNS = [16]

CLASSIFICATION_MODES = {
    "2class": {
        "label_column": "label12",
        "class_names": ["low", "high"],
        "keep_not_a_bug": False,
    },
    "3class": {
        "label_column": "label13",
        "class_names": ["minor", "major", "critical"],
        "keep_not_a_bug": False,
    },
    "2class_filter": {
        "label_column": "label12",
        "class_names": ["not_a_bug", "low", "high"],
        "keep_not_a_bug": True,
    },
    "4class": {
        "label_column": "label13",
        "class_names": ["not_a_bug", "minor", "major", "critical"],
        "keep_not_a_bug": True,
    },
}


# Set the seeds used for splitting and training
def set_random_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


# Remove common words before comparing descriptions
def tokenize_for_grouping(text):
    cleaned = re.sub(r"[^a-z\s]", " ", str(text).lower())

    stopwords = {
        "the", "a", "an", "is", "are", "to", "of", "for", "and",
        "or", "in", "on", "with", "that", "which", "this", "it",
        "its", "be", "as", "by", "not", "no", "has", "have",
        "could", "may", "might", "should", "would", "can",
        "also", "some", "their",
    }

    return {
        word for word in cleaned.split()
        if word not in stopwords and len(word) > 2
    }


# Keep similar descriptions in the same train/test group
def assign_groups(data, similarity_threshold=0.3):
    token_sets = [
        tokenize_for_grouping(item["text"])
        for item in data
    ]
    parents = list(range(len(data)))

    # Find the group a finding belongs to
    def find_group(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]

        return index

    for first in range(len(data)):
        for second in range(first + 1, len(data)):
            first_words = token_sets[first]
            second_words = token_sets[second]

            if not first_words or not second_words:
                continue

            shared_words = len(first_words & second_words)
            total_words = len(first_words | second_words)
            similarity = shared_words / total_words

            if similarity >= similarity_threshold:
                first_group = find_group(first)
                second_group = find_group(second)

                if first_group != second_group:
                    parents[max(first_group, second_group)] = min(
                        first_group, second_group
                    )

    for index, item in enumerate(data):
        item["group"] = f"g{find_group(index)}"

    return data


# Load findings together with my labels
def fetch_training_data(db_path, skip_run_ids=None):
    skip_run_ids = skip_run_ids or set()
    conn = sqlite3.connect(db_path)

    try:
        rows = conn.execute("""
            SELECT
                f.id,
                f.run_id,
                f.issue_type,
                f.description,
                f.severity AS ai_severity,
                m.severity AS label
            FROM my_labels m
            JOIN findings f ON f.id = m.finding_id
        """).fetchall()
    finally:
        conn.close()

    data = []
    dropped = Counter()

    for finding_id, run_id, issue_type, description, ai_severity, label in rows:
        label = (label or "").strip().lower()

        if label in EXCLUDED_LABELS:
            dropped[label] += 1
            continue

        if run_id in skip_run_ids:
            dropped["excluded_run"] += 1
            continue

        if not description or not str(description).strip():
            dropped["no_description"] += 1
            continue

        if label not in {"critical", "major", "minor", NOT_A_BUG}:
            dropped["invalid_label"] += 1
            continue

        # Merge major and critical for the low/high modes
        if label == NOT_A_BUG:
            binary_label = NOT_A_BUG
        elif label in HIGH_SEVERITY:
            binary_label = "high"
        else:
            binary_label = "low"

        data.append({
            "id": finding_id,
            "run_id": run_id,
            "issue_type": issue_type,
            "text": str(description).strip(),
            "label13": label,
            "label12": binary_label,
            "ai_severity": (ai_severity or "").strip().lower(),
            "group": None,
        })

    return data, dropped


# Split whole groups rather than individual findings
def split_by_group(data, label_column, test_fraction=0.2, random_seed=42):
    rng = random.Random(random_seed)
    groups = {}

    for item in data:
        groups.setdefault(item["group"], []).append(item)

    target_size = int(round(len(data) * test_fraction))
    label_counts = Counter(item[label_column] for item in data)
    labels = sorted(label_counts)

    target_proportions = {
        label: label_counts[label] / len(data)
        for label in labels
    }

    group_ids = list(groups)
    rng.shuffle(group_ids)

    test_groups = set()
    test_size = 0
    test_counts = Counter()

    for group_id in group_ids:
        if test_size >= target_size:
            break

        group_items = groups[group_id]

        # Avoid adding a very large group when test is nearly full
        if (
            test_size + len(group_items) > target_size * 1.25
            and test_size > target_size * 0.6
        ):
            continue

        new_counts = test_counts + Counter(
            item[label_column] for item in group_items
        )
        new_total = sum(new_counts.values())

        new_difference = sum(
            abs(new_counts[label] / new_total - target_proportions[label])
            for label in labels
        )

        current_total = sum(test_counts.values())
        current_difference = 99

        if current_total:
            current_difference = sum(
                abs(
                    test_counts[label] / current_total
                    - target_proportions[label]
                )
                for label in labels
            )

        # Try to keep the class proportions reasonably close
        if current_total == 0 or new_difference <= current_difference + 0.15:
            test_groups.add(group_id)
            test_counts = new_counts
            test_size += len(group_items)

    # Add examples of underrepresented classes where possible
    for label in labels:
        needed = max(5, int(round(label_counts[label] * test_fraction)))

        while True:
            available = sum(
                1 for item in data
                if item["group"] in test_groups
                and item[label_column] == label
            )

            if available >= needed:
                break

            candidates = [
                group_id for group_id, items in groups.items()
                if group_id not in test_groups
                and any(item[label_column] == label for item in items)
            ]

            # Leave at least one remaining group containing this class
            if len(candidates) < 2:
                break

            candidates.sort(key=lambda group_id: len(groups[group_id]))
            chosen_group = candidates[0]
            test_groups.add(chosen_group)

            print(
                f"Moved group {chosen_group} to test "
                f"to add examples of {label}"
            )

    train_data = [
        item for item in data
        if item["group"] not in test_groups
    ]
    test_data = [
        item for item in data
        if item["group"] in test_groups
    ]

    return train_data, test_data


# Calculate and print the classification results
def compute_metrics(true_labels, predictions, classes, heading):
    accuracy = accuracy_score(true_labels, predictions)

    macro_f1 = f1_score(
        true_labels,
        predictions,
        average="macro",
        labels=classes,
        zero_division=0,
    )

    print(f"\n{heading}")
    print(f"Accuracy: {accuracy:.3f} | Macro-F1: {macro_f1:.3f}")

    print(classification_report(
        true_labels,
        predictions,
        labels=classes,
        zero_division=0,
        digits=3,
    ))

    report = classification_report(
        true_labels,
        predictions,
        labels=classes,
        zero_division=0,
        output_dict=True,
    )

    matrix = confusion_matrix(
        true_labels,
        predictions,
        labels=classes,
    )

    return {
        "accuracy": round(float(accuracy), 4),
        "macro_f1": round(float(macro_f1), 4),
        "report": report,
        "confusion_matrix": matrix.tolist(),
        "classes": classes,
    }


# Save a confusion matrix for the report
def save_confusion_plot(matrix, classes, save_path, title):
    matrix = np.array(matrix)
    class_count = len(classes)

    fig, axis = plt.subplots(
        figsize=(1.6 * class_count + 2.2, 1.4 * class_count + 2.0)
    )

    axis.imshow(matrix, cmap="Blues")
    axis.set_xticks(range(class_count), classes)
    axis.set_yticks(range(class_count), classes)
    axis.set_xlabel("Predicted")
    axis.set_ylabel("True (human label)")
    axis.set_title(title)

    threshold = matrix.max() / 2 if matrix.max() else 0

    for row in range(class_count):
        for column in range(class_count):
            text_colour = (
                "white" if matrix[row, column] > threshold else "black"
            )

            axis.text(
                column,
                row,
                str(matrix[row, column]),
                ha="center",
                va="center",
                color=text_colour,
            )

    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)

    print(f"Confusion matrix saved to {save_path}")


# Use the saved AI severity as the second baseline
def generate_llm_baseline_predictions(test_data, mode):
    valid_severities = {"critical", "major", "minor"}
    label_column = CLASSIFICATION_MODES[mode]["label_column"]
    predictions = []

    # This baseline mapping does not predict not_a_bug
    for item in test_data:
        severity = item["ai_severity"]

        if label_column == "label12":
            prediction = "high" if severity in HIGH_SEVERITY else "low"
        else:
            prediction = severity if severity in valid_severities else "minor"

        predictions.append(prediction)

    return predictions


# Fine-tune DistilBERT and predict the test labels
def train_distilbert(
    train_data,
    test_data,
    classes,
    label_column,
    epochs,
    learning_rate,
    batch_size,
    random_seed,
):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\nDevice: {device}")

    class_ids = {
        label: index for index, label in enumerate(classes)
    }

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    # Convert each description into model inputs
    class FindingsDataset(Dataset):
        def __init__(self, records):
            self.records = records

        def __len__(self):
            return len(self.records)

        def __getitem__(self, index):
            record = self.records[index]

            tokens = tokenizer(
                record["text"],
                truncation=True,
                max_length=MAX_SEQ_LENGTH,
                padding="max_length",
                return_tensors="pt",
            )

            return {
                "input_ids": tokens["input_ids"][0],
                "attention_mask": tokens["attention_mask"][0],
                "labels": torch.tensor(class_ids[record[label_column]]),
            }

    generator = torch.Generator()
    generator.manual_seed(random_seed)

    train_loader = DataLoader(
        FindingsDataset(train_data),
        batch_size=batch_size,
        shuffle=True,
        generator=generator,
    )

    test_loader = DataLoader(
        FindingsDataset(test_data),
        batch_size=batch_size,
    )

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=len(classes),
    ).to(device)

    # Give less common classes more weight during training
    class_counts = Counter(
        item[label_column] for item in train_data
    )

    class_weights = torch.tensor(
        [
            len(train_data) / (len(classes) * max(class_counts[label], 1))
            for label in classes
        ],
        dtype=torch.float,
    ).to(device)

    print("Class weights:", {
        label: round(weight.item(), 2)
        for label, weight in zip(classes, class_weights)
    })

    loss_function = torch.nn.CrossEntropyLoss(weight=class_weights)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=learning_rate,
    )

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0

        for batch in train_loader:
            optimizer.zero_grad()

            batch = {
                key: value.to(device)
                for key, value in batch.items()
            }

            outputs = model(
                input_ids=batch["input_ids"],
                attention_mask=batch["attention_mask"],
            )

            loss = loss_function(outputs.logits, batch["labels"])
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        average_loss = total_loss / len(train_loader)
        print(f"Epoch {epoch}/{epochs} | Train loss: {average_loss:.4f}")

    # Evaluate after training is finished
    model.eval()
    predictions = []

    with torch.no_grad():
        for batch in test_loader:
            batch = {
                key: value.to(device)
                for key, value in batch.items()
            }

            outputs = model(
                input_ids=batch["input_ids"],
                attention_mask=batch["attention_mask"],
            )

            predicted_ids = outputs.logits.argmax(-1).cpu().tolist()
            predictions.extend(classes[index] for index in predicted_ids)

    return model, tokenizer, predictions


# Check how well the model filters out findings labelled not_a_bug
def evaluate_filter(true_labels, predictions):
    binary_true = [
        NOT_A_BUG if label == NOT_A_BUG else "real_bug"
        for label in true_labels
    ]
    binary_predictions = [
        NOT_A_BUG if label == NOT_A_BUG else "real_bug"
        for label in predictions
    ]

    kept_labels = [
        true for true, predicted in zip(binary_true, binary_predictions)
        if predicted == "real_bug"
    ]

    # Proportion of findings that are false positives
    false_share_before = binary_true.count(NOT_A_BUG) / len(binary_true)
    false_share_after = (
        kept_labels.count(NOT_A_BUG) / len(kept_labels)
        if kept_labels else 0.0
    )

    results = {
        "not_a_bug_precision": round(float(precision_score(
            binary_true,
            binary_predictions,
            pos_label=NOT_A_BUG,
            zero_division=0,
        )), 4),
        "not_a_bug_recall": round(float(recall_score(
            binary_true,
            binary_predictions,
            pos_label=NOT_A_BUG,
            zero_division=0,
        )), 4),
        "not_a_bug_f1": round(float(f1_score(
            binary_true,
            binary_predictions,
            pos_label=NOT_A_BUG,
            zero_division=0,
        )), 4),

        # Keep the existing JSON keys for earlier results
        "pipeline_fp_rate_before": round(false_share_before, 4),
        "pipeline_fp_rate_after": round(false_share_after, 4),
        "findings_suppressed": binary_predictions.count(NOT_A_BUG),
        "findings_kept": len(kept_labels),
    }

    print("\nFalse-positive filtering")
    print(
        f"not_a_bug | Precision: {results['not_a_bug_precision']:.3f}"
        f" | Recall: {results['not_a_bug_recall']:.3f}"
        f" | F1: {results['not_a_bug_f1']:.3f}"
    )

    if kept_labels:
        print(
            f"False-positive share: {100 * false_share_before:.1f}%"
            f" -> {100 * false_share_after:.1f}%"
        )
    else:
        print(
            "No findings were kept. The after-filter share is undefined; "
            "the saved value is 0.0 for compatibility."
        )

    print(
        f"{results['findings_suppressed']} of {len(binary_predictions)} "
        f"findings suppressed, {results['findings_kept']} kept"
    )
    print("The saved-severity baseline does not predict not_a_bug.")

    return results


# Main
def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode",
        choices=list(CLASSIFICATION_MODES),
        default="2class",
        help="2class/3class score severity; 2class_filter/4class keep not_a_bug",
    )
    parser.add_argument("--db", default=None, help="Uses config.DB_PATH by default")
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--lr", type=float, default=3e-5)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--test-frac", type=float, default=0.2)
    parser.add_argument(
        "--exclude-runs",
        default=",".join(map(str, DEFAULT_SKIP_RUNS)),
    )
    parser.add_argument("--out", default="classifier_out")
    parser.add_argument(
        "--no-train",
        action="store_true",
        help="Run the baselines without training DistilBERT",
    )

    args = parser.parse_args()

    if not 0 < args.test_frac < 1:
        parser.error("--test-frac must be between 0 and 1")

    if args.epochs < 1 or args.batch_size < 1 or args.lr <= 0:
        parser.error("Epochs, batch size and learning rate must be positive")

    set_random_seed(args.seed)
    os.makedirs(args.out, exist_ok=True)

    db_path = args.db

    if db_path is None:
        from config import DB_PATH
        db_path = DB_PATH

    skip_runs = {
        int(value) for value in args.exclude_runs.split(",")
        if value.strip()
    }

    # Load and group before applying the selected mode
    data, dropped = fetch_training_data(db_path, skip_runs)
    data = assign_groups(data)

    mode = CLASSIFICATION_MODES[args.mode]
    label_column = mode["label_column"]
    classes = mode["class_names"]

    not_a_bug_count = sum(
        1 for item in data if item["label13"] == NOT_A_BUG
    )

    if not mode["keep_not_a_bug"]:
        data = [
            item for item in data
            if item["label13"] != NOT_A_BUG
        ]
        dropped[NOT_A_BUG] = not_a_bug_count

    label_distribution = Counter(
        item[label_column] for item in data
    )
    group_count = len({item["group"] for item in data})

    print(f"Database: {db_path}")
    print(f"Mode: {args.mode} | Classes: {classes}")
    print(f"Trainable findings: {len(data)}")

    if mode["keep_not_a_bug"]:
        proportion = 100 * not_a_bug_count / max(len(data), 1)
        print(
            f"Keeping {not_a_bug_count} not_a_bug examples "
            f"({proportion:.1f}% of the data)"
        )

    print("Excluded:", dict(dropped))
    print("Label distribution:", dict(label_distribution))
    print(f"Similarity groups: {group_count}")

    if len(data) < 40:
        raise SystemExit("Too little data. Check that my_labels is populated.")

    # Split the data without separating members of the same group
    train_data, test_data = split_by_group(
        data,
        label_column,
        args.test_frac,
        args.seed,
    )

    if not train_data or not test_data:
        raise SystemExit(
            "The split produced an empty train or test set. "
            "Check the group sizes and test fraction."
        )

    print(f"\nTrain: {len(train_data)} | Test: {len(test_data)}")
    print("Train labels:", dict(Counter(
        item[label_column] for item in train_data
    )))
    print("Test labels:", dict(Counter(
        item[label_column] for item in test_data
    )))

    train_groups = {item["group"] for item in train_data}
    test_groups = {item["group"] for item in test_data}

    assert not train_groups & test_groups, "Groups overlap between train and test"

    true_labels = [item[label_column] for item in test_data]
    missing_classes = [
        label for label in classes
        if label not in set(true_labels)
    ]

    if missing_classes:
        print(
            f"\nNo test examples for {missing_classes}. "
            "Performance on these classes cannot be assessed from this split."
        )

    results = {
        "mode": args.mode,
        "seed": args.seed,
        "n_total": len(data),
        "n_train": len(train_data),
        "n_test": len(test_data),
        "excluded": dict(dropped),
        "label_distribution": dict(label_distribution),
        "n_groups": group_count,
    }

    # Baseline 1: always predict the most common training label
    majority_label = Counter(
        item[label_column] for item in train_data
    ).most_common(1)[0][0]

    results["baseline_majority"] = compute_metrics(
        true_labels,
        [majority_label] * len(test_data),
        classes,
        f"Baseline 1: majority class ({majority_label})",
    )

    # Baseline 2: use the severity already saved in findings
    llm_predictions = generate_llm_baseline_predictions(test_data, args.mode)

    results["baseline_llm"] = compute_metrics(
        true_labels,
        llm_predictions,
        classes,
        "Baseline 2: saved LLM severity",
    )

    output_path = os.path.join(args.out, f"metrics_{args.mode}.json")

    if args.no_train:
        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(results, file, indent=2)

        print(f"\nSaved {output_path} (baselines only)")
        return

    # Train and evaluate DistilBERT
    model, tokenizer, predictions = train_distilbert(
        train_data,
        test_data,
        classes,
        label_column,
        args.epochs,
        args.lr,
        args.batch_size,
        args.seed,
    )

    results["distilbert"] = compute_metrics(
        true_labels,
        predictions,
        classes,
        f"DistilBERT ({args.mode})",
    )

    if mode["keep_not_a_bug"]:
        results["false_positive_filter"] = evaluate_filter(
            true_labels,
            predictions,
        )

    save_confusion_plot(
        results["distilbert"]["confusion_matrix"],
        classes,
        os.path.join(args.out, f"confusion_{args.mode}.png"),
        f"DistilBERT: {args.mode}",
    )

    # Save the trained model, tokenizer and class order
    model_dir = os.path.join(args.out, f"model_{args.mode}")
    model.save_pretrained(model_dir)
    tokenizer.save_pretrained(model_dir)

    with open(
        os.path.join(model_dir, "classes.json"),
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(classes, file)

    print(f"Saved model to {model_dir}/")

    print("\nSummary")
    print(f"{'Model':<22}{'Accuracy':>10}{'Macro-F1':>10}")

    for key, name in [
        ("baseline_majority", "Majority class"),
        ("baseline_llm", "LLM severity"),
        ("distilbert", "DistilBERT"),
    ]:
        result = results[key]
        print(
            f"{name:<22}"
            f"{result['accuracy']:>10.3f}"
            f"{result['macro_f1']:>10.3f}"
        )

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(results, file, indent=2)

    print(f"\nSaved {output_path}")


if __name__ == "__main__":
    main()