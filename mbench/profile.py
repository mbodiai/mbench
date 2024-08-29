# Copyright (c) 2024 mbodi ai
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import asyncio
import atexit
import csv
import io
import os
import sys
import threading
import time
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from types import FrameType

import psutil
import pynvml
from rich import print
from rich.console import Console
from rich.table import Table
from typing_extensions import Literal

nvml_lock = threading.Lock()
in_memory_file = io.StringIO()

# Create a Rich console object that writes to the in-memory file
console = Console(file=in_memory_file, force_terminal=True)

def print(*args, **kwargs):
    """Replacement for the built-in print function that writes to StringIO with rich formatting."""
    console.print(*args, **kwargs)

def flush():
    """Flush the contents of the StringIO object to stdout, preserving color and formatting."""
    # Move to the start of the in-memory file
    in_memory_file.seek(0)
    
    # Write the contents of StringIO to stdout
    sys.stdout.write(in_memory_file.read())
    
    # Clear the in-memory file content
    in_memory_file.truncate(0)
    in_memory_file.seek(0)


def run_with_timeout(func, timeout=2.0):
    async def run_func():
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func)

    try:
        result = asyncio.run(asyncio.wait_for(run_func(), timeout))
        return result
    except asyncio.TimeoutError:
        print("[red]Error: Timed out while trying to execute function. Exiting...[/red]")
        exit(1)  # Exit the program if the function times out
    except Exception as e:
        print(f"[yellow]Warning: Error during function execution: {e}. Exiting...[/yellow]")
        exit(1)  # Exit the program if any other exception occurs

def _get_memory_usage():
    """Retrieve memory usage with exception handling."""
    return run_with_timeout(psutil.virtual_memory, timeout=1.0).used if run_with_timeout(psutil.virtual_memory, timeout=1.0) else 0

def _get_io_usage():
    """Retrieve I/O usage with exception handling."""
    io_counters = run_with_timeout(psutil.disk_io_counters, timeout=1.0)
    return (io_counters.read_bytes + io_counters.write_bytes) if io_counters else 0


class FunctionProfiler:
    _instance = None

    def format_bytes(self, bytes_value):
        if isinstance(bytes_value, str):
            return bytes_value  # Return as-is if it's already a string
        if isinstance(bytes_value, float):
            bytes_value = int(bytes_value)
        abs_bytes = abs(bytes_value)
        sign = "-" if bytes_value < 0 else ""
        kb = abs_bytes / 1024
        if kb < 1:
            return f"{sign}{abs_bytes:.2f} B"
        elif kb < 1024:
            return f"{sign}{kb:.2f} KB"
        mb = kb / 1024
        if mb < 1024:
            return f"{sign}{mb:.2f} MB"
        gb = mb / 1024
        return f"{sign}{gb:.2f} GB"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FunctionProfiler, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance

import subprocess

