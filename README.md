## Contents

- [Prerequisites & Running Benchmarks](#prerequisites--running-benchmarks)
- [1. CountPrimeBenchmark](#1-countprimebenchmark)
- [2. PartitionerBenchmark (Parallel SIMD SquareRoot)](#2-partitionerbenchmark-parallel-simd-squareroot)
- [3. RegexBenchmark](#3-regexbenchmark)
- [4. StringConcatBenchmark](#4-stringconcatbenchmark)
- [5. WebServerBenchmark (Raw HTTP Server)](#5-webserverbenchmark-raw-http-server)
- [6. Proxy Server Benchmark (YARP vs Nginx)](#6-proxy-server-benchmark-yarp-vs-nginx)
- [7. Throw vs Result Benchmark (C# NativeAOT vs Rust)](#7-throw-vs-result-benchmark-c-nativeaot-vs-rust)
- [8. LinqBenchmark (C# LINQ vs Struct Functor vs Rust Iterator)](#8-linqbenchmark-c-linq-vs-struct-functor-vs-rust-iterator)

## Prerequisites & Running Benchmarks

### Automated Run (Recommended)

You can compile all code (JIT, AOT, C, C++, Rust), install dependencies, run the hyperfine and bombardier benchmarks sequentially (including automatic hosting/teardown of the web servers), and update this `README.md` file using the provided Ansible playbooks in `./playbooks`.

To run everything automatically:
```bash
# Install Ansible if not installed
sudo apt update && sudo apt install ansible -y

# Execute all playbooks
ansible-playbook playbooks/all.yml
```

#### Run Individual Playbooks

Each benchmark has its own standalone playbook in `./playbooks/benchmarks/<name>.yml`:

- `prime` — `CountPrimeBenchmark`
- `partitioner` — `PartitionerBenchmark` (SIMD + Multi-threading)
- `regex` — `RegexBenchmark`
- `string` — `StringConcatBenchmark`
- `webserver` — `WebServerBenchmark`
- `proxy` — `ProxyServerBenchmark`
- `throw_vs_result` — `ThrowVsResultBenchmark`
- `linq` — `LinqBenchmark` (C# LINQ vs Struct Functor vs Rust Iterator)

```bash
# Run a single benchmark
ansible-playbook playbooks/benchmarks/prime.yml

# Only update README.md from existing results JSON files
ansible-playbook playbooks/results.yml

# Update all dependencies (apt packages + isolated tools in ~/.bench-tools)
ansible-playbook playbooks/update.yml
```

---

## 1. CountPrimeBenchmark

_Counting prime numbers up to 30 million using multiple threads._

<!-- TABLE_START: prime -->
| Language | Version | Wall [ms] | Min..Max [ms] | CPU [ms] | Peak RAM [MiB] | Instructions | IPC | Cache Miss | Branch Misses | Relative |
| :------- | :------ | ----------: | ----------------: | ---------: | -------------: | -----------: | --: | ---------: | ------------: | ----------: |
| [`C# (AOT)`](src/CountPrimeBenchmark/cs/Program.cs) | `11.0.100` | 703.6 ± 17.9 | 687.3..749.5 | 11914.9 | 3.6 | 34.91B | 0.73 | 1.7M (22.7%) | 16.4M | 1.00 ± 0.03 |
| [`Rust`](src/CountPrimeBenchmark/rust/src/main.rs) | `1.100.0` | 709.2 ± 12.7 | 692.7..727.3 | 12090.6 | 2.0 | 41.95B | 0.95 | 500.1K (21.9%) | 14.7M | 1.01 ± 0.02 |
| [`C# (JIT)`](src/CountPrimeBenchmark/cs/Program.cs) | `11.0.100` | 741.7 ± 15.1 | 719.8..769.3 | 12124.8 | 26.5 | 35.09B | 0.74 | 5.0M (25.8%) | 18.0M | 1.05 ± 0.02 |
<!-- TABLE_END: prime -->

## 2. PartitionerBenchmark (Parallel SIMD SquareRoot)

_Computing the square root of 50 million `float` elements (~200 MiB, exceeding L3 cache) over 80 iterations with parallel initialization and equal per-core static chunking across C# `Partitioner` + `Vector<float>`, Rust `rayon` (`par_chunks_mut`), and C++ OpenMP (`simd`)._

<!-- TABLE_START: partitioner -->
| Language | Version | Wall [ms] | Min..Max [ms] | CPU [ms] | Peak RAM [MiB] | Instructions | IPC | Cache Miss | Branch Misses | Relative |
| :------- | :------ | ----------: | ----------------: | ---------: | -------------: | -----------: | --: | ---------: | ------------: | ----------: |
| [`C# (AOT)`](src/PartitionerBenchmark/cs/Program.cs) | `11.0.100` | 597.1 ± 31.6 | 562.6..653.9 | 6691.7 | 194.0 | 2.54B | 0.11 | 19.5M (3.8%) | 460.5K | 1.00 ± 0.05 |
| [`C++ (g++)`](src/PartitionerBenchmark/cpp/PartitionerBenchmark.cpp) | `14.2.0` | 608.0 ± 45.2 | 563.7..722.1 | 9963.6 | 193.7 | 3.02B | 0.09 | 15.3M (3.0%) | 162.6K | 1.02 ± 0.08 |
| [`Rust`](src/PartitionerBenchmark/rust/src/main.rs) | `1.100.0` | 617.9 ± 17.8 | 592.9..648.1 | 7966.0 | 192.0 | 1.56B | 0.06 | 23.4M (4.5%) | 1.1M | 1.03 ± 0.03 |
| [`C# (JIT)`](src/PartitionerBenchmark/cs/Program.cs) | `11.0.100` | 633.4 ± 13.3 | 614.3..660.0 | 7297.5 | 218.0 | 5.36B | 0.21 | 24.3M (4.6%) | 2.7M | 1.06 ± 0.02 |
<!-- TABLE_END: partitioner -->

## 3. RegexBenchmark

_Executing regex pattern matching 10 million times._

<!-- TABLE_START: regex -->
| Language | Version | Wall [s] | Min..Max [s] | CPU [s] | Peak RAM [MiB] | Instructions | IPC | Cache Miss | Branch Misses | Relative |
| :------- | :------ | ----------: | ----------------: | ---------: | -------------: | -----------: | --: | ---------: | ------------: | ----------: |
| [`C`](src/RegexBenchmark/c/RegexBenchmark.c) | `14.2.0` | 1.102 ± 0.019 | 1.077..1.132 | 1.202 | 2.0 | 25.33B | 4.94 | 123.8K (0.1%) | 77.0K | 1.00 ± 0.02 |
| [`Rust`](src/RegexBenchmark/rust/src/main.rs) | `1.100.0` | 1.271 ± 0.017 | 1.252..1.305 | 1.380 | 2.7 | 25.37B | 4.31 | 196.5K (4.1%) | 85.9K | 1.15 ± 0.02 |
| [`C# (AOT)`](src/RegexBenchmark/cs/Program.cs) | `11.0.100` | 2.141 ± 0.077 | 2.077..2.278 | 2.330 | 3.3 | 27.10B | 2.72 | 377.0K (27.2%) | 3.2M | 1.94 ± 0.07 |
| [`C# (JIT)`](src/RegexBenchmark/cs/Program.cs) | `11.0.100` | 2.224 ± 0.019 | 2.197..2.250 | 2.451 | 28.0 | 26.25B | 2.51 | 4.7M (24.1%) | 5.7M | 2.02 ± 0.02 |
| [`Python`](src/RegexBenchmark/py/RegexBenchmark.py) | `3.12.3` | 7.358 ± 0.082 | 7.287..7.531 | 8.018 | 10.5 | 138.70B | 4.05 | 5.5M (10.8%) | 14.8M | 6.67 ± 0.07 |
<!-- TABLE_END: regex -->

## 4. StringConcatBenchmark

_String concatenation performance tests._

<!-- TABLE_START: string -->
| Language | Version | Wall [s] | Min..Max [s] | CPU [s] | Peak RAM [MiB] | Instructions | IPC | Cache Miss | Branch Misses | Relative |
| :------- | :------ | ----------: | ----------------: | ---------: | -------------: | -----------: | --: | ---------: | ------------: | ----------: |
| [`C`](src/StringConcatBenchmark/c/StringConcatBenchmark.c) | `14.2.0` | 1.022 ± 0.011 | 1.010..1.029 | 1.115 | 1.5 | 18.59B | 3.90 | 292.4K (24.7%) | 120.1K | 1.00 ± 0.01 |
| [`C# (JIT)`](src/StringConcatBenchmark/cs/Program.cs) | `11.0.100` | 1.145 ± 0.006 | 1.139..1.151 | 1.287 | 61.2 | 21.42B | 4.08 | 6.1M (20.2%) | 4.7M | 1.12 ± 0.01 |
| [`C# (AOT)`](src/StringConcatBenchmark/cs/Program.cs) | `11.0.100` | 1.156 ± 0.047 | 1.125..1.211 | 1.253 | 3.4 | 23.60B | 4.44 | 381.0K (29.7%) | 108.1K | 1.13 ± 0.05 |
<!-- TABLE_END: string -->

## 5. WebServerBenchmark (Raw HTTP Server)

_Comparing the throughput of a basic plaintext HTTP "Hello World" response between ASP.NET Core Kestrel, the `zerg` io_uring library for Linux, and Rust Actix-web._

> **Note:** Logging is completely disabled to prevent I/O overhead.

<!-- TABLE_START: webserver -->
| Server | Version | Reqs/sec (Avg ± Stdev) | Relative RPS | Latency (Avg ± Stdev) | Relative Latency | Throughput | Relative Throughput |
|:---|:---|---:|---:|---:|---:|---:|---:|
| [`Zerg (AOT)`](src/WebServerBenchmark/csZerg/Program.cs) | `11.0.100` | 405421.53 ± 63802.23 | 1.00x | 0.31 ± 0.22 ms | 1.00x | 29.74 MB/s | 0.98x |
| [`Zerg (JIT)`](src/WebServerBenchmark/csZerg/Program.cs) | `11.0.100` | 400230.65 ± 62331.96 | 0.99x | 0.31 ± 0.18 ms | 1.01x | 29.37 MB/s | 0.97x |
| [`Actix-web (Rust)`](src/WebServerBenchmark/rust_actix/src/main.rs) | `1.100.0` | 353494.60 ± 51472.39 | 0.87x | 0.35 ± 0.15 ms | 1.15x | 30.32 MB/s | 1.00x |
| [`Kestrel (JIT)`](src/WebServerBenchmark/cs/Program.cs) | `11.0.100` | 162242.28 ± 32687.31 | 0.40x | 0.77 ± 0.30 ms | 2.52x | 23.98 MB/s | 0.79x |
| [`Kestrel (AOT)`](src/WebServerBenchmark/cs/Program.cs) | `11.0.100` | 139104.81 ± 18569.53 | 0.34x | 0.90 ± 0.16 ms | 2.94x | 12.47 MB/s | 0.41x |
<!-- TABLE_END: webserver -->

## 6. Proxy Server Benchmark (YARP vs Nginx)

_Comparing the C# YARP (Yet Another Reverse Proxy) against Nginx, both routing to the target API server on port 5000._

<!-- TABLE_START: proxy -->
| Proxy | Version | Reqs/sec (Avg ± Stdev) | Relative RPS | Latency (Avg ± Stdev) | Relative Latency | Throughput | Relative Throughput |
|:---|:---|---:|---:|---:|---:|---:|---:|
| [`Nginx`](src/WebServerBenchmark/nginx/nginx.conf) | `1.24.0` | 131265.18 ± 12275.75 | 1.00x | 0.95 ± 0.15 ms | 1.00x | 26.28 MB/s | 1.00x |
| [`YARP (JIT)`](src/WebServerBenchmark/cs/Program.cs) | `11.0.100` | 89282.27 ± 11414.30 | 0.68x | 1.40 ± 1.21 ms | 1.47x | 13.19 MB/s | 0.50x |
| [`YARP (AOT)`](src/WebServerBenchmark/cs/Program.cs) | `11.0.100` | 85775.31 ± 11145.78 | 0.65x | 1.46 ± 0.73 ms | 1.53x | 12.67 MB/s | 0.48x |
<!-- TABLE_END: proxy -->

## 7. Throw vs Result Benchmark (C# NativeAOT vs Rust)

_Comparing Rust `Result<i32, DomainError>` / `catch_unwind` against C# 15 `[Union] Result<int, ErrorCode>`, classic `TryOut`, and `throw`/`catch` at a 10% failure rate (each failure carrying an `ErrorCode` + string message). Identical parameters within each table: `Sync` runs 300 million operations (~0.5 s baseline), `Async` runs 80 million operations (~0.5 s baseline)._

### Sync (300M operations)

<!-- TABLE_START: throw_vs_result_sync -->
| Variant | Version | Wall [s] | Min..Max [s] | CPU [s] | Peak RAM [MiB] | Instructions | IPC | Cache Miss | Branch Misses | Relative |
| :------- | :------ | ----------: | ----------------: | ---------: | -------------: | -----------: | --: | ---------: | ------------: | ----------: |
| [`Rust Result`](src/ThrowVsResultBenchmark/rust/src/main.rs) | `1.100.0` | 0.496 ± 0.033 | 0.474..0.534 | 0.537 | 1.7 | 7.23B | 3.19 | 83.2K (33.5%) | 335.1K | 1.00 ± 0.07 |
| [`C# TryOut`](src/ThrowVsResultBenchmark/cs/Program.cs) | `11.0.100` | 0.525 ± 0.018 | 0.514..0.546 | 0.562 | 3.5 | 8.73B | 3.67 | 93.9K (35.3%) | 4.1M | 1.06 ± 0.04 |
| [`C# Result`](src/ThrowVsResultBenchmark/cs/Program.cs) | `11.0.100` | 1.497 ± 0.015 | 1.483..1.512 | 1.626 | 3.5 | 12.39B | 1.77 | 111.0K (29.6%) | 4.2M | 3.02 ± 0.03 |
| [`C# Throw`](src/ThrowVsResultBenchmark/cs/Program.cs) | `11.0.100` | 27.905 ± 0.146 | 27.736..28.002 | 30.509 | 54.4 | 414.15B | 3.21 | 47.3M (11.8%) | 44.5M | 56.21 ± 0.29 |
| [`Rust Panic (catch_unwind)`](src/ThrowVsResultBenchmark/rust/src/main.rs) | `1.100.0` | 40.665 ± 0.214 | 40.475..40.896 | 44.474 | 1.8 | 657.66B | 3.46 | 16.5M (8.5%) | 48.6M | 81.91 ± 0.43 |
<!-- TABLE_END: throw_vs_result_sync -->

### Async (80M operations)

<!-- TABLE_START: throw_vs_result_async -->
| Variant | Version | Wall [s] | Min..Max [s] | CPU [s] | Peak RAM [MiB] | Instructions | IPC | Cache Miss | Branch Misses | Relative |
| :------- | :------ | ----------: | ----------------: | ---------: | -------------: | -----------: | --: | ---------: | ------------: | ----------: |
| [`Rust AsyncResult`](src/ThrowVsResultBenchmark/rust/src/main.rs) | `1.100.0` | 0.475 ± 0.002 | 0.473..0.476 | 0.514 | 1.8 | 3.05B | 1.37 | 34.4K (28.4%) | 388.3K | 1.00 ± 0.00 |
| [`C# AsyncResult (runtime-async)`](src/ThrowVsResultBenchmark/cs/Program.cs) | `11.0.100` | 0.512 ± 0.003 | 0.510..0.515 | 0.548 | 3.5 | 6.27B | 2.70 | 83.7K (35.3%) | 4.9M | 1.08 ± 0.01 |
| [`C# AsyncResult (no runtime-async)`](src/ThrowVsResultBenchmark/cs/Program.cs) | `11.0.100` | 2.111 ± 0.022 | 2.086..2.128 | 2.297 | 3.5 | 17.08B | 1.75 | 435.9K (35.5%) | 7.8M | 4.44 ± 0.05 |
| [`C# AsyncThrow (runtime-async)`](src/ThrowVsResultBenchmark/cs/Program.cs) | `11.0.100` | 8.643 ± 0.066 | 8.584..8.714 | 9.440 | 51.8 | 131.34B | 3.30 | 14.4M (12.5%) | 12.8M | 18.21 ± 0.14 |
| [`C# AsyncThrow (no runtime-async)`](src/ThrowVsResultBenchmark/cs/Program.cs) | `11.0.100` | 22.745 ± 0.032 | 22.720..22.781 | 24.865 | 52.4 | 325.94B | 3.09 | 69.7M (6.3%) | 89.7M | 47.84 ± 0.07 |
<!-- TABLE_END: throw_vs_result_async -->

## 8. LinqBenchmark (C# LINQ vs Struct Functor vs Rust Iterator)

_Comparing C# LINQ delegates (`JIT` with Dynamic PGO vs `NativeAOT` without PGO), C# monomorphized `struct` functors (`where TSelector : struct`), and Rust zero-cost iterators over an L2-resident array of 4,096 16-byte `Item` structs._

### Sum with Selector (`200,000` passes × `4,096` items)

<!-- TABLE_START: linq_sum -->
| Variant | Version | Wall [s] | Min..Max [s] | CPU [s] | Peak RAM [MiB] | Instructions | IPC | Cache Miss | Branch Misses | Relative |
| :------- | :------ | ----------: | ----------------: | ---------: | -------------: | -----------: | --: | ---------: | ------------: | ----------: |
| [`Rust Iterator`](src/LinqBenchmark/rust/src/main.rs) | `1.100.0` | 0.373 ± 0.011 | 0.361..0.384 | 0.409 | 1.8 | 4.68B | 2.76 | 3.4M (1.6%) | 213.8K | 1.00 ± 0.03 |
| [`C# StructFunctor (AOT)`](src/LinqBenchmark/cs/Program.cs) | `11.0.100` | 0.422 ± 0.006 | 0.418..0.429 | 0.457 | 3.5 | 8.20B | 4.33 | 4.0M (1.6%) | 219.6K | 1.13 ± 0.02 |
| [`C# StructFunctor (JIT)`](src/LinqBenchmark/cs/Program.cs) | `11.0.100` | 0.691 ± 0.006 | 0.687..0.697 | 0.757 | 24.5 | 10.54B | 3.42 | 7.0M (3.1%) | 962.2K | 1.85 ± 0.01 |
| [`C# LINQ (JIT)`](src/LinqBenchmark/cs/Program.cs) | `11.0.100` | 0.840 ± 0.011 | 0.833..0.852 | 0.925 | 25.6 | 17.28B | 4.50 | 7.6M (3.4%) | 6.2M | 2.25 ± 0.03 |
| [`C# LINQ (AOT)`](src/LinqBenchmark/cs/Program.cs) | `11.0.100` | 4.243 ± 0.044 | 4.218..4.294 | 4.703 | 9.6 | 50.82B | 2.55 | 5.6M (2.5%) | 443.3K | 11.38 ± 0.12 |
<!-- TABLE_END: linq_sum -->

### Pipeline: `Where().Select().Sum()` (`100,000` passes × `4,096` items)

<!-- TABLE_START: linq_pipeline -->
| Variant | Version | Wall [s] | Min..Max [s] | CPU [s] | Peak RAM [MiB] | Instructions | IPC | Cache Miss | Branch Misses | Relative |
| :------- | :------ | ----------: | ----------------: | ---------: | -------------: | -----------: | --: | ---------: | ------------: | ----------: |
| [`Rust Iterator`](src/LinqBenchmark/rust/src/main.rs) | `1.100.0` | 0.210 ± 0.001 | 0.210..0.211 | 0.229 | 1.8 | 2.96B | 3.03 | 1.6M (1.5%) | 75.7K | 1.00 ± 0.00 |
| [`C# StructFunctor (AOT)`](src/LinqBenchmark/cs/Program.cs) | `11.0.100` | 0.318 ± 0.004 | 0.314..0.323 | 0.339 | 3.5 | 3.70B | 2.57 | 2.6M (2.4%) | 59.6K | 1.51 ± 0.02 |
| [`C# StructFunctor (JIT)`](src/LinqBenchmark/cs/Program.cs) | `11.0.100` | 0.494 ± 0.004 | 0.490..0.498 | 0.539 | 24.5 | 6.11B | 2.74 | 5.1M (4.4%) | 1.4M | 2.35 ± 0.02 |
| [`C# LINQ (JIT)`](src/LinqBenchmark/cs/Program.cs) | `11.0.100` | 0.838 ± 0.007 | 0.830..0.843 | 0.931 | 37.8 | 14.35B | 3.77 | 6.7M (5.5%) | 8.3M | 3.98 ± 0.03 |
| [`C# LINQ (AOT)`](src/LinqBenchmark/cs/Program.cs) | `11.0.100` | 5.099 ± 0.006 | 5.094..5.106 | 5.654 | 17.9 | 44.72B | 1.86 | 6.1M (4.9%) | 101.2M | 24.22 ± 0.03 |
<!-- TABLE_END: linq_pipeline -->
