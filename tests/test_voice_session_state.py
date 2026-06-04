from services.voice_session import SessionState, VoiceSession


def test_confirm_prefers_pending_action_params_for_confirmation_only_intents():
    session = VoiceSession("session-1")
    session.intent = "inbox.approve"
    session.state = SessionState.CONFIRMING
    session.pending_action = {
        "intent": "inbox.approve",
        "params": {"ref_id": "REF-123"},
    }

    confirmed = session.confirm()

    assert confirmed["intent"] == "inbox.approve"
    assert confirmed["params"] == {"ref_id": "REF-123"}
    assert session.state == SessionState.EXECUTING
