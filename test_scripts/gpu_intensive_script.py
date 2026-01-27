#!/usr/bin/env python3
"""
Test script with GPU-intensive operations for Scalene profiling
Note: This script requires CUDA and compatible GPU to run GPU operations
"""

try:
    import cupy as cp
    import numpy as np
    CUDA_AVAILABLE = True
except ImportError:
    CUDA_AVAILABLE = False
    print("CUDA/cupy not available, using CPU fallback")

def gpu_matrix_operations():
    """Perform matrix operations on GPU"""
    if CUDA_AVAILABLE:
        # Create large matrices on GPU
        matrix_a = cp.random.rand(1000, 1000)
        matrix_b = cp.random.rand(1000, 1000)
        
        # Perform matrix multiplication
        result = cp.dot(matrix_a, matrix_b)
        
        # Perform element-wise operations
        result_squared = result ** 2
        result_sum = cp.sum(result_squared)
        
        return result_sum
    else:
        # CPU fallback
        matrix_a = np.random.rand(1000, 1000)
        matrix_b = np.random.rand(1000, 1000)
        
        result = np.dot(matrix_a, matrix_b)
        result_squared = result ** 2
        result_sum = np.sum(result_squared)
        
        return result_sum

def gpu_vector_operations():
    """Perform vector operations on GPU"""
    if CUDA_AVAILABLE:
        # Create large vectors on GPU
        vector_a = cp.random.rand(1000000)
        vector_b = cp.random.rand(1000000)
        
        # Perform vector operations
        result = vector_a * vector_b
        sum_result = cp.sum(result)
        mean_result = cp.mean(result)
        
        return sum_result, mean_result
    else:
        # CPU fallback
        vector_a = np.random.rand(1000000)
        vector_b = np.random.rand(1000000)
        
        result = vector_a * vector_b
        sum_result = np.sum(result)
        mean_result = np.mean(result)
        
        return sum_result, mean_result

def gpu_memory_intensive():
    """Perform memory-intensive operations on GPU"""
    if CUDA_AVAILABLE:
        # Create multiple large arrays
        arrays = []
        for i in range(10):
            array = cp.random.rand(5000, 5000)  # Large 2D array
            arrays.append(array)
        
        # Perform operations on all arrays
        total_sum = 0
        for array in arrays:
            array_sum = cp.sum(array)
            total_sum += array_sum
        
        return total_sum
    else:
        # CPU fallback
        arrays = []
        for i in range(5):  # Reduced size for CPU
            array = np.random.rand(1000, 1000)
            arrays.append(array)
        
        total_sum = 0
        for array in arrays:
            array_sum = np.sum(array)
            total_sum += array_sum
        
        return total_sum

def main():
    """Main function with GPU-intensive operations"""
    print("Starting GPU-intensive operations...")
    print(f"CUDA available: {CUDA_AVAILABLE}")
    
    # GPU matrix operations
    matrix_result = gpu_matrix_operations()
    print(f"Matrix operations result: {matrix_result}")
    
    # GPU vector operations
    vector_sum, vector_mean = gpu_vector_operations()
    print(f"Vector operations - sum: {vector_sum}, mean: {vector_mean}")
    
    # GPU memory-intensive operations
    memory_result = gpu_memory_intensive()
    print(f"Memory-intensive operations result: {memory_result}")
    
    print("GPU-intensive operations completed")
    
    return matrix_result + vector_sum + memory_result

if __name__ == "__main__":
    main()