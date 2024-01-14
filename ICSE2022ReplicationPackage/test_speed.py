import time
import concurrent.futures

# Define a CPU-bound task (for example, a computation-heavy function)
def cpu_bound_task(x):
    # A simple example of a CPU-intensive calculation
    return sum(i*i for i in range(x))

def time_execution(executor_class, max_workers, tasks):
    start_time = time.time()
    with executor_class(max_workers=max_workers) as executor:
        executor.map(cpu_bound_task, tasks)
    end_time = time.time()
    return end_time - start_time

def compare_thread_vs_process_pool(num_tasks, max_workers):
    tasks = [10000] * num_tasks  # Adjust the task complexity as needed

    # Time ThreadPoolExecutor
    thread_time = time_execution(concurrent.futures.ThreadPoolExecutor, max_workers, tasks)
    print(f"ThreadPoolExecutor time: {thread_time:.2f} seconds")

    # Time ProcessPoolExecutor
    process_time = time_execution(concurrent.futures.ProcessPoolExecutor, max_workers, tasks)
    print(f"ProcessPoolExecutor time: {process_time:.2f} seconds")

if __name__ == "__main__":
    compare_thread_vs_process_pool(num_tasks=1000000, max_workers=50)
    # num_tasks=10000, max_workers=50
    # ThreadPoolExecutor time: 7.25 seconds 
    # ProcessPoolExecutor time: 9.31 seconds
    # num_tasks=1000000, max_workers=50
    # ThreadPoolExecutor time: 898.11 seconds
    # ProcessPoolExecutor time: 1122.49 seconds