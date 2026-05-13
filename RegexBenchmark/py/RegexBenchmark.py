import re

def main():
    # Precompile the pattern into the C engine's cache
    pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    text = "Please contact support@example.com or sales@example.org for more info."
    
    count = 0
    # The same 10 million iterations
    for _ in range(10_000_000):
        count += len(pattern.findall(text))
        
    print(f"Total matches: {count}")

if __name__ == '__main__':
    main()