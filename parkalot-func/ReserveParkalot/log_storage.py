# log_storage.py
#
# Captures everything logged during a single run and saves it as one file in
# Azure Blob Storage when the run finishes. Container logs are lost when the
# container is deleted, so this keeps a permanent history of every run.
#
# Configuration (environment variables):
#   LOG_STORAGE_CONNECTION_STRING  Azure Storage connection string. If unset,
#                                  the log is written to the local logs/ folder.
#   LOG_STORAGE_CONTAINER          Blob container name (default: parkalot-logs).

import io
import logging
import os
from datetime import datetime, timezone

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_CONTAINER = "parkalot-logs"


class RunLogCapture(logging.Handler):
    """Logging handler that keeps the whole run's log in memory."""

    def __init__(self):
        super().__init__(level=logging.INFO)
        self.setFormatter(logging.Formatter(LOG_FORMAT))
        self._buffer = io.StringIO()
        self.started_at = datetime.now(timezone.utc)
        self.highest_level = logging.NOTSET

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._buffer.write(self.format(record) + "\n")
            self.highest_level = max(self.highest_level, record.levelno)
        except Exception:
            self.handleError(record)

    def contents(self) -> str:
        return self._buffer.getvalue()

    def outcome(self) -> str:
        """Short label for the file name so failed runs stand out in a listing."""
        if self.highest_level >= logging.ERROR:
            return "FAILED"
        if self.highest_level >= logging.WARNING:
            return "WARNING"
        return "OK"

    def blob_name(self) -> str:
        ts = self.started_at
        return f"{ts:%Y/%m}/{ts:%Y-%m-%dT%H-%M-%SZ}_{self.outcome()}.log"


def save_run_log(capture: RunLogCapture) -> None:
    """Upload the captured log to Blob Storage, or save it locally as a fallback."""
    name = capture.blob_name()
    data = capture.contents().encode("utf-8")

    conn_str = os.environ.get("LOG_STORAGE_CONNECTION_STRING")
    if conn_str:
        container = os.environ.get("LOG_STORAGE_CONTAINER", DEFAULT_CONTAINER)
        try:
            from azure.core.exceptions import ResourceExistsError
            from azure.storage.blob import BlobServiceClient, ContentSettings

            service = BlobServiceClient.from_connection_string(conn_str)
            container_client = service.get_container_client(container)
            try:
                container_client.create_container()
            except ResourceExistsError:
                pass
            container_client.upload_blob(
                name,
                data,
                overwrite=True,
                content_settings=ContentSettings(content_type="text/plain; charset=utf-8"),
            )
            print(f"Run log uploaded to blob {container}/{name}", flush=True)
            return
        except Exception as e:
            # Never let log upload problems hide the run's own result.
            print(f"Failed to upload run log to Blob Storage: {e}", flush=True)
    else:
        print("LOG_STORAGE_CONNECTION_STRING not set; saving run log locally", flush=True)

    local_path = os.path.join(os.getcwd(), "logs", name.replace("/", "_"))
    try:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(data)
        print(f"Run log saved to {local_path}", flush=True)
    except Exception as e:
        print(f"Failed to save run log locally: {e}", flush=True)
