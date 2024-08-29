import unittest
import csv
import os
from unittest.mock import patch, MagicMock
from mbench.profile import FunctionProfiler

class TestFunctionProfiler(unittest.TestCase):
    def setUp(self):
        self.test_csv_file = "test_profile.csv"
        self.profiler = FunctionProfiler()
        self.profiler.csv_file = self.test_csv_file

    def tearDown(self):
        if os.path.exists(self.test_csv_file):
            os.remove(self.test_csv_file)

    def test_save_data(self):
        self.profiler.profiles["test_func"] = {
            "calls": 1,
            "total_time": 0.1,
            "total_cpu": 0.05,
            "total_memory": 1000,
            "total_gpu": 500,
            "total_io": 200,
            "notes": "Test note",
        }
        self.profiler.save_and_print_data()

        # Read the saved data
        with open(self.profiler.csv_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Check if there's exactly one data row
        self.assertEqual(len(rows), 1)

        # Check the values
        row = rows[0]
        self.assertEqual(row["Function"], "test_func")
        self.assertEqual(int(row["Calls"]), 1)
        self.assertEqual(float(row["Total Time"]), 0.1)
        self.assertEqual(float(row["Total CPU"]), 0.05)
        self.assertEqual(float(row["Total Memory"]), 1000)
        self.assertEqual(float(row["Total GPU"]), 500)
        self.assertEqual(float(row["Total IO"]), 200)
        self.assertEqual(row["Notes"], "Test note")

    def test_load_data(self):
        self.profiler.csv_file = 'test.csv'
        with open(self.profiler.csv_file, 'w') as f:
            f.write('Function,Calls,Total Time,Total CPU,Total Memory,Total GPU,Total IO,Avg Duration,Avg CPU Usage,Avg Memory Usage,Avg GPU Usage,Avg IO Usage,Notes\n')
            f.write('test_func,1,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,Test note\n')
        loaded_profiles = self.profiler.load_data()
        self.assertEqual(loaded_profiles['test_func']['calls'], 1)
        self.assertEqual(loaded_profiles['test_func']['total_time'], 1.0)
        self.assertEqual(loaded_profiles['test_func']['notes'], 'Test note')

    @patch('time.time')
    @patch('psutil.virtual_memory')
    @patch('pynvml.nvmlDeviceGetMemoryInfo')
    def test_start_profile(self, mock_nvml, mock_psutil, mock_time):
        mock_time.return_value = 1.0
        mock_psutil.return_value.used = 1024
        mock_nvml.return_value.used = 1024
        mock_frame = MagicMock()
        mock_frame.f_code.co_name = 'test_func'
        mock_frame.f_back = MagicMock()
        mock_frame.f_back.f_globals = {'__name__': 'test_module'}
        self.profiler.set_target_module('test_module', 'caller')
        self.profiler._start_profile(mock_frame)
        self.assertEqual(self.profiler.current_calls['test_func']['start_time'], 1.0)

if __name__ == '__main__':
    unittest.main()
