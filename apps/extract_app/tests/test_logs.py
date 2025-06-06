import subprocess
import pytest


@pytest.mark.parametrize("args , expected_exit",[
    (["logs","--config","docs/pipeline_config.json","--pipeline","test-modis_daily_ndvi_jal_002","--options","region:002"],0),
    (["logs","--config","docs/pipeline_config.json","--pipeline","test-modis_daily_ndvi_jal_002","--options","run_date:2025-04-30"],0),
    (["logs","--config","docs/pipeline_config.json","--pipeline","test-modis_daily_ndvi_jal_002","--options","from_date:2011-01-01"],0),
    (["logs","--config","docs/pipeline_config.json","--pipeline","test-modis_daily_ndvi_jal_002","--options","message:Termino con exito"],0),
    (["logs","--config","docs/pipeline_config.json","--pipeline","test-modis_daily_ndvi_jal_002"],0)
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
    (["logs","--config","docs/pipeline_config.json","--pipeline","test-modis_daily_ndvi_jal_002","--options",],2),
    (["logs","--config","--pipeline","test-modis_daily_ndvi_jal_002","--options","run_date:2025-04-30"],2),
    (["logs","--config","docs/pipeline_config.json","--pipeline","--options","from_date:2011-01-01"],2),
    (["logs","--config","docs/pipeline_config.json","--pipeline","test-modis_daily_ndvi_jal_002","--options","massage:Termino con exito"],0),
    (["logs","--config","docs/pipeline_config.json","--pipeline","test-modis_daily_ndvi_jal_"],0)
])

def test_invalid_inputs(args, expected_exit):
    result = subprocess.run(["python", "main.py"] + args, capture_output=True, text=True)
    assert result.returncode == expected_exit
    assert result.stderr or result.stdout
