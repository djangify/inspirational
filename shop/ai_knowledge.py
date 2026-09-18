# shop/ai_knowledge.py
"""
AI-assisted drafting of a product's "Product Knowledge" (problem solved, who
it's for, differentiator, search keywords) and buyer Q&A: the plain-language
layer AI systems like ChatGPT and Claude need to understand, recommend and
cite a product, kept separate from persuasive sales copy.

This module only drafts. Nothing here touches the database; the admin view
that calls it shows the draft for the owner to edit and only saves what they
approve.
"""
import json

from django.conf import settings
from django.utils.html import strip_tags

MODEL = "claude-sonnet-5"


class KnowledgeDraftError(Exception):
    """Raised when a draft can't be generated; message is safe to show the owner."""


def generate_knowledge_draft(product):
    """Call Claude for a draft ProductKnowledge + Q&A for the given product.

    Returns a dict: problem_solved, target_audience, differentiator,
    search_keywords, questions (list of {"question", "answer"}, up to 8).
    """
    api_key = getattr(settings, "ANTHROPIC_API_KEY", None)
    if not api_key:
        raise KnowledgeDraftError(
            "ANTHROPIC_API_KEY is not configured, so AI drafting is unavailable."
        )

    import anthropic

    description = strip_tags(product.description or "").strip()
    category = product.category.name if product.category_id else ""

    prompt = (
        "You are helping a small digital-product store owner write the "
        "'Product Knowledge' layer for one product on their site: plain-language "
        "facts an AI system (ChatGPT, Claude, Perplexity) or a search engine could "
        "lift directly into an answer, kept separate from persuasive sales copy.\n\n"
        f"Product title: {product.title}\n"
        f"Category: {category}\n"
        f"Existing description: {description[:1000]}\n\n"
        "Respond with ONLY valid JSON (no markdown fences, no commentary) matching "
        "exactly this shape:\n"
        "{\n"
        '  "problem_solved": "the specific problem a buyer has that this solves, one or two sentences",\n'
        '  "target_audience": "the specific kind of person this is for, not \'everyone\'",\n'
        '  "differentiator": "what sets this apart from other ways to solve the same problem",\n'
        '  "search_keywords": "comma-separated search terms someone would use before buying this",\n'
        '  "questions": [\n'
        '    {"question": "a real buyer question", "answer": "a direct, plain-language answer"}\n'
        "  ]\n"
        "}\n\n"
        "Write 4 to 6 questions. Keep every field concrete to this specific product, "
        "not generic filler. Never use an em dash; use a comma, period, or 'and' instead."
    )

    client = anthropic.Anthropic(api_key=api_key)
    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as exc:
        raise KnowledgeDraftError(f"The AI request failed: {exc}") from exc

    text_block = next(
        (b for b in message.content if getattr(b, "type", None) == "text"), None
    )
    if text_block is None:
        raise KnowledgeDraftError("The AI response didn't include any text.")
    text = text_block.text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError) as exc:
        raise KnowledgeDraftError(
            "The AI response wasn't valid JSON, please try again."
        ) from exc

    raw_questions = data.get("questions") or []
    questions = [
        {
            "question": str(q.get("question", "")).strip(),
            "answer": str(q.get("answer", "")).strip(),
        }
        for q in raw_questions
        if isinstance(q, dict) and str(q.get("question", "")).strip()
    ][:8]

    return {
        "problem_solved": str(data.get("problem_solved", "")).strip(),
        "target_audience": str(data.get("target_audience", "")).strip(),
        "differentiator": str(data.get("differentiator", "")).strip(),
        "search_keywords": str(data.get("search_keywords", "")).strip(),
        "questions": questions,
    }
