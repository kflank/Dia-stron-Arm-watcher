from src.state_machine import FreezeStateMachine


def test_freeze_and_recover_transitions():
    machine = FreezeStateMachine(freeze_seconds=5, recover_seconds=2, cooldown_seconds=10)

    status, alert = machine.update(motion_present=True, now=0)
    assert status == "MOVING"
    assert alert is False

    status, alert = machine.update(motion_present=False, now=5)
    assert status == "FROZEN"
    assert alert is True

    status, alert = machine.update(motion_present=False, now=6)
    assert status == "FROZEN"
    assert alert is False

    status, alert = machine.update(motion_present=True, now=7)
    assert status == "FROZEN"
    assert alert is False

    status, alert = machine.update(motion_present=True, now=9.1)
    assert status == "MOVING"
    assert alert is False
