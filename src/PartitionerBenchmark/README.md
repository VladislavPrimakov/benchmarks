# PartitionerBenchmark: Source Code, Assembly & Results

Benchmark of parallel SIMD `sqrt` calculation over an array of `50,000,000` `float` elements (~200 MiB, exceeding L3 cache) over `80` iterations with parallel first-touch initialization and equal per-core static chunking across **C++ (OpenMP + `simd`)**, **Rust (`rayon` `par_chunks_mut`)**, and **C# (`Partitioner` + `Span<T>` + `Vector<float>`)**.

---

## 1. Source Code

### C++ (`src/PartitionerBenchmark/cpp/PartitionerBenchmark.cpp`)
Compiled with:
```bash
g++ -O3 -march=native -flto=auto -std=c++20 -fno-math-errno -fopenmp src/PartitionerBenchmark/cpp/PartitionerBenchmark.cpp -o src/PartitionerBenchmark/cpp/partitioner_benchmark_cpp
```

```cpp
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
```

---

### Rust (`src/PartitionerBenchmark/rust/src/main.rs`)
Compiled with:
```bash
RUSTFLAGS="-C target-cpu=native" cargo build --release --manifest-path src/PartitionerBenchmark/rust/Cargo.toml
```

```rust
use std::mem::MaybeUninit;
use rayon::prelude::*;

const LENGTH: usize = 50_000_000;
const ITERATIONS: usize = 80;

fn main() {
    let mut arr: Vec<f32> = Vec::with_capacity(LENGTH);
    let chunk_size = LENGTH.div_ceil(rayon::current_num_threads());

    arr.spare_capacity_mut()[..LENGTH]
        .par_chunks_mut(chunk_size)
        .for_each(|chunk| {
            chunk.fill(MaybeUninit::new(16.0_f32));
        });

    // SAFETY: Every element in 0..LENGTH was initialized above.
    unsafe {
        arr.set_len(LENGTH);
    }

    for _ in 0..ITERATIONS {
        arr.par_chunks_mut(chunk_size).for_each(|chunk| {
            for x in chunk {
                *x = x.sqrt();
            }
        });
    }

    println!("First: {}, Last: {}", arr[0], arr[arr.len() - 1]);
}
```

---

### C# (`src/PartitionerBenchmark/cs/Program.cs`)
Compiled with:
```bash
# JIT
dotnet build -c Release -o src/PartitionerBenchmark/cs/bin/Release/jit /p:TargetFramework=net11.0 src/PartitionerBenchmark/cs/PartitionerBenchmark.csproj

# NativeAOT
dotnet publish -c Release -r linux-x64 -o src/PartitionerBenchmark/cs/bin/Release/aot /p:PublishAot=true /p:IlcInstructionSet=native /p:OptimizationPreference=Speed /p:TargetFramework=net11.0 src/PartitionerBenchmark/cs/PartitionerBenchmark.csproj
```

```csharp
using System;
using System.Collections.Concurrent;
using System.Numerics;
using System.Runtime.InteropServices;
using System.Threading.Tasks;

const int Length = 50_000_000;
const int Iterations = 80;

float[] arr = GC.AllocateUninitializedArray<float>(Length);

int threads = Environment.ProcessorCount;
int chunkSize = (arr.Length + threads - 1) / threads;
var partitioner = Partitioner.Create(0, arr.Length, chunkSize);

Parallel.ForEach(partitioner, range =>
{
    arr.AsSpan(range.Item1, range.Item2 - range.Item1).Fill(16.0f);
});

for (int iter = 0; iter < Iterations; iter++)
{
    Parallel.ForEach(partitioner, range =>
    {
        Span<float> slice = arr.AsSpan(range.Item1, range.Item2 - range.Item1);

        Span<Vector<float>> vectors = MemoryMarshal.Cast<float, Vector<float>>(slice);

        for (int i = 0; i < vectors.Length; i++)
        {
            vectors[i] = Vector.SquareRoot(vectors[i]);
        }

        int remainderStart = vectors.Length * Vector<float>.Count;
        for (int i = remainderStart; i < slice.Length; i++)
        {
            slice[i] = MathF.Sqrt(slice[i]);
        }
    });
}

Console.WriteLine($"First: {arr[0]}, Last: {arr[^1]}");
```

---

## 2. Generated Assembly (Hot Loop, Intel Syntax)

### C++ (`g++ 14.2.0`, `-O3 -march=native -flto=auto -fno-math-errno -fopenmp`)
> **Note:** Without `-fno-math-errno`, `g++` refuses to emit 256-bit `vsqrtps` because standard C/C++ requires `std::sqrt` to set `errno = EDOM` on negative inputs (`call sqrtf@plt`). With `-fno-math-errno` and `#pragma omp simd`, `g++` vectorizes the OpenMP chunk loop into 256-bit AVX (`ymm0`) + 128-bit SSE (`xmm0`) + scalar (`xmm0`) tail handling inside `main._omp_fn.0`:

