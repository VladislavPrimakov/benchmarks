#include <stdio.h>
#include <stdlib.h>

#define ITERATIONS 10000000

int main() {
    int a = 42;
    double b = 3.14159;
    const char* c = "test";
    
    char buffer[256];
    long long total_length = 0;

    for (int i = 0; i < ITERATIONS; i++) {
        total_length += snprintf(buffer, sizeof(buffer), "Int: %d, Double: %.5f, String: %s", a, b, c);
    }

    printf("Total length (prevents optimization): %lld\n", total_length);

    return 0;
}
