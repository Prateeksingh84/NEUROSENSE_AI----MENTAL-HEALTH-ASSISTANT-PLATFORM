"""
==========================================================================
NeuroSense AI — Test Runner
==========================================================================

Usage:
    python tests/run_tests.py

Or:
    pytest tests -v
"""

import subprocess
import sys
from pathlib import Path


# ==========================================================================
# COLORS
# ==========================================================================

GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"


# ==========================================================================
# TEST FILES
# ==========================================================================

TEST_FILES = [
    "tests/test_auth.py",
    "tests/test_reports.py",
    "tests/test_emotion.py",
    "tests/test_dashboard.py",
    "tests/test_voice.py",
    "tests/test_handsign.py",
]


# ==========================================================================
# RUN TEST
# ==========================================================================

def run_test_file(test_file):

    print(
        f"\n{BLUE}Running {test_file}{RESET}"
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            test_file,
            "-v"
        ]
    )

    if result.returncode == 0:

        print(
            f"{GREEN}PASSED: {test_file}{RESET}"
        )

        return True

    else:

        print(
            f"{RED}FAILED: {test_file}{RESET}"
        )

        return False


# ==========================================================================
# MAIN
# ==========================================================================

def main():

    print(
        f"{BLUE}\nNeuroSense AI Test Suite\n{RESET}"
    )

    total = 0
    passed = 0

    for file in TEST_FILES:

        if not Path(file).exists():

            print(
                f"{RED}Missing: {file}{RESET}"
            )

            continue

        total += 1

        success = run_test_file(file)

        if success:
            passed += 1

    print("\n===================================")

    print(
        f"{BLUE}Total Test Files:{RESET} {total}"
    )

    print(
        f"{GREEN}Passed:{RESET} {passed}"
    )

    print(
        f"{RED}Failed:{RESET} {total - passed}"
    )

    print("===================================\n")

    if passed == total:

        print(
            f"{GREEN}All tests passed successfully!{RESET}"
        )

    else:

        print(
            f"{RED}Some tests failed.{RESET}"
        )


# ==========================================================================
# START
# ==========================================================================

if __name__ == "__main__":
    main()