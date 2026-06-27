# Vsision Agent 

import base64
import json
from config import client, MODEL

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def analyse(pages):
    print("Vision Agent starting analysis...")
    all_findings = []

    for page in pages:
        print(f"  Analysing: {page['url']}")
        image_data = encode_image(page["screenshot"])

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert QA engineer specialising in UI/UX 
and functional testing. Analyse the provided screenshot of a web 
application and identify any defects, issues, or areas of concern.

For each issue found, respond in this exact JSON format:
{
    "findings": [
        {
            "issue_type": "visual|functional|ux",
            "description": "Clear description of the issue",
            "severity": "critical|major|minor",
            "location": "Where on the page the issue is",
            "recommended_fix": "Specific actionable fix for this issue"
        }
    ]
}

Be specific and thorough. Look for:
- Broken or incorrect images
- Layout issues or misaligned elements  
- Missing or incorrect text
- Broken buttons or interactive elements
- Poor colour contrast or accessibility issues
- Confusing or misleading UI elements
- Form validation issues

Respond ONLY with the JSON, no extra text."""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Please analyse this screenshot from the page: {page['url']}"
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

        result = json.loads(raw)
        findings = result.get("findings", [])

        print(f"  Found {len(findings)} issue(s)")
        for f in findings:
            f["page_url"] = page["url"]
            all_findings.append(f)

    print(f"Vision Agent complete — {len(all_findings)} total findings")
    return all_findings