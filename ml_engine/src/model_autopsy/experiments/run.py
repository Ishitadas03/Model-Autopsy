"""Module entry point for executing experiments via python -m model_autopsy.experiments.run."""

import sys
from scripts.experiments.run_e001 import main

if __name__ == "__main__":
    sys.exit(main())
