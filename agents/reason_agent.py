# Reason Agent 

import re

import json
from config import client, MODEL, chat_with_retry

# Trim a raw DOM to structure and text, strip scripts and styles, cap length
# Keep error and message regions even if they sit deep in the DOM
def _trim_dom(dom, max_chars=8000):
    if not dom:
        return ""
    # Remove script and style blocks entirely
    dom = re.sub(r"<script[\s\S]*?</script>", "", dom, flags=re.IGNORECASE)
    dom = re.sub(r"<style[\s\S]*?</style>", "", dom, flags=re.IGNORECASE)
    # Remove long inline style attributes
    dom = re.sub(r'\sstyle="[^"]*"', "", dom)
    # Collapse whitespace
    dom = re.sub(r"\s+", " ", dom).strip()

    if len(dom) <= max_chars:
        return dom

    # Pull out windows of text around error or message keywords so defect
    # evidence deep in the DOM survives truncation
    keywords = ["error", "required", "invalid", "warning", "must be"]
    windows = []
    low = dom.lower()
    for kw in keywords:
        start = 0
        while True:
            i = low.find(kw, start)
            if i == -1:
                break
            # Grab a window of characters around the keyword for context
            windows.append(dom[max(0, i - 120): i + 120])
            start = i + len(kw)
    error_text = " ".join(windows)[:2000]

    # Keep the start of the DOM for structure, plus any error windows found
    head = dom[: max_chars - len(error_text) - 50]
    if error_text:
        return head + " ... ERROR REGIONS: " + error_text
    return head

# Reduce a DOM to a structural fingerprint for dedup
# Strips digits and whitespace so states that differ only in counts or
# data values collapse to the same fingerprint
def _fingerprint(dom):
    dom = re.sub(r"\d+", "", dom or "")   # remove numbers like cart counts
    dom = re.sub(r"\s+", "", dom)          # remove whitespace
    return dom

def analyse(pages):
    print("Reason Agent starting analysis...")
    all_findings = []
    seen = set()

    for page in pages:
        dom = _trim_dom(page.get("dom", ""))
        if not dom:
            print(f"  No DOM for {page['url']}, skipping")
            continue

        # Interaction states are handled by transition analysis, skip them here
        if page.get("interaction"):
            continue

        # Skip near-duplicate states already analysed this run
        # Include the URL so distinct pages (e.g. different product items) are
        # never collapsed together, even if their DOM structure is similar
        fp = page.get("url", "") + "|" + _fingerprint(dom)
        if fp in seen:
            print(f"  Skipping near-duplicate: {page['url']}")
            continue
        seen.add(fp)

        print(f"  Analysing: {page['url']}")

        response = chat_with_retry(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert QA engineer analysing the DOM of a
                                web application for FUNCTIONAL defects. You reason about
                                behaviour and structure, not visual appearance.

                                Report every functional defect the DOM clearly shows, and
                                describe it clearly. Do not hold back on genuine problems.

                                At the same time, only report what the DOM actually shows.
                                Do not invent defects, and do not report visual or styling
                                issues (those are handled separately). If you are unsure
                                whether something is a real defect, you may still report it
                                but mark it as low confidence.

                                Typical functional defects include form fields missing
                                validation or required attributes, inputs without labels or
                                accessible names, controls that lead nowhere, duplicate
                                element ids, missing alt text on images, and incorrect or
                                missing responses to a user action.

                                For each defect, respond in this exact JSON format:
                                {
                                    "findings": [
                                        {
                                            "issue_type": "functional|accessibility",
                                            "description": "Clear description of the defect",
                                            "severity": "critical|major|minor",
                                            "confidence": "high|medium|low",
                                            "location": "Element or region the defect relates to",
                                            "recommended_fix": "Specific actionable fix"
                                        }
                                    ]
                                }

                                If the DOM shows no clear functional defects, return
                                {"findings": []}. Respond ONLY with the JSON, no extra text."""
                },
                {
                    "role": "user",
                    "content": f"""Analyse the DOM of this page: {page['url']}

DOM:
{dom}"""
                }
            ],
            max_tokens=1000
        )

        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            print(f"  Could not parse response for {page['url']}, skipping")
            continue

        findings = result.get("findings", [])

        print(f"  Found {len(findings)} issue(s)")
        for f in findings:
            f["page_url"] = page["url"]
            f["source"] = "reason"
            all_findings.append(f)

    print(f"Reason Agent complete, {len(all_findings)} total findings")
    return all_findings
        
# Analyse a before and after DOM pair for one interaction state
# Judges whether the change caused by the action was correct
# Runs only on states that carry a dom_before, so it is separate from per state analysis
def analyse_transitions(pages):
    print("Reason Agent starting transition analysis...")
    all_findings = []

    seen = set()
    for page in pages:
        # Only interaction states with a recorded before state qualify
        if not page.get("interaction") or not page.get("dom_before"):
            continue

        before = _trim_dom(page.get("dom_before", ""))
        after = _trim_dom(page.get("dom", ""))

        # Skip near-duplicate transitions (same before and after fingerprint)
        fp = _fingerprint(before) + "|" + _fingerprint(after)
        if fp in seen:
            print(f"  Skipping near-duplicate transition: {page['url']}")
            continue
        seen.add(fp)

        print(f"  Comparing before and after: {page['url']} ({page.get('action','')})")

        response = chat_with_retry(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert QA engineer judging whether a user
                                action produced the correct change in a web application.
                                You are given the DOM BEFORE the action and the DOM AFTER
                                the action, plus a description of the action.

                                Reason about whether the change is correct and complete.
                                Report a defect only when the transition is clearly wrong,
                                for example: the action had no effect when it should have,
                                an error response is missing or incomplete, an expected
                                state change did not happen, or the wrong thing changed.

                                Do not report visual or styling issues. Do not invent
                                defects. If you are unsure, you may report it as low
                                confidence.

                                For each defect, respond in this exact JSON format:
                                {
                                    "findings": [
                                        {
                                            "issue_type": "functional|accessibility",
                                            "description": "What went wrong in the transition",
                                            "severity": "critical|major|minor",
                                            "confidence": "high|medium|low",
                                            "location": "Element or region involved",
                                            "recommended_fix": "Specific actionable fix"
                                        }
                                    ]
                                }

                                If the transition looks correct, return {"findings": []}.
                                Respond ONLY with the JSON, no extra text."""
                },
                {
                    "role": "user",
                    "content": f"""Page: {page['url']}
Action taken: {page.get('action','')}
Intent: {page.get('action_reason','')}

DOM BEFORE the action:
{before}

DOM AFTER the action:
{after}

Was this change correct and complete?"""
                }
            ],
            max_tokens=1000
        )

        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            print(f"  Could not parse response for {page['url']}, skipping")
            continue

        findings = result.get("findings", [])

        print(f"  Found {len(findings)} transition issue(s)")
        for f in findings:
            f["page_url"] = page["url"]
            f["source"] = "reason_transition"
            all_findings.append(f)

    print(f"Transition analysis complete, {len(all_findings)} findings")
    return all_findings

