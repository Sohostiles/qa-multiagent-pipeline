# Run the pipeline and handle unexpected errors
import logging

import db
from orchestrator import run_pipeline

logger = logging.getLogger(__name__)


def run_test(run_id, url, login_config=None):
    try:
        run_pipeline(
            url=url,
            login_config=login_config,
            run_id=run_id
        )
    except Exception:
        # Save the failure so the dashboard can show it
        db.update_run_status(run_id, "failed")

        # Print the full error in the server terminal
        logger.exception("Pipeline failed for run %s", run_id)