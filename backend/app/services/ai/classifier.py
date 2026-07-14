"""Call 1 of the pipeline: fast, cheap category detection.
Phase 4.5: the category vocabulary expands to cover the full agent roster.
"""
from app.core.config import get_settings
from app.services.ai import client

CATEGORIES = [
    "food", "ingredients", "receipt", "document", "product", "electronics",
    "clothing", "furniture", "appliance", "household", "plant", "animal",
    "insect", "vehicle", "artwork", "landmark", "mineral", "damage",
    "unknown",
]

_HINTS = """Category guidance:
- food: a prepared meal or dish ready to eat
- ingredients: raw ingredients/groceries (use when it's components, not a dish)
- receipt: a printed till/purchase receipt
- document: any paper document, form, letter, card, or ID
- electronics: phones, laptops, gadgets, devices
- product: any other retail product or packaged item
- appliance/household: white goods, tools, household items
- damage: visible damage, faults, leaks, cracks, stains needing repair/cleaning
- artwork: paintings, sculptures, murals
- landmark: buildings, monuments, places
- mineral: rocks, stones, crystals"""

_SYSTEM = f"""You are the classification stage of a camera-scanning assistant.
Look at the image and respond with ONLY a JSON object, no other text:
{{"category": "<one of: {', '.join(CATEGORIES)}>",
 "confidence": <0.0-1.0>,
 "observations": "<2-3 sentences: what the object is, notable details, any visible text>"}}
{_HINTS}"""


def classify(image_bytes: bytes, ext: str) -> dict:
    result = client.complete_json(
        model=get_settings().classifier_model,
        system=_SYSTEM,
        content=[client.image_block(image_bytes, ext),
                 {"type": "text", "text": "Classify this image."}],
    )
    if result.get("category") not in CATEGORIES:
        result["category"] = "unknown"
    result["confidence"] = max(0.0, min(1.0, float(result.get("confidence", 0.5))))
    return result
