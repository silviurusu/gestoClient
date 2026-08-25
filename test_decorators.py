import logging
import pytest

import util  # noqa: F401  -- must be imported before decorators (circular import)
import decorators


class _RecordingHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())


@pytest.fixture
def log_messages():
    logger = logging.getLogger("decorators")
    handler = _RecordingHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    yield handler.messages
    logger.removeHandler(handler)


def test_time_log_logs_exit_when_function_returns(log_messages):
    @decorators.time_log
    def ok():
        return 42

    assert ok() == 42
    assert log_messages[0] == ">>> ok()"
    assert log_messages[-1].startswith("<<< ok() - duration = ")


def test_time_log_logs_exit_when_function_raises(log_messages):
    @decorators.time_log
    def boom():
        raise ValueError("boom")

    with pytest.raises(ValueError):
        boom()

    assert log_messages[0] == ">>> boom()"
    assert log_messages[-1].startswith("<<< boom() - duration = ")


def test_time_log_logs_exit_on_sys_exit(log_messages):
    @decorators.time_log
    def bye():
        raise SystemExit(2)

    with pytest.raises(SystemExit):
        bye()

    assert log_messages[-1].startswith("<<< bye() - duration = ")
