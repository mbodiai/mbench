import pytest
from unittest.mock import patch, MagicMock
from mbench.profile import FunctionProfiler, profileme, profile, profiling, display_profile_info, _get_memory_usage, _get_io_usage
import os
import time
from rich.console import Console

console = Console()

@pytest.fixture
def profiler():
    return FunctionProfiler()

def test_load_data(profiler, tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text('Function,Calls,Total Time,Total CPU,Total Memory,Total GPU,Total IO,Avg Duration,Avg CPU Usage,Avg Memory Usage,Avg GPU Usage,Avg IO Usage,Notes\n'
                        'test_func,1,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,\n')
    profiler.csv_file = str(csv_file)
    profiler.load_data()
    assert profiler.profiles['test_func']['calls'] == 1

def test_save_and_print_data(profiler, tmp_path):
    csv_file = tmp_path / "test.csv"
    profiler.csv_file = str(csv_file)
    profiler.profiles['test_func'] = {
        'calls': 1,
        'total_time': 1.0,
        'total_cpu': 1.0,
        'total_memory': 1.0,
        'total_gpu': 1.0,
        'total_io': 1.0,
        'notes': ''
    }
    profiler.save_and_print_data()
    content = csv_file.read_text()
    assert 'test_func,1,1.000000,1.000000,1.000000,1.000000,1.000000,1.000000,1.000000,1.000000,1.000000,1.000000,' in content

def test_get_gpu_usage(profiler):
    total, usages = profiler._get_gpu_usage()
    assert isinstance(total, int)
    assert isinstance(usages, list)
    assert len(usages) == profiler.num_gpus
    assert all(isinstance(usage, int) for usage in usages)

def test_get_io_usage():
    io_usage = _get_io_usage()
    assert isinstance(io_usage, int)

def test_start_profile(profiler):
    with patch('time.time', return_value=1.0), \
         patch('psutil.virtual_memory', return_value=MagicMock(used=1024)), \
         patch('pynvml.nvmlDeviceGetMemoryInfo', return_value=MagicMock(used=1024)):
        mock_frame = MagicMock()
        mock_frame.f_globals = {'__name__': 'test_module'}
        mock_frame.f_code.co_name = 'test_func'
        profiler.set_target_module('test_module', 'all')
        profiler._start_profile(mock_frame)
        assert profiler.current_calls['test_func']['start_time'] == 1.0




@pytest.mark.parametrize("bytes_value, expected", [
    (1024, '1.00 KB'),
    (1024 * 1024, '1.00 MB'),
    (1024 * 1024 * 1024, '1.00 GB'),
    (500, '500.00 B'),
])
def test_format_bytes(profiler, bytes_value, expected):
    assert profiler.format_bytes(bytes_value) == expected

def test_profileme():
    with patch('mbench.profile.FunctionProfiler') as mock_profiler:
        profileme()
        assert mock_profiler.called

def test_profile():
    with patch('mbench.profile.FunctionProfiler') as mock_profiler, \
         patch.dict(os.environ, {'MBENCH': '1'}), \
         patch('mbench.profile._profiler_instance', mock_profiler.return_value):
        mock_instance = mock_profiler.return_value
        mock_instance._get_gpu_usage.return_value = 0
        mock_instance.format_bytes.return_value = "0 B"
        
        @profile
        def test_func():
            pass
        
        test_func()
        
        mock_instance._start_profile.assert_called()
        mock_instance._end_profile.assert_called()
        assert mock_profiler.called


@patch('mbench.profile._get_io_usage', return_value=0)
@patch('mbench.profile._get_gpu_usage', return_value=(0, [0]))
def test_min_duration(mock_gpu, mock_io):
    with patch.dict(os.environ, {'MBENCH': '1'}):
        with profiling("short_block"):
            time.sleep(0.1)
        with profiling("long_block"):
            time.sleep(1.1)

@patch('mbench.profile._get_io_usage', return_value=0)
@patch('mbench.profile._get_gpu_usage', return_value=(0, [0]))
def test_quiet_mode(mock_gpu, mock_io):
    with patch.dict(os.environ, {'MBENCH': '1'}):
        with profiling("quiet_block", quiet=True):
            pass

@patch('mbench.profile._get_io_usage', return_value=0)
@patch('mbench.profile._get_gpu_usage', return_value=(0, [0]))
def test_summary_mode(mock_gpu, mock_io):
    with patch.dict(os.environ, {'MBENCH': '1'}):
        @profile
        def test_func():
            pass

        test_func()
    
    assert 'test_profile.test_func' in FunctionProfiler().profiles
    assert FunctionProfiler().profiles['test_profile.test_func']['calls'] == 1

@patch('mbench.profile._get_io_usage', return_value=0)
@patch('mbench.profile._get_gpu_usage', return_value=(0, [0]))
def test_profiling(mock_gpu, mock_io):
    with patch.dict(os.environ, {'MBENCH': '1'}):
        with profiling('test_func'):
            pass

    assert 'test_func' in FunctionProfiler().profiles
    assert FunctionProfiler().profiles['test_func']['calls'] == 1

def test_display_profile_info():
    with patch('mbench.profile.console.print') as mock_print:
        display_profile_info(
            name="test_func",
            duration=1.0,
            cpu_usage=0.5,
            mem_usage=1024,
            gpu_usage=2048,
            io_usage=4096,
            avg_time=1.0,
            avg_cpu=0.5,
            avg_memory=1024,
            avg_gpu=2048,
            avg_io=4096,
            calls=1
        )
        mock_print.assert_called()

        mock_print.reset_mock()
        display_profile_info(
            name="test_func",
            duration=0.4,
            cpu_usage=0.2,
            mem_usage=512,
            gpu_usage=1024,
            io_usage=2048,
            avg_time=0.4,
            avg_cpu=0.2,
            avg_memory=512,
            avg_gpu=1024,
            avg_io=2048,
            calls=1
        )
        mock_print.assert_called()

        mock_print.reset_mock()
        display_profile_info(
            name="test_func",
            duration=1.0,
            cpu_usage=0.5,
            mem_usage=1024,
            gpu_usage=2048,
            io_usage=4096,
            avg_time=1.0,
            avg_cpu=0.5,
            avg_memory=1024,
            avg_gpu=2048,
            avg_io=4096,
            calls=1
        )
        mock_print.assert_called()