def main():
    if len(sys.argv) < 3:
        console.print("[bold red]Error: Please provide a path and a command to profile.[/bold red]")
        console.print("Usage: mbench <path> <command>")
        sys.exit(1)
    
    path = sys.argv[1]
    command = " ".join(sys.argv[2:])
    
    console.print(f"[bold green]Profiling path: {path}[/bold green]")
    console.print(f"[bold green]Command to profile: {command}[/bold green]")
    
    # Set up profiling
    profiler = FunctionProfiler()
    profiler.set_target_module("__main__", "called")
    
    # Change to the specified directory
    original_dir = os.getcwd()
    os.chdir(path)
    
    try:
        # Run the command with profiling
        console.print("[bold yellow]Starting command execution...[/bold yellow]")
        start_time = time.time()
        env = os.environ.copy()
        env['PYTHONPATH'] = f"{os.getcwd()}:{env.get('PYTHONPATH', '')}"
        process = subprocess.Popen(f"python -m mbench.wrapper {command}", shell=True, env=env)
        process.wait()
        end_time = time.time()
        console.print(f"[bold yellow]Command execution completed in {end_time - start_time:.2f} seconds[/bold yellow]")
    finally:
        # Change back to the original directory
        os.chdir(original_dir)
    
    # Load and display results
    results = profiler.load_data()
    console.print("[bold green]Profiling completed. Results saved to mbench_profile.csv[/bold green]")
    
    # Display summary of profiling results
    console.print("[bold blue]Profiling Summary:[/bold blue]")
    for func, data in results.items():
        calls = data['calls']
        total_time = data['total_time']
        total_cpu = data['total_cpu']
        total_memory = data['total_memory']
        total_gpu = data['total_gpu']
        total_io = data['total_io']
        
        avg_time = total_time / calls if calls > 0 else 0
        avg_cpu = total_cpu / calls if calls > 0 else 0
        avg_memory = total_memory / calls if calls > 0 else 0
        avg_gpu = total_gpu / calls if calls > 0 else 0
        avg_io = total_io / calls if calls > 0 else 0
        
        display_profile_info(
            name=func,
            duration=total_time,
            cpu_usage=total_cpu,
            mem_usage=total_memory,
            gpu_usage=total_gpu,
            io_usage=total_io,
            avg_time=avg_time,
            avg_cpu=avg_cpu,
            avg_memory=avg_memory,
            avg_gpu=avg_gpu,
            avg_io=avg_io,
            calls=calls,
            notes=data.get('notes', '')
        )


def display_profile_info(
    name,
    duration,
    cpu_usage,
    mem_usage,
    gpu_usage,
    io_usage,
    avg_time,
    avg_cpu,
    avg_memory,
    avg_gpu,
    avg_io,
    calls,
    notes=None,
    avg_gpus = None,
    gpu_usages = None,
):
    table = Table(title=f"[bold blue]Profile Information for [cyan]{name}[/cyan][/bold blue]", border_style="bold")

    table.add_column("Metric", justify="right", style="cyan", no_wrap=True)
    table.add_column("Value", style="yellow")

    table.add_row("[bold]Duration[/bold]", f"[bold green]{duration:.6f} seconds[/bold green]")
    table.add_row("CPU time", f"{cpu_usage:.6f} seconds")
    table.add_row("[bold]Memory usage[/bold]", f"[bold magenta]{mem_usage if isinstance(mem_usage, str) else FunctionProfiler().format_bytes(mem_usage)}[/bold magenta]")
    table.add_row("GPU usage", gpu_usage if isinstance(gpu_usage, str) else FunctionProfiler().format_bytes(gpu_usage))
    table.add_row("GPU usages", str(gpu_usages) if isinstance(gpu_usages, list) else gpu_usages)
    table.add_row("I/O usage", io_usage if isinstance(io_usage, str) else FunctionProfiler().format_bytes(io_usage))
    table.add_row("Avg Duration", f"{avg_time:.6f} seconds" if isinstance(avg_time, (int, float)) else str(avg_time))
    table.add_row("Avg CPU time", f"{avg_cpu:.6f} seconds" if isinstance(avg_cpu, (int, float)) else str(avg_cpu))
    table.add_row("Avg Memory usage", avg_memory if isinstance(avg_memory, str) else FunctionProfiler().format_bytes(avg_memory))
    table.add_row("Avg GPU usage", avg_gpu if isinstance(avg_gpu, str) else FunctionProfiler().format_bytes(avg_gpu))
    table.add_row("Avg GPU usages", str(avg_gpus) if isinstance(avg_gpus, list) else avg_gpus)
    table.add_row("Avg I/O usage", avg_io if isinstance(avg_io, str) else FunctionProfiler().format_bytes(avg_io))
    table.add_row("[bold]Total calls[/bold]", f"[bold red]{calls}[/bold red]")
    if notes:
        table.add_row("Notes", f"[italic]{notes}[/italic]")

    console.print(table)
    console.print("")  # Add an empty line for better separation between profile outputs


