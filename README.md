# Benchmark Results

Here are the results for the benchmarking runs across different languages and test cases.

## Prerequisites & Running Benchmarks

### Automated Run (Recommended)

You can compile all code (JIT, AOT, C, Rust), install dependencies, run the hyperfine and bombardier benchmarks sequentially (including automatic hosting/teardown of the web servers), and update this `README.md` file using the provided Ansible playbook.

To run everything automatically:
```bash
# Install Ansible if not installed
sudo apt update && sudo apt install ansible -y

# Execute the playbook (runs all benchmarks)
ansible-playbook playbook_run_benchmarks.yml
```

#### Run Specific Benchmarks (Using Tags)

The playbook is equipped with **Tags** so you can run only specific test suites. The available tags are:
* `prime` — Runs only `CountPrimeBenchmark`
* `regex` — Runs only `RegexBenchmark`
* `string` — Runs only `StringConcatBenchmark`
* `webserver` — Runs only `WebServerBenchmark`
* `proxy` — Runs only `ProxyServerBenchmark`
* `result` — Runs only the result conversion script to update `README.md` based on current results JSON files

Examples:
```bash
# Run ONLY the prime numbers benchmark
ansible-playbook playbook_run_benchmarks.yml --tags prime

# Run both WebServer and Proxy benchmarks
ansible-playbook playbook_run_benchmarks.yml --tags "webserver,proxy"

# Skip the heavy 60-second webserver/proxy benchmarks and run only simple CLI ones
ansible-playbook playbook_run_benchmarks.yml --skip-tags "webserver,proxy"
```

---

## 1. CountPrimeBenchmark

_Counting prime numbers up to 15 million using multiple threads._

<!-- TABLE_START: prime -->
| Language | Mean [ms] | Min [ms] | Max [ms] | Relative |
| :------- | ----------: | -------: | -------: | ----------: |
| `Rust` | 252.4 ± 0.7 | 251.7 | 254.0 | 1.00 ± 0.00 |
| `C# (AOT)` | 314.5 ± 4.4 | 308.9 | 324.7 | 1.25 ± 0.02 |
| `C# (JIT)` | 318.5 ± 4.2 | 310.1 | 325.4 | 1.26 ± 0.02 |
<!-- TABLE_END: prime -->

## 2. RegexBenchmark

_Executing regex pattern matching 10 million times._

<!-- TABLE_START: regex -->
| Language | Mean [s] | Min [s] | Max [s] | Relative |
| :------- | ------------: | ------: | ------: | ----------: |
| `C` | 1.093 ± 0.022 | 1.069 | 1.154 | 1.00 ± 0.02 |
| `Rust` | 1.274 ± 0.012 | 1.254 | 1.296 | 1.16 ± 0.01 |
| `C# (JIT)` | 2.057 ± 0.023 | 2.030 | 2.112 | 1.88 ± 0.02 |
| `C# (AOT)` | 2.063 ± 0.030 | 2.026 | 2.132 | 1.89 ± 0.03 |
| `Python` | 7.324 ± 0.087 | 7.245 | 7.529 | 6.70 ± 0.08 |
<!-- TABLE_END: regex -->

## 3. StringConcatBenchmark

_String concatenation performance tests._

<!-- TABLE_START: string -->
| Language | Mean [s] | Min [s] | Max [s] | Relative |
| :------- | ------------: | ------: | ------: | ----------: |
| `C` | 1.015 ± 0.008 | 1.007 | 1.023 | 1.00 ± 0.01 |
| `C# (JIT)` | 1.187 ± 0.014 | 1.175 | 1.203 | 1.17 ± 0.01 |
| `C# (AOT)` | 1.198 ± 0.032 | 1.172 | 1.233 | 1.18 ± 0.03 |
<!-- TABLE_END: string -->

## 4. WebServerBenchmark (Raw HTTP Server)

_Comparing the throughput of a basic plaintext HTTP "Hello World" response between ASP.NET Core Kestrel, the `zerg` io_uring library for Linux, and Rust Actix-web._

> **Note:** Logging is completely disabled to prevent I/O overhead.

<!-- TABLE_START: webserver -->
| Server | Reqs/sec (Avg ± Stdev) | Relative RPS | Latency (Avg ± Stdev) | Relative Latency | Throughput | Relative Throughput |
|:---|---:|---:|---:|---:|---:|---:|
| **Zerg (AOT)** | 467416.02 ± 41125.22 | 1.00x | 0.26 ± 0.16 ms | 1.00x | 34.30 MB/s | 0.98x |
| **Zerg (JIT)** | 449090.95 ± 47224.18 | 0.96x | 0.27 ± 0.16 ms | 1.04x | 32.96 MB/s | 0.94x |
| **Actix-web (Rust)** | 409087.48 ± 44093.79 | 0.88x | 0.30 ± 0.13 ms | 1.15x | 35.11 MB/s | 1.00x |
| **Kestrel (JIT)** | 217323.88 ± 25984.89 | 0.46x | 0.57 ± 0.28 ms | 2.17x | 32.12 MB/s | 0.92x |
| **Kestrel (AOT)** | 154585.73 ± 15731.23 | 0.33x | 0.81 ± 0.25 ms | 3.06x | 13.85 MB/s | 0.39x |
<!-- TABLE_END: webserver -->

## 5. Proxy Server Benchmark (YARP vs Nginx)

_Comparing the C# YARP (Yet Another Reverse Proxy) against Nginx, both routing to the target API server on port 5000._

<!-- TABLE_START: proxy -->
| Proxy | Reqs/sec (Avg ± Stdev) | Relative RPS | Latency (Avg ± Stdev) | Relative Latency | Throughput | Relative Throughput |
|:---|---:|---:|---:|---:|---:|---:|
| **Nginx** | 131265.18 ± 12275.75 | 1.00x | 0.95 ± 0.15 ms | 1.00x | 26.28 MB/s | 1.00x |
| **YARP (JIT)** | 89282.27 ± 11414.30 | 0.68x | 1.40 ± 1.21 ms | 1.47x | 13.19 MB/s | 0.50x |
| **YARP (AOT)** | 85775.31 ± 11145.78 | 0.65x | 1.46 ± 0.73 ms | 1.53x | 12.67 MB/s | 0.48x |
<!-- TABLE_END: proxy -->
