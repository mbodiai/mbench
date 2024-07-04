# Copyright (c) 2024 mbodi ai
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import atexit
import csv
import os
import sys
import time
from collections import defaultdict

import psutil
import pynvml
from rich import print


def format_bytes(bytes_value):
    gb = bytes_value / (1024 * 1024 * 1024)
    if gb >= 1:
        return f"{gb:.2f} GB"
    else:
        mb = bytes_value / (1024 * 1024)
        return f"{mb:.2f} MB"

class FunctionProfiler:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FunctionProfiler, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance

    def initialize(self):
        self.csv_file = 'profiling_data.csv'
        self.profiles = self.load_data()
        self.current_calls = {}
        self.target_module = None
        self.profiler_functions = set(dir(self)) | {'profileme'}
        atexit.register(self.save_data)
        
        # Initialize GPU monitoring
        try:
            pynvml.nvmlInit()
            self.num_gpus = pynvml.nvmlDeviceGetCount()
            self.gpu_handles = [pynvml.nvmlDeviceGetHandleByIndex(i) for i in range(self.num_gpus)]
        except pynvml.NVMLError:
            print("[yellow]Warning: Unable to initialize GPU monitoring.[/yellow]")
            self.num_gpus = 0
            self.gpu_handles = []

    def set_target_module(self, module_name):
        self.target_module = module_name

    def load_data(self):
        profiles = defaultdict(lambda: {'calls': 0, 'total_time': 0, 'total_cpu': 0, 'total_memory': 0, 'total_gpu': 0, 'total_io': 0})
        if os.path.exists(self.csv_file):
            with open(self.csv_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    func_key = row['Function']
                    profiles[func_key] = {
                        'calls': int(row['Calls']),
                        'total_time': float(row['Total Time']),
                        'total_cpu': float(row['Total CPU']),
                        'total_memory': float(row['Total Memory']),
                        'total_gpu': float(row['Total GPU']),
                        'total_io': float(row['Total IO']),
                    }
        return profiles

    def save_data(self):
        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['Function', 'Calls', 'Total Time', 'Total CPU', 'Total Memory', 'Total GPU', 'Total IO', 'Avg Duration', 'Avg CPU Usage', 'Avg Memory Usage', 'Avg GPU Usage', 'Avg IO Usage'])
            writer.writeheader()
            for func_key, data in self.profiles.items():
                calls = data['calls']
                avg_time = data['total_time'] / calls if calls > 0 else 0
                avg_cpu = data['total_cpu'] / calls if calls > 0 else 0
                avg_memory = data['total_memory'] / calls if calls > 0 else 0
                avg_gpu = data['total_gpu'] / calls if calls > 0 else 0
                avg_io = data['total_io'] / calls if calls > 0 else 0
                writer.writerow({
                    'Function': func_key,
                    'Calls': calls,
                    'Total Time': f"{data['total_time']:.6f}",
                    'Total CPU': f"{data['total_cpu']:.6f}",
                    'Total Memory': f"{data['total_memory'] / (1024 * 1024):.6f}",  # Convert to MB
                    'Total GPU': f"{data['total_gpu'] / (1024 * 1024):.6f}",  # Convert to MB
                    'Total IO': f"{data['total_io'] / (1024 * 1024):.6f}",  # Convert to MB
                    'Avg Duration': f"{avg_time:.6f}",
                    'Avg CPU Usage': f"{avg_cpu:.6f}",
                    'Avg Memory Usage': f"{avg_memory / (1024 * 1024):.6f}",  # Convert to MB
                    'Avg GPU Usage': f"{avg_gpu / (1024 * 1024):.6f}",  # Convert to MB
                    'Avg IO Usage': f"{avg_io / (1024 * 1024):.6f}",  # Convert to MB
                })
        print(f"[bold green]Profiling data saved to {self.csv_file}[/bold green]")
        print("[bold] mbench [/bold] is distributed by Mbodi AI under the terms of the [MIT License](LICENSE).")

    def profile(self, frame, event, arg):
        if event == 'call':
            return self._start_profile(frame)
        if event == 'return':
            self._end_profile(frame)
        return self.profile

    def _get_func_key(self, frame):
        code = frame.f_code
        return f"{code.co_name}"

    def _get_gpu_usage(self):
        total_gpu_usage = 0
        for handle in self.gpu_handles:
            try:
                info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                total_gpu_usage += info.used
            except pynvml.NVMLError:
                pass
        return total_gpu_usage

    def _get_io_usage(self):
        io = psutil.disk_io_counters()
        return io.read_bytes + io.write_bytes if io else 0

    def _start_profile(self, frame):
        if frame.f_globals.get('__name__') != self.target_module:
            return None
        func_key = self._get_func_key(frame)
        if func_key in self.profiler_functions:
            return None
        self.current_calls[func_key] = {
            'start_time': time.time(),
            'cpu_start': time.process_time(),
            'mem_start': psutil.virtual_memory().used,
            'gpu_start': self._get_gpu_usage(),
            'io_start': self._get_io_usage(),
        }
        return self.profile

    def _end_profile(self, frame):
        if frame.f_globals.get('__name__') != self.target_module:
            return
        func_key = self._get_func_key(frame)
        if func_key in self.profiler_functions:
            return
        if func_key in self.current_calls:
            start_data = self.current_calls[func_key]
            end_time = time.time()
            
            duration = end_time - start_data['start_time']
            cpu_usage = time.process_time() - start_data['cpu_start']
            mem_usage = psutil.virtual_memory().used - start_data['mem_start']
            gpu_usage = self._get_gpu_usage() - start_data['gpu_start']
            io_usage = self._get_io_usage() - start_data['io_start']
            
            # Update global mean
            self.profiles[func_key]['calls'] += 1
            self.profiles[func_key]['total_time'] += duration
            self.profiles[func_key]['total_cpu'] += cpu_usage
            self.profiles[func_key]['total_memory'] += mem_usage
            self.profiles[func_key]['total_gpu'] += gpu_usage
            self.profiles[func_key]['total_io'] += io_usage
            
            calls = self.profiles[func_key]['calls']
            avg_time = self.profiles[func_key]['total_time'] / calls
            avg_cpu = self.profiles[func_key]['total_cpu'] / calls
            avg_memory = self.profiles[func_key]['total_memory'] / calls
            avg_gpu = self.profiles[func_key]['total_gpu'] / calls
            avg_io = self.profiles[func_key]['total_io'] / calls
            
            # Print immediate profile
            print(f"[bold green]Function: {func_key}[/bold green]")
            print(f"[bold white]Duration: {duration:.6f}[/bold white] seconds")
            print(f"CPU time: {cpu_usage:.6f} seconds")
            print(f"Memory usage: [bold red]{format_bytes(mem_usage)} [/bold red]")
            print(f"GPU usage:[bold white]{format_bytes(gpu_usage)} [/bold white]")
            print(f"  I/O usage: {format_bytes(io_usage)}")
            print(f"  Avg Duration: {avg_time:.6f} seconds")
            print(f"  Avg CPU time: {avg_cpu:.6f} seconds")
            print(f"  Avg Memory usage: {format_bytes(avg_memory)}")
            print(f"  Avg GPU usage: {format_bytes(avg_gpu)}")
            print(f"  Avg I/O usage: {format_bytes(avg_io)}")
            print(f"  Total calls: {calls}")
            print("-----------------------------")
            
            del self.current_calls[func_key]

_profiler_instance = None

def profileme():
    global _profiler_instance
    if os.environ.get('MBENCH') == '1' and _profiler_instance is None:
        _profiler_instance = FunctionProfiler()
        import inspect
        caller_module = inspect.currentframe().f_back.f_globals['__name__']
        _profiler_instance.set_target_module(caller_module)
        sys.setprofile(_profiler_instance.profile)
        print(f"[bold green] Profiling started for module: {caller_module} [/bold green]")
    elif os.environ.get('MBENCH') != '1':
        print("Profiling is not active. Set MBENCH=1 to enable profiling.")


def profile(func):
    def wrapper(*args, **kwargs):
        global _profiler_instance
        if os.environ.get('MBENCH') == '1':
            if _profiler_instance is None:
                _profiler_instance = FunctionProfiler()
                caller_module = func.__module__
                _profiler_instance.set_target_module(caller_module)
                sys.setprofile(_profiler_instance.profile)
                print(f"[bold green] Profiling started for module: {caller_module} [/bold green]")
            result = func(*args, **kwargs)
            sys.setprofile(None)  # Stop profiling after the function call
            return result
        else:
            print("Profiling is not active. Set MBENCH=1 to enable profiling.")
            return func(*args, **kwargs)
    return wrapper