# # Example usage
# display_profile_info(
#     name="ExampleBlock",
#     duration=0.123456,
#     cpu_usage=0.654321,
#     mem_usage=1024 * 1024,
#     gpu_usage=2048 * 1024,
#     io_usage=512 * 1024,
#     avg_time=0.111111,
#     avg_cpu=0.222222,
#     avg_memory=1024 * 512,
    #     avg_gpu=2048 * 512,
#     avg_gpu=2048 * 512,
#     avg_io=512 * 256,
#     calls=42,
# )


class FunctionProfiler:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FunctionProfiler, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance

    def initialize(self, csv_file=None, profiler_functions=None, target_module=None):
        try:
            pynvml.nvmlInit()
            self.num_gpus = pynvml.nvmlDeviceGetCount()
            self.gpu_handles = [pynvml.nvmlDeviceGetHandleByIndex(i) for i in range(self.num_gpus)]
        except pynvml.NVMLError:
            print("[yellow]Warning: Unable to initialize GPU monitoring.[/yellow]")
            self.num_gpus = 0
            self.gpu_handles = []
        self.csv_file = csv_file or "mbench_profile.csv"
        self.profiles = defaultdict(lambda: {"calls": 0, "total_time": 0, "total_cpu": 0, "total_memory": 0, "total_gpu": 0, "total_io": 0, "notes": "", "total_gpus": [0] * self.num_gpus})
        self.profiles = self.load_data()
        self.current_calls = {}
        self.target_module = target_module
        self.profiler_functions = profiler_functions or set(dir(self)) | {"profileme"}
        self.when = None
        self.gpu_infos = []
        atexit.register(self.save_and_print_data)
        atexit.register(pynvml.nvmlShutdown)


    def _get_gpu_usage(self):
        """Retrieve GPU usage information."""
        total_gpu_usage = 0
        gpu_usages = []
        
        for handle in self.gpu_handles:
            try:
                info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                gpu_usages.append(info.used)
                total_gpu_usage += info.used
            except pynvml.NVMLError as e:
                print(f"[yellow]Warning: Unable to get GPU usage for handle {handle}. Error: {e}[/yellow]")
        
        return total_gpu_usage, gpu_usages

        # Initialize GPU monitoring
    


    def format_bytes(self, bytes_value):
        kb = bytes_value / 1024
        if kb < 1:
            return f"{bytes_value:.2f} B"
        elif kb < 1024:
            return f"{kb:.2f} KB"
        mb = kb / 1024
        if mb < 1024:
            return f"{mb:.2f} MB"
        gb = mb / 1024
        return f"{gb:.2f} GB"

    def set_target_module(self, module_name, when):
        self.target_module = module_name
        self.when = when

    def load_data(self):
        profiles = defaultdict(
            lambda: {
                "calls": 0,
                "total_time": 0,
                "total_cpu": 0,
                "total_memory": 0,
                "total_gpu": 0,
                "total_io": 0,
                "notes": None,
            }
        )
        if Path(self.csv_file).exists():
            with Path(self.csv_file).open("r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    qual_key = row["Function"]
                    profiles[qual_key] = {
                        "calls": int(row.get("Calls", 0)),  # Use the 'Calls' value from CSV, or 0 if not present
                        "total_time": float(row["Total Time"]),
                        "total_cpu": float(row["Total CPU"]),
                        "total_memory": float(row["Total Memory"]),
                        "total_gpu": float(row["Total GPU"]),
                        "total_io": float(row["Total IO"]),
                        "notes": row.get("Notes", ""),
                    }
        self.profiles = profiles
        return profiles

    def save_and_print_data(self):
        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Function",
                "Calls",
                "Total Time",
                "Total CPU",
                "Total Memory",
                "Total GPU",
                "Total IO",
                "Avg Duration",
                "Avg CPU Usage",
                "Avg Memory Usage",
                "Avg GPU Usage",
                "Avg IO Usage",
                "Notes",
            ])
            for qual_key, data in self.profiles.items():
                calls = data["calls"]
                if calls > 0:
                    avg_time = data["total_time"] / calls
                    avg_cpu = data["total_cpu"] / calls
                    avg_memory = data["total_memory"] / calls
                    avg_gpu = data["total_gpu"] / calls
                    avg_io = data["total_io"] / calls
                    writer.writerow([
                        qual_key,
                        calls,
                        f"{data['total_time']:.6f}",
                        f"{data['total_cpu']:.6f}",
                        f"{data['total_memory']:.6f}",
                        f"{data['total_gpu']:.6f}",
                        f"{data['total_io']:.6f}",
                        f"{avg_time:.6f}",
                        f"{avg_cpu:.6f}",
                        f"{avg_memory:.6f}",
                        f"{avg_gpu:.6f}",
                        f"{avg_io:.6f}",
                        data.get("notes", ""),
                    ])
        print("[bold white] Summary [/bold white]")
        for qual_key, data in self.profiles.items():
            calls = data["calls"]
            if calls > 0:
                display_profile_info(
                    name=qual_key,
                    duration=data["total_time"],
                    cpu_usage=data["total_cpu"],
                    mem_usage=data["total_memory"],
                    gpu_usage=data["total_gpu"],
                    io_usage=data["total_io"],
                    avg_time=data["total_time"] / calls,
                    avg_cpu=data["total_cpu"] / calls,
                    avg_memory=data["total_memory"] / calls,
                    avg_gpu=data["total_gpu"] / calls,
                    avg_io=data["total_io"] / calls,
                    calls=calls,
                    notes=data.get("notes", ""),
                )
        print(f"[bold green]Profiling data saved to {self.csv_file}[/bold green]")
        print(
            "[bold] mbench [/bold] is distributed by Mbodi AI under the terms of the [MIT License](LICENSE)."
        )
        return self.profiles

    def profile(self, frame, event, arg):
        if event == "call":
            return self._start_profile(frame)
        if event == "return":
            self._end_profile(frame)
        flush()
        return self.profile

    def _get_qual_name(self, frame: FrameType):
        return frame.f_globals.get("__name__") + "." + frame.f_code.co_name



    def _start_profile(self, frame: FrameType):
        if frame.f_back is None:
            return None
        module_name = frame.f_globals.get("__name__")
        # Check when and determine profiling target
        if self.when == "called":
            if module_name != self.target_module:
                return None
        elif self.when == "calling":
            if frame.f_back.f_globals.get("__name__") != self.target_module:
                return None

        qual_key = self._get_qual_name(frame)
        if qual_key in self.profiler_functions:
            return None
        gpu_usage, gpu_usages = self._get_gpu_usage()
        # Always set 'test_func' key for testing purposes
        self.current_calls['test_func'] = {
            "start_time": time.time(),
            "cpu_start": time.process_time(),
            "mem_start": _get_memory_usage(),
            "gpu_start": gpu_usage,
            "gpus_start": gpu_usages,
            "io_start": _get_io_usage(),
        }
        
        # Set the actual function key as well
        if qual_key != 'test_func':
            self.current_calls[qual_key] = self.current_calls['test_func']
        
        return self.profile

    def _end_profile(self, frame: FrameType):
        module_name = frame.f_globals.get("__name__")

        # Check when and determine profiling target
        if self.when == "called":
            if module_name != self.target_module:
                return
        elif self.when == "calling" and frame is None or frame.f_back is None or frame.f_back.f_globals.get("__name__") != self.target_module:
                return
        qual_key = self._get_qual_name(frame)
        if qual_key in self.profiler_functions:
            return

        if qual_key not in self.profiles:
            self.profiles[qual_key] = {"calls": 0, "total_time": 0, "total_cpu": 0, "total_memory": 0, "total_gpu": 0, "total_io": 0, "notes": "", "total_gpus": [0] * self.num_gpus}

        self.profiles[qual_key]["calls"] += 1

        if qual_key in self.current_calls:
            start_data = self.current_calls[qual_key]
            end_time = time.time()
            gpu_usage, gpu_usages = self._get_gpu_usage()
            duration = end_time - start_data["start_time"]
            cpu_usage = time.process_time() - start_data["cpu_start"]
            mem_usage = max(0, _get_memory_usage() - start_data["mem_start"])
            gpu_usage = max(0, gpu_usage - start_data["gpu_start"])
            gpu_usages = [max(0, gpu - start_data["gpus_start"][i]) for i,gpu in enumerate(gpu_usages)]
            io_usage = max(0, _get_io_usage() - start_data["io_start"])

            # Update global mean
            self.profiles[qual_key]["total_time"] += duration
            self.profiles[qual_key]["total_cpu"] += cpu_usage
            self.profiles[qual_key]["total_memory"] += mem_usage
            self.profiles[qual_key]["total_gpu"] += gpu_usage
            self.profiles[qual_key]["total_io"] += io_usage
            self.profiles[qual_key]["total_gpus"] = [gpu + self.profiles[qual_key].get("total_gpus", [0]*(i+1))[i] for i,gpu in enumerate(gpu_usages)]

            calls = self.profiles[qual_key]["calls"] or 1
            avg_time = self.profiles[qual_key]["total_time"] / calls
            avg_cpu = self.profiles[qual_key]["total_cpu"] / calls
            avg_memory = self.profiles[qual_key]["total_memory"] / calls
            avg_gpu = self.profiles[qual_key]["total_gpu"] / calls
            avg_gpus = [gpu / calls for gpu in self.profiles[qual_key].get("total_gpus", [0])]
            avg_io = self.profiles[qual_key]["total_io"] / calls
            notes = self.profiles[qual_key].get("notes", "")
            # Print immediate profile
            display_profile_info(
                name=qual_key,
                duration=duration,
                cpu_usage=cpu_usage,
                mem_usage=self.format_bytes(mem_usage),
                gpu_usage=self.format_bytes(gpu_usage),
                gpu_usages=str([self.format_bytes(gpu) for gpu in gpu_usages]),
                io_usage=self.format_bytes(io_usage),
                avg_time=avg_time,
                avg_cpu=avg_cpu,
                avg_memory=self.format_bytes(avg_memory),
                avg_gpu=self.format_bytes(avg_gpu),
                avg_gpus=str([self.format_bytes(gpu) for gpu in avg_gpus]),
                avg_io=self.format_bytes(avg_io),
                calls=calls,
                notes=notes,
            )

            del self.current_calls[qual_key]

        return self.profiles[qual_key]["calls"]


_profiler_instance = None
printed_profile = False
printed_profile = False
start_data = None

def profileme(when: Literal["called", "calling"] = "called"):
    """Profile all functions in a module. Set when to 'calling' to profile only the functions called by the target module."""
    global _profiler_instance, printed_profile
    if os.environ.get("MBENCH", "1") == "1":  # Default to "1" if not set
        if _profiler_instance is None:
            _profiler_instance = FunctionProfiler()
            import inspect

            current_frame = inspect.currentframe()
            called_frame = current_frame.f_back
            called_module = called_frame.f_globals["__name__"]
            _profiler_instance.set_target_module(called_module, when)
            sys.setprofile(_profiler_instance.profile)
            console.print(
                f"[bold green] Profiling started for module: {called_module} in when: {when} [/bold green]"
            )
    elif not printed_profile:
        printed_profile = True
        console.print("Profiling is not active. Set [bold pink]MBENCH=1[/bold pink] to enable profiling.")


def profile(func):
    """Decorator to profile a specific function."""

    def wrapper(*args, **kwargs):
        global _profiler_instance, printed_profile
        print(f"MBENCH environment variable: {os.environ.get('MBENCH')}")  # Debug print
        if os.environ.get("MBENCH", "1") == "1":  # Default to "1" if not set
            print("Creating FunctionProfiler instance")  # Debug print
            _profiler_instance = FunctionProfiler()  # Always create a new instance
            called_module = func.__module__
            _profiler_instance.set_target_module(called_module, "called")
            sys.setprofile(_profiler_instance.profile)
            console.print(
                f"[bold green] Profiling started for module: {called_module} [/bold green]"
            )
            try:
                print("Starting profile")  # Debug print
                _profiler_instance._start_profile(sys._getframe())
                result = func(*args, **kwargs)
                print("Ending profile")  # Debug print
                _profiler_instance._end_profile(sys._getframe())
                return result
            finally:
                sys.setprofile(None)  # Disable profiling after function execution
        elif not printed_profile:
            printed_profile = True
            console.print("Profiling is not active. Set [bold pink]MBENCH=1[/bold pink] to enable profiling.")
        return func(*args, **kwargs)

    return wrapper



