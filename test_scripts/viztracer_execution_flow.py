#!/usr/bin/env python3
"""
Test script for VizTracer execution flow tracing
This script tests VizTracer's ability to trace complex execution flows
"""

class TestClass:
    """Test class for execution flow tracing"""
    
    def __init__(self):
        self.value = 42
    
    def method_a(self):
        """Method A"""
        return self.value * 2
    
    def method_b(self, multiplier):
        """Method B"""
        return self.method_a() * multiplier
    
    def method_c(self):
        """Method C that calls other methods"""
        result_a = self.method_a()
        result_b = self.method_b(3)
        return result_a + result_b

def complex_execution_flow():
    """Function with complex execution flow"""
    
    # Create object
    obj = TestClass()
    
    # Call methods in sequence
    result1 = obj.method_a()
    result2 = obj.method_b(5)
    result3 = obj.method_c()
    
    # Nested function calls
    def nested_function():
        return obj.method_a() + obj.method_b(2)
    
    result4 = nested_function()
    
    return result1 + result2 + result3 + result4

def conditional_execution_flow(condition):
    """Function with conditional execution flow"""
    
    if condition:
        return "Condition was true"
    else:
        return "Condition was false"

def loop_execution_flow(iterations):
    """Function with loop execution flow"""
    
    total = 0
    for i in range(iterations):
        total += i
        if i % 2 == 0:
            total *= 2
    
    return total

def main():
    """Main function"""
    print("Starting VizTracer execution flow tracing test...")
    
    # Test different execution flow patterns
    complex_execution_flow()
    conditional_execution_flow(True)
    conditional_execution_flow(False)
    loop_execution_flow(10)
    
    print("VizTracer execution flow tracing test completed")
    return "success"

if __name__ == "__main__":
    main()