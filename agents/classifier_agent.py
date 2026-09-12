# Classifier Agent
# This agent is responsible for classifying the findings.

# A fine-tuned DistilBERT classifier was also tested for this role but was not
# used due to its performance results (see train_classifier.py and the Evaluation chapter).
# The final implementation therefore uses an LLM-based classifier.
# The modular design also allows the classifier to be replaced without changing the analysis agents.

import json
from config import MODEL, chat_with_retry

VALID_SEVERITIES = {"critical", "major", "minor"}
# The same rubric was used when hand-labelling the traininng data
RUBRIC = """critical: BOTH conditions must hold.
  (a) something is demonstrably broken: a control produced no change when
      activated, a link leads to a 404, input landed in the wrong field, or
      displayed data is impossible or corrupt; AND
  (b) it obstructs buying: adding to cart, the cart contents, checkout, or
      completing the order.
  A broken control elsewhere on the page is major, not critical.
major: the application works but something is wrong or a user is obstructed.
  Includes broken controls outside the purchase flow, wrong or duplicated
  images, content that does not match its product, controls with no accessible
  name, and form inputs with no label.
minor: presentational only. Layout, spacing, alignment, truncation, contrast,
  alt-text wording, redundant ARIA, missing aria-expanded on a working control,
  tabindex and focus-order concerns."""

SYSTEM = f"""You are a QA lead assigning severity to automated test findings.

Apply this rubric exactly:
{RUBRIC}

Decision rules, applied in order:
1. If the finding says an interaction had no effect, or reports a 404, corrupt
   data, or input placed in the wrong field, it is critical.
2. Otherwise, accessibility findings are NEVER critical. An accessibility
   finding is major only if a user of assistive technology cannot identify or
   operate a control at all: a button or link with no accessible name, or a form
   input with no label. Every other accessibility finding is minor, including
   imperfect alt text, redundant alt text, missing aria-expanded, and tabindex
   or focus-order concerns.
3. Otherwise, findings about appearance alone are minor.
4. Reserve critical for rule 1. It should be rare.
5. Critical requires BOTH a demonstrable break AND obstruction of the purchase
   flow. A menu that will not open, a miscounting badge, or a missing error
   message is broken but does not stop a purchase: those are major.

You are given a numbered list of findings. Respond ONLY with JSON:
{{"severities": [{{"i": <index>, "severity": "critical|major|minor"}}, ...]}}

Every index in the input must appear exactly once. Do not invent indices, do not
rewrite the findings, and do not add commentary."""

def _batch(items, size):
    for i in range(0, len(items), size):
        yield i, items[i:i + size]


def _classify_batch(offset, batch):
    listing = "\n".join(
        f"{offset + i}: [{finding.get('issue_type', '?')}] "
        f"{finding.get('description', '')}"
        for i, finding in enumerate(batch)
    )

    response = chat_with_retry(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM},
            {
                "role": "user",
                "content": f"Assign severity:\n\n{listing}"
            }
        ],
        temperature=0,
        max_tokens=1500,
    )

    raw = response.choices[0].message.content.strip()

    # Remove markdown formatting if the model returned JSON in a code block
    if raw.startswith("```"):
        raw = raw.split("```")[1]

        if raw.startswith("json"):
            raw = raw[4:]

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        print("  Could not parse classifier response, keeping original severities")
        return {}

    assigned = {}

    for item in result.get("severities", []):
        try:
            index = int(item["i"])
        except (KeyError, TypeError, ValueError):
            continue

        severity = str(item.get("severity", "")).strip().lower()

        if severity in VALID_SEVERITIES:
            assigned[index] = severity

    return assigned


# Run all findings through the classifier and update their severity.
# The original severity is also saved so it can be compared later.
def classify(findings, batch_size=25):
    if not findings:
        return findings

    print(f"Classifier Agent assigning severity to {len(findings)} findings...")

    assigned = {}

    for offset, batch in _batch(findings, batch_size):
        result = _classify_batch(offset, batch)
        assigned.update(result)

    changed = 0

    for i, finding in enumerate(findings):
        original = finding.get("severity", "")
        finding["severity_initial"] = original

        new_severity = assigned.get(i)

        if new_severity:
            finding["severity"] = new_severity

            if new_severity != original:
                changed += 1

    missing = len(findings) - len(assigned)

    print(
        f"  Assigned {len(assigned)}/{len(findings)} "
        f"({changed} changed from the original value)"
    )

    if missing:
        print(f"  {missing} finding(s) kept their original severity")

    return findings


# Compare the severity originally assigned by the analysis agent
# with the final severity assigned by the classifier.
def compare(findings):
    from collections import Counter

    pairs = Counter(
        (
            finding.get("severity_initial", ""),
            finding.get("severity", "")
        )
        for finding in findings
    )

    print(f"{'produced by agent':<20}{'classifier':<14}{'count':>7}")

    for (before, after), count in pairs.most_common():
        mark = "  (unchanged)" if before == after else ""
        print(f"{str(before):<20}{str(after):<14}{count:>7}{mark}")