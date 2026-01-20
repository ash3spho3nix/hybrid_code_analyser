"""
Sample Python file for testing Hybrid Code Analyzer CLI
"""

def calculate_factorial(n):
    """Calculate factorial of a number"""
    if n == 0:
        return 1
    else:
        return n * calculate_factorial(n - 1)

def find_prime_numbers(limit):
    """Find prime numbers up to a given limit"""
    primes = []
    for num in range(2, limit + 1):
        is_prime = True
        for i in range(2, int(num ** 0.5) + 1):
            if num % i == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(num)
    return primes

def process_data(data):
    """Process some data"""
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
        else:
            result.append(0)
    return result

# Main execution
if __name__ == "__main__":
    print("Testing factorial calculation:")
    print(f"5! = {calculate_factorial(5)}")
    
    print("\nTesting prime numbers:")
    primes = find_prime_numbers(20)
    print(f"Primes up to 20: {primes}")
    
    print("\nTesting data processing:")
    data = [1, -2, 3, 0, 5]
    processed = process_data(data)
    print(f"Processed data: {processed}")