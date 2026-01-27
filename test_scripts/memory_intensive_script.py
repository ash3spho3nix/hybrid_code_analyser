#!/usr/bin/env python3
"""
Test script with memory-intensive operations for Scalene profiling
"""

import numpy as np

def create_large_data_structures():
    """Create large data structures that consume memory"""
    # Create large lists
    large_list = [i * 2 for i in range(100000)]
    
    # Create large dictionary
    large_dict = {f"key_{i}": f"value_{i * 100}" for i in range(50000)}
    
    # Create large numpy arrays
    large_array = np.random.rand(10000, 100)  # 10,000 x 100 array
    
    return large_list, large_dict, large_array

def process_large_data():
    """Process large amounts of data"""
    # Generate large dataset
    data = []
    for i in range(10000):
        data.append({
            'id': i,
            'name': f"Item {i}",
            'values': [j * i for j in range(100)],
            'metadata': {'created': '2023-01-01', 'updated': '2023-01-02'}
        })
    
    # Process the data
    processed_data = []
    for item in data:
        processed_item = {
            'id': item['id'],
            'name': item['name'].upper(),
            'sum': sum(item['values']),
            'average': sum(item['values']) / len(item['values'])
        }
        processed_data.append(processed_item)
    
    return processed_data

def memory_leak_simulation():
    """Simulate memory leak pattern"""
    memory_cache = []
    
    for iteration in range(100):
        # Create data that grows with each iteration
        batch_data = [f"iteration_{iteration}_item_{i}" for i in range(1000)]
        memory_cache.extend(batch_data)
        
        # Only remove half of what we add (simulating leak)
        if len(memory_cache) > 5000:
            memory_cache = memory_cache[1000:]  # Remove first 1000 items
    
    return memory_cache

def main():
    """Main function with memory-intensive operations"""
    print("Starting memory-intensive operations...")
    
    # Create large data structures
    large_list, large_dict, large_array = create_large_data_structures()
    print(f"Created large list with {len(large_list)} items")
    print(f"Created large dict with {len(large_dict)} items")
    print(f"Created large array with shape {large_array.shape}")
    
    # Process large data
    processed_data = process_large_data()
    print(f"Processed {len(processed_data)} data items")
    
    # Simulate memory leak
    memory_cache = memory_leak_simulation()
    print(f"Memory cache size: {len(memory_cache)} items")
    
    # Calculate memory usage
    total_memory = (
        len(large_list) * 28 +  # Approximate size of list items
        len(large_dict) * 100 +  # Approximate size of dict items
        large_array.nbytes +  # Numpy array memory
        len(processed_data) * 200 +  # Approximate size of processed items
        len(memory_cache) * 50  # Approximate size of cache items
    )
    
    print(f"Estimated total memory usage: {total_memory / (1024 * 1024):.2f} MB")
    print("Memory-intensive operations completed")
    
    return total_memory

if __name__ == "__main__":
    main()