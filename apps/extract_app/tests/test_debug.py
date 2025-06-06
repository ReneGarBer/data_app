import subprocess
import pytest


@pytest.mark.parametrize("args , expected_exit",[
    (["debug","--ini","docs/credentials.ini","--con","dengueappstg"],0),
    (["debug","--con","dengueappstg"],0),
    (["debug","--ini","docs/credentials.ini","--con","eeAPI"],0),
    (["debug","--con","eeAPI"],0)
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
    #missing/wrong --ini
    (["debg","docs/credentials.ini","--con","dengueappstg"],2),
    (["debug","--ini","","con","dengueappstg"],2),
    (["debug","--ini","docs/credent.ini","con","dengueappstg"],2),
    (["debug","ini","--con","dengueappstg"],2),
    #missing/wrong --con
    (["debug","--ini","docs/credentials.ini","con","dengueappstg"],2),
    (["debug","--ini","docs/credentials.ini","--con",""],0),
    (["debug","--ini","docs/credentials.ini","--con"],2),
    (["debug","--ini","docs/credentials.ini","","dengueappstg"],2),
    (["debug","--ini","docs/credentials.ini","--con","eappstg"],0)
])

def test_invalid_inputs(args, expected_exit):
    result = subprocess.run(["python", "main.py"] + args, capture_output=True, text=True)
    assert result.returncode == expected_exit
    assert result.stderr or result.stdout
