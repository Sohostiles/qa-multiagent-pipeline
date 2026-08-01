# Vsision Agent 

import re

import base64
import json
from config import chat_with_retry, client, MODEL

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Trim a raw DOM down to structure and text for the Vision Agent
# Strips scripts, styles, and inline style noise, then caps the length
def _trim_dom(dom, max_chars=4000):
    if not dom:
        return ""
    # Remove script and style blocks entirely
    dom = re.sub(r"<script[\s\S]*?</script>", "", dom, flags=re.IGNORECASE)
    dom = re.sub(r"<style[\s\S]*?</style>", "", dom, flags=re.IGNORECASE)
    # Remove long inline style attributes
    dom = re.sub(r'\sstyle="[^"]*"', "", dom)
    # Collapse whitespace
    dom = re.sub(r"\s+", " ", dom).strip()
    return dom[:max_chars]

def analyse(pages):
    print("Vision Agent starting analysis...")
    all_findings = []

    for page in pages:
        print(f"  Analysing: {page['url']}")
        image_data = encode_image(page["screenshot"])

        # Extra context for interaction-derived states
        if page.get("interaction"):
            interaction_note = (
                f"\nThis state resulted from an interaction: {page.get('action','')}."
                f" Intent: {page.get('action_reason','')}."
                f" Judge whether the visual response to this action looks correct."
            )
        else:
            interaction_note = ""

        response = chat_with_retry(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert QA engineer reviewing a screenshot
                                of a web application for VISUAL defects.

                                Report every defect you can actually see in the image, and
                                describe it clearly. Do not hold back on genuine problems.

                                At the same time, only report what the image really shows.
                                Do not invent defects, and do not guess about behaviour a
                                static image cannot reveal, such as whether a link works or
                                whether a click does something. If you are unsure whether
                                something is a real defect, you may still report it but say
                                clearly that it is uncertain.

                                Typical visual defects include broken or missing images,
                                overlapping or cut-off elements, misaligned layout, unreadable
                                or low-contrast text, duplicated content, and obviously broken
                                rendering.

                                For each defect, respond in this exact JSON format:
                                {
                                    "findings": [
                                        {
                                            "issue_type": "visual|ux",
                                            "description": "Clear description of the visible defect",
                                            "severity": "critical|major|minor",
                                            "confidence": "high|medium|low",
                                            "location": "Where on the page the defect is",
                                            "recommended_fix": "Specific actionable fix"
                                        }
                                    ]
                                }

                                If the page genuinely looks correct, return {"findings": []}.
                                Respond ONLY with the JSON, no extra text."""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""Analyse this screenshot from the page: {page['url']}

The page DOM is provided below for cross-checking what you see. Use it to confirm
whether something is truly a defect (for example, whether an element is actually
present or missing). Judge visual appearance from the image, not the DOM.
{interaction_note}

DOM:
{_trim_dom(page.get('dom', ''))}"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_data}"
                            }
                        }
                    ]
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
            all_findings.append(f)

    print(f"Vision Agent complete — {len(all_findings)} total findings")
    return all_findings