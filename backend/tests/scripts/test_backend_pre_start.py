from unittest.mock import MagicMock, patch

from app.backend_pre_start import init, logger


def test_init_successful_connection() -> None:
    engine_mock = MagicMock()

    session_mock = MagicMock()
    exec_mock = MagicMock(return_value=True)
    session_mock.configure_mock(**{"exec.return_value": exec_mock})

    # Mock Session to work as a context manager
    session_context_mock = MagicMock()
    session_context_mock.__enter__ = MagicMock(return_value=session_mock)
    session_context_mock.__exit__ = MagicMock(return_value=False)

    with (
        patch("app.backend_pre_start.Session", return_value=session_context_mock),
        patch.object(logger, "info"),
        patch.object(logger, "error"),
        patch.object(logger, "warn"),
    ):
        try:
            init(engine_mock)
            connection_successful = True
        except Exception:
            connection_successful = False

        assert (
            connection_successful
        ), "The database connection should be successful and not raise an exception."

        # Just verify exec was called once (can't compare select(1) objects directly)
        session_mock.exec.assert_called_once()