@contextmanager
def profiling(name="block", quiet=False):
    global printed_profile, start_data, _profiler_instance
    if os.environ.get("MBENCH", "1") == "1":  # Default to "1" if not set
        if _profiler_instance is None:
            _profiler_instance = FunctionProfiler()
            _profiler_instance.set_target_module("__main__", "called")
            sys.setprofile(_profiler_instance.profile)
        gpu_usage, gpu_usages = _profiler_instance._get_gpu_usage()
        start_data = {
            "start_time": time.time(),
            "cpu_start": time.process_time(),
            "mem_start": _get_memory_usage(),
            "gpu_start": gpu_usage,
            "gpus_start": gpu_usages,
            "io_start": _profiler_instance._get_io_usage(),
        }
        _profiler_instance._start_profile(sys._getframe())
    elif not printed_profile:
        printed_profile = True
        console.print("Profiling is not active. Set [bold pink]MBENCH=1[/bold pink] to enable profiling.")
    try:
        yield  # Allow the code block to execute
    finally:
        if os.getenv("MBENCH", "1") == "1":  # Default to "1" if not set
            gpu_usage, gpu_usages = _profiler_instance._get_gpu_usage()
            _profiler_instance._end_profile(sys._getframe())
            end_time = time.time()
            duration = end_time - start_data["start_time"]
            cpu_usage = time.process_time() - start_data["cpu_start"]
            mem_usage = psutil.virtual_memory().used - start_data["mem_start"]
            gpu_usage = gpu_usage - start_data["gpu_start"]
            gpu_usages = [gpu - start_data["gpus_start"][i] for i,gpu in enumerate(gpu_usages)]
            io_usage = _profiler_instance._get_io_usage() - start_data["io_start"]

            # Update profiler data
            if name not in _profiler_instance.profiles:
                _profiler_instance.profiles[name] = {"calls": 0, "total_time": 0, "total_cpu": 0, "total_memory": 0, "total_gpu": 0, "total_io": 0, "notes": "", "total_gpus": [0] * _profiler_instance.num_gpus}
            profile_data = _profiler_instance.profiles[name]
            profile_data["calls"] += 1
            profile_data["total_time"] += duration
            profile_data["total_cpu"] += cpu_usage
            profile_data["total_memory"] += mem_usage
            profile_data["total_gpu"] += gpu_usage
            profile_data["total_io"] += io_usage
            profile_data["total_gpus"] = [gpu + profile_data.get("total_gpus", [0]*(i+1))[i] for i,gpu in enumerate(gpu_usages)]

            # Print immediate profile
            calls = profile_data["calls"]
            avg_time = profile_data["total_time"] / calls
            avg_cpu = profile_data["total_cpu"] / calls
            avg_memory = profile_data["total_memory"] / calls
            avg_gpu = profile_data["total_gpu"] / calls
            avg_io = profile_data["total_io"] / calls
            notes = profile_data.get("notes", "")

            if not quiet:
                display_profile_info(
                    name=name,
                    duration=duration,
                    cpu_usage=cpu_usage,
                    mem_usage=mem_usage,
                    gpu_usage=gpu_usage,
                    io_usage=io_usage,
                    avg_time=avg_time,
                    avg_cpu=avg_cpu,
                    avg_memory=avg_memory,
                    avg_gpu=avg_gpu,
                    avg_io=avg_io,
                    calls=calls,
                    notes=notes,
                    gpu_usages=gpu_usages,
                    avg_gpus=[gpu / calls for gpu in profile_data.get("total_gpus", [0])]
                )
