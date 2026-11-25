#include <algorithm>
#include <cmath>
#include <iostream>
#include <memory>
#include <thread>
#include <omp.h>

constexpr std::size_t kLength = 50'000'000;
constexpr int kIterations = 80;

int main() {
    auto arr = std::make_unique_for_overwrite<float[]>(kLength);
    const int threads = static_cast<int>(std::thread::hardware_concurrency());
    const std::size_t chunk_size = (kLength + threads - 1) / threads;

    #pragma omp parallel num_threads(threads)
    {
        const int t = omp_get_thread_num();
        const std::size_t start = static_cast<std::size_t>(t) * chunk_size;
        const std::size_t end = std::min(start + chunk_size, kLength);

        std::fill(arr.get() + start, arr.get() + end, 16.0f);
        #pragma omp barrier

        for (int iter = 0; iter < kIterations; ++iter) {
            #pragma omp simd
            for (std::size_t i = start; i < end; ++i) {
                arr[i] = std::sqrt(arr[i]);
            }
            #pragma omp barrier
        }
    }

    std::cout << "First: " << arr[0] << ", Last: " << arr[kLength - 1] << "\n";
    return 0;
}
