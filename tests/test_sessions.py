from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from valaris_agent_system import ConversationMessage, TurnResult
from valaris_agent_system.sessions import Checkpoint, FileSessionStore, SessionState


class SessionStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = FileSessionStore(Path(self.temp_dir.name))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_guardar_sesion(self) -> None:
        session = SessionState(session_id="session-save")

        self.store.save_session(session)

        self.assertTrue((Path(self.temp_dir.name) / "session-save" / "session.json").exists())

    def test_cargar_sesion(self) -> None:
        session = SessionState(session_id="session-load")
        self.store.save_session(session)

        loaded = self.store.load_session("session-load")

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.session_id, "session-load")

    def test_checkpoint(self) -> None:
        result = TurnResult(
            session_id="session-checkpoint",
            final_output="done",
            messages=[ConversationMessage(role="assistant", content="done")],
            events=[],
            turns_used=1,
        )

        saved_session = self.store.save_result(result)
        checkpoint = self.store.load_checkpoint("session-checkpoint", saved_session.last_checkpoint)

        self.assertIsInstance(checkpoint, Checkpoint)
        self.assertEqual(checkpoint.session_id, "session-checkpoint")
        self.assertEqual(checkpoint.result.final_output, "done")
