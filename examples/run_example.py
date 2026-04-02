from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path

from valaris_agent_system.runtime.app import create_app
from valaris_agent_system.sessions.store import FileSessionStore
from document_automation.workflow import (
    DocumentAutomationService,
    DocumentJob,
    build_document_runtime,
)


async def main() -> None:
    runtime = build_document_runtime()
    app = create_app(runtime)
    print("FastAPI app initialized:", app.title)

    base_dir = Path(__file__).resolve().parent / "document_automation"
    session_store = FileSessionStore(base_dir / ".sessions")
    workflow = DocumentAutomationService(
        runtime=runtime,
        session_store=session_store,
        workspace=base_dir,
    )

    source_document = base_dir / "fixtures" / "source_document.txt"
    job = DocumentJob(
        session_id="document-demo",
        source_uri=source_document.resolve().as_uri(),
        download_path="artifacts/downloads/source_document.txt",
        report_path="artifacts/reports/source_document.report.json",
        min_char_count=80,
        required_terms=["compliance", "approval", "validation"],
    )
    shutil.rmtree(session_store.root / job.session_id, ignore_errors=True)

    result = await workflow.run_job(job)
    saved_state = session_store.load_session(job.session_id)
    assert saved_state is not None
    assert saved_state.result is not None
    assert saved_state.result.status == "completed"

    report_path = base_dir / "artifacts" / "reports" / "source_document.report.json"
    assert report_path.exists()

    print("\nDOCUMENT WORKFLOW RESULT")
    print(json.dumps(result.model_dump(mode="json"), indent=2))

    print("\nSAVED SESSION SUMMARY")
    print(json.dumps(saved_state.result.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
