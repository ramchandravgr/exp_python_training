import tracemalloc

def main():
    print("Hello from lab-1808!")
    
    return [i ** 2 for i in range(500000)]

res = get_function_memory(main)

def get_function_memory(func, *args, **kwargs):
    tracemalloc.start()

    result = func(*args, **kwargs)

    current,peak = tracemalloc.get_traced_memory()

    tracemalloc.stop()

    print(f"[{func.__name__}] Net Allocated Memory : {current / (1024 * 1024):.2f } MB")
    print(f"[{func.__name__}] Peak Memory Allocation : {peak / (1024 * 1024):.2f } MB")

    return result


if __name__ == "__main__":
    main()
