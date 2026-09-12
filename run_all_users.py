# run_all_users.py
# Run the pipeline for each SauceDemo user to build a dataset to train DISTILBERT
# Each finding stores to the DB with its own run_id

from orchestrator import run_pipeline, SAUCEDEMO_LOGIN

USERS = [
    "standard_user",
    "problem_user",
    "error_user",
    "visual_user",
    "performance_glitch_user",
    "locked_out_user",
]

if __name__ == "__main__":
    results = []
    for user in USERS:
        print(f"\n{'#'*60}")
        print(f"Running pipeline for user: {user}")
        print(f"{'#'*60}")
        try:
            result = run_pipeline(
                url="https://www.saucedemo.com/",
                login_config={**SAUCEDEMO_LOGIN, "username": user},
            )
            results.append((user, result["run_id"], len(result["findings"])))
        except Exception as e:
            # locked_out_user is expected to fail at login
            print(f"Pipeline failed for user {user}: {e}")
            results.append((user, None, 0))

    print(f"\n{'='*60}")
    print("ALL RUNS COMPLETE")
    print(f"{'='*60}")
    print(f"{'User':<26} {'Run ID':>8} {'Findings':>10}")
    print("-" * 46)
    for user, run_id, n in results:
        rid = str(run_id) if run_id is not None else "FAILED"
        print(f"{user:<26} {rid:>8} {n:>10}")
        