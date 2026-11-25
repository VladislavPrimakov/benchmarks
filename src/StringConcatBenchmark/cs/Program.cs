int iterations = 10_000_000;
int a = 42;
double b = 3.14159;
string cStr = "test";

long totalLength = 0;

Span<char> buffer = stackalloc char[256];

for (int i = 0; i < iterations; i++) {
    buffer.TryWrite($"Int: {a}, Double: {b:F5}, String: {cStr}", out int charsWritten);
    totalLength += charsWritten;
}

System.Console.WriteLine($"Total length (prevents optimization): {totalLength}");
