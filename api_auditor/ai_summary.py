from anthropic import Anthropic


def generate_ai_summary(metadata, operations, findings):
    try:
        client = Anthropic()

        prompt = f"""
        You are helping a Forward Deployed Engineer explain an OpenAPI integration-readiness audit.

        API title: {metadata["title"]}
        API version: {metadata["version"]}
        Spec version: {metadata["openapi_version"]}
        Operations checked: {len(operations)}
        Findings: {findings}

        Write a concise plain-English summary for an integrating engineer.
        Do not invent issues that are not in the findings.
        If there are no findings, say the audited checks passed, but mention that this is not a full OpenAPI validation.
        Keep it under 150 words.
        """

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=250,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text
    except Exception as error:
        return f"AI summary could not be generated: {error}"
