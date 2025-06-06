import subprocess
import pytest


@pytest.mark.parametrize("args , expected_exit",[
    (["run"],0)
])

def test_valid_inputs(args,expected_exit):
    result = subprocess.run(["python","main.py"]+args,capture_output=True,text=True)
    assert result.returncode==expected_exit, (
        f"Expected {expected_exit}, got {result.returncode}.\n"
        f"Command: {' '.join(args)}\n"
        f"STDOUT: {result.stdout}\n"
        f"STDERR: {result.stderr}"
    )


@pytest.mark.parametrize("args , expected_exit",[
    (["run"],2)
])

def test_invalid_inputs(args, expected_exit):
    result = subprocess.run(["python", "main.py"] + args, capture_output=True, text=True)
    assert result.returncode == expected_exit
    assert result.stderr or result.stdout
