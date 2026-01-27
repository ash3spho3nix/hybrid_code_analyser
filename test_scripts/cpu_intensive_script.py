#!/usr/bin/env python3
"""
Test script with CPU-intensive operations for Scalene profiling
"""

def cpu_intensive_calculation():
    """Perform CPU-intensive calculations"""
    result = 0
    for i in range(1000000):
        result += i * i
        if i % 10000 == 0:
            # Add some branching logic
            if result > 1000000000:
                result = result // 2
    return result

def fibonacci(n):
    """Calculate Fibonacci sequence recursively"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def main():
    """Main function with CPU-intensive operations"""
    print("Starting CPU-intensive operations...")
    
    # CPU-intensive calculation
    cpu_result = cpu_intensive_calculation()
    print(f"CPU calculation result: {cpu_result}")
    
    # Recursive Fibonacci (CPU-intensive)
    fib_result = fibonacci(30)
    print(f"Fibonacci(30): {fib_result}")
    
    # String operations
    long_string = "Hello, World! " * 10000
    processed_string = long_string.upper()
    print(f"String length: {len(processed_string)}")
    
    print("CPU-intensive operations completed")
    return cpu_result + fib_result

if __name__ == "__main__":
    main()