```asm
; Main 256-bit AVX loop (8 floats = 32 bytes per iteration)
1560:   c5 fc 51 00             vsqrtps ymm0, YMMWORD PTR [rax]
1564:   48 83 c0 20             add     rax, 0x20
1568:   c5 fc 11 40 e0          vmovups YMMWORD PTR [rax-0x20], ymm0
156d:   48 39 c2                cmp     rdx, rax
1570:   75 ee                   jne     1560

; Remainder check & 128-bit SSE epilogue (4 floats)
157a:   f6 44 24 18 07          test    BYTE PTR [rsp+0x18], 0x7
157f:   0f 84 9b 00 00 00       je      1620
1585:   c5 f8 77                vzeroupper
...
15a1:   c5 f8 51 02             vsqrtps xmm0, XMMWORD PTR [rdx]
15a5:   c5 f8 11 02             vmovups XMMWORD PTR [rdx], xmm0
...
; Scalar tail (vsqrtss)
15c8:   c5 f2 51 06             vsqrtss xmm0, xmm1, DWORD PTR [rsi]
15cc:   c5 fa 11 06             vmovss  DWORD PTR [rsi], xmm0
```

---

### Rust (`rustc`, `opt-level = 3`, `lto = true`, `target-cpu=native`)
> **Note:** LLVM auto-vectorizes `for x in chunk { *x = x.sqrt(); }` and unrolls the inner loop **4x** using four 256-bit registers (`ymm0`–`ymm3`), processing **32 `float` elements (128 bytes)** per branch, followed by a 128-bit (`xmm0`) cleanup loop and scalar tail:

```asm
; Main 4x-unrolled 256-bit AVX loop (32 floats = 128 bytes per iteration)
vsqrtps ymm0, YMMWORD PTR [r8+rdi*4]
vsqrtps ymm1, YMMWORD PTR [r8+rdi*4+0x20]
vsqrtps ymm2, YMMWORD PTR [r8+rdi*4+0x40]
vsqrtps ymm3, YMMWORD PTR [r8+rdi*4+0x60]
vmovups YMMWORD PTR [r8+rdi*4], ymm0
vmovups YMMWORD PTR [r8+rdi*4+0x20], ymm1
vmovups YMMWORD PTR [r8+rdi*4+0x40], ymm2
vmovups YMMWORD PTR [r8+rdi*4+0x60], ymm3
add     rdi, 0x20
cmp     rsi, rdi
jne     <loop>

; 128-bit SSE cleanup loop (4 floats = 16 bytes per iteration)
vsqrtps xmm0, XMMWORD PTR [r8+rsi*4]
vmovups XMMWORD PTR [r8+rsi*4], xmm0
add     rsi, 0x4
cmp     rdx, rsi
jne     <sse_loop>
```

---

### C# (NativeAOT / RyuJIT, `IlcInstructionSet=native`)
> **Note:** RyuJIT hoists all `Span<T>` bounds checks outside the hot loop and emits a clean 256-bit `vsqrtps ymm0` loop (8 floats = 32 bytes per iteration), followed by the scalar `vsqrtss` remainder loop:

```asm
; Main 256-bit AVX loop (8 floats = 32 bytes per iteration, zero bounds checks)
vsqrtps ymm0, YMMWORD PTR [rax+rdx*1]
vmovups YMMWORD PTR [rax+rdx*1], ymm0
add     rdx, 0x20
dec     esi
jne     <loop>

; Scalar remainder loop (MathF.Sqrt)
vsqrtss xmm0, xmm0, DWORD PTR [rax+rdx*4]
vmovss  DWORD PTR [rax+rdx*4], xmm0
inc     ecx
cmp     ecx, edi
jl      <tail_loop>
vzeroupper
```

---

## 3. Benchmark Results (`hyperfine --warmup 3`)

See the live, auto-updated table in the root [README.md](../../README.md#2-partitionerbenchmark-parallel-simd-squareroot):

| Language | Version | Wall [ms] | Min..Max [ms] | CPU [ms] | Peak RAM [MiB] | Instructions | IPC | Cache Miss | Branch Misses | Relative |
| :------- | :------ | ----------: | ----------------: | ---------: | -------------: | -----------: | --: | ---------: | ------------: | ----------: |
| `C# (AOT)` | `11.0.100` | 597.1 ± 31.6 | 562.6..653.9 | 6691.7 | 194.0 | 2.54B | 0.11 | 19.5M (3.8%) | 460.5K | 1.00 ± 0.05 |
| `C++ (g++)` | `14.2.0` | 608.0 ± 45.2 | 563.7..722.1 | 9963.6 | 193.7 | 3.02B | 0.09 | 15.3M (3.0%) | 162.6K | 1.02 ± 0.08 |
| `Rust` | `1.100.0` | 617.9 ± 17.8 | 592.9..648.1 | 7966.0 | 192.0 | 1.56B | 0.06 | 23.4M (4.5%) | 1.1M | 1.03 ± 0.03 |
| `C# (JIT)` | `11.0.100` | 633.4 ± 13.3 | 614.3..660.0 | 7297.5 | 218.0 | 5.36B | 0.21 | 24.3M (4.6%) | 2.7M | 1.06 ± 0.02 |
