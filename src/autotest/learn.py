"""Helpers for the student exercises (not part of the system under test)."""


def todo(message: str = "") -> None:
    """Mark a step you have not done yet: fails the test with a readable TODO message.

    Every exercise test starts with a call to ``todo(...)``. When you begin working on that
    test, DELETE the call. The test then passes only if your own code is correct.
    """
    __tracebackhide__ = True            # pytest: do not show this helper frame, only YOUR test
    raise AssertionError(f"TODO - {message}" if message else "TODO - complete this exercise")
