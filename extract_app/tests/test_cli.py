import subprocess
import pytest

# ✅ Valid test cases
@pytest.mark.parametrize("args, expected_exit", [
    (["run", "--format", "sql", "--pipeline", "x", "--config", "y"], 0),
    (["run", "--format", "csv", "--pipeline", "pipeline_name", "--config", "conf.json"], 0),
    (["logs", "--pipeline", "x"], 0),
    (["debug","--connection","api"], 0),
    (["debug","--connection","sql"], 0)
])

def test_valid_inputs(args, expected_exit):
    result = subprocess.run(["python", "main.py"] + args, capture_output=True, text=True)
    assert result.returncode == expected_exit, (
        f"Expected {expected_exit}, got {result.returncode}.\n"
        f"Command: {' '.join(args)}\n"
        f"STDOUT: {result.stdout}\n"
        f"STDERR: {result.stderr}"
    )


# ❌ Invalid test cases
@pytest.mark.parametrize("args, expected_exit", [
    ([], 0),  # should show help and exit cleanly
    (["rn", "--format", "sql", "--pipeline", "x", "--config", "y"], 2),
    (["run", "--format", "sql"], 2),  # missing pipeline and config
    (["run", "--format", "json", "--pipeline", "x", "--config", "y"], 2),  # invalid format
    (["-logs", "--format", "sql", "--pipeline", "x", "--config", "y", "--extra", "oops"], 2),  # unknown arg
    (["logs", "--format", "sql", "--pipeline", "x", "--config", "y", "--extra", "oops"], 2),  # extra parameters
    (["logs",""], 2),  # missing parameters
])

def test_invalid_inputs(args, expected_exit):
    result = subprocess.run(["python", "main.py"] + args, capture_output=True, text=True)
    assert result.returncode == expected_exit
    assert result.stderr or result.stdout  # Output must say something

