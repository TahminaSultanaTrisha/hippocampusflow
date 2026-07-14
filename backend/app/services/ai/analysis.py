"""Runs the full pipeline for one scan, as a background task:

  read image -> classify (Call 1) -> retrieve related memories ->
  route -> specialist agent (Call 2, with memory context) ->
  save results -> store a new memory -> status 'complete'

Phase 3 addition: the two memory steps. This is what turns a scanner into
an assistant -- every analysis knows what came before it.
"""
import json
import logging

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.scan import Scan
from app.models.scan_result import ScanResult
from app.services import memory_service
from app.services.ai import classifier, client, router
from app.services.storage_service import LocalImageStorage

logger = logging.getLogger("hippocampusflow.analysis")


def run_analysis(scan_id: str) -> None:
    db = SessionLocal()
    try:
        scan = db.get(Scan, scan_id)
        if scan is None:
            return
        scan.status = "analyzing"
        db.commit()

        path = LocalImageStorage().path_for(scan.image_key)
        image_bytes = path.read_bytes()
        ext = path.suffix.lstrip(".")

        # Call 1 -- classify
        c = classifier.classify(image_bytes, ext)
        scan.category = c["category"]
        scan.confidence = c["confidence"]
        db.commit()

        # Memory retrieval: what do we already know that's relevant?
        memories = memory_service.related(db, scan.user_id, c["observations"], limit=5)
        memory_block = memory_service.format_block(memories)

        # Route -> Call 2 -- specialist analysis (now memory-aware)
        agent = router.route(c["category"])
        result = client.complete_json(
            model=get_settings().agent_model,
            system=agent.system_prompt,
            content=[
                client.image_block(image_bytes, ext),
                {"type": "text",
                 "text": f"First-pass observations: {c['observations']}\n\n"
                         f"{memory_block}\n"
                         f"Analyze this {c['category']} for the user."},
            ],
        )

        scan.summary = result.get("summary", "")
        db.add(ScanResult(
            scan_id=scan.id,
            agent=agent.name,
            details_json=json.dumps(result.get("details", {})),
            actions_json=json.dumps(result.get("suggested_actions", [])),
        ))
        scan.status = "complete"
        db.commit()

        # Store what to remember for next time.
        memory_service.remember(db, scan.user_id, scan.id,
                                result.get("memory", ""))
    except Exception as exc:
        logger.exception("Analysis failed for scan %s", scan_id)
        db.rollback()
        scan = db.get(Scan, scan_id)
        if scan is not None:
            scan.status = "failed"
            scan.summary = f"Analysis failed: {exc}"
            db.commit()
    finally:
        db.close()
