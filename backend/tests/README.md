# Backend test datasets

From the repository root, run the offline suite:

    uv --directory backend run --locked --no-sync pytest -q -rs -m "not costs-money" tests

Algorithm tests use small synthetic evidence fixtures. Regression, request-validation,
MCP and legacy-package checks run with the packages currently installed.

Tests marked lp_dataset require all six baseline frameworks to declare stored
learning progressions. During the code-first migration they report explicit skips.
They run automatically once all six LP packages are installed. Package validation
still runs before checking availability: invalid packages fail, and missing or
unexpected baseline frameworks fail rather than being treated as pending LP data.
Some acceptance tests assert exact totals for the complete dataset (8,080 edges and
6,522 connected pairs), so these are not partial-dataset acceptance checks.

All six runtime LP packages are now installed. Require complete dataset acceptance:

    uv --directory backend run --locked --no-sync pytest -q -rs -m "not costs-money" --require-lp-dataset tests

The strict option fails when LP migrations are missing. No dataset acceptance tests
should skip; the legacy-only package test may skip once no legacy packages remain.
Package changes also need read-only validation of each affected package.
