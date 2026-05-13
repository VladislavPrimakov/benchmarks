# Benchmark Results

Here are the results for the benchmarking runs across different languages and test cases. The tool used for benchmarking was `hyperfine`, which was executed via WSL.

## 1. CountPrimeBenchmark

_Counting prime numbers up to 15 million using multiple threads._

**Compilation Commands:**

```bash
# C#
dotnet build -c Release CountPrimeBenchmark/cs/CountPrimeBenchmark.csproj

# Rust
cargo build --release --manifest-path CountPrimeBenchmark/rust/CountPrimeBenchmark/Cargo.toml
```

**Benchmark Command:**

```bash
wsl hyperfine -r 3 \
  -n "C#" "./CountPrimeBenchmark/cs/bin/Release/net10.0/linux-x64/CountPrimeBenchmark" \
  -n "Rust" "./CountPrimeBenchmark/rust/CountPrimeBenchmark/target/release/multithread_benchmark"
```

| Language |   Mean [ms] | Min [ms] | Max [ms] |    Relative |
| :------- | ----------: | -------: | -------: | ----------: |
| `Rust`   | 280.0 ± 8.4 |    274.4 |    289.7 |        1.00 |
| `C#`     | 356.7 ± 6.7 |    352.2 |    364.4 | 1.27 ± 0.05 |

## 2. RegexBenchmark

_Executing regex pattern matching 10 million times._

**Compilation Commands:**

```bash
# C (Requires libpcre2-dev)
gcc -O3 RegexBenchmarks/c/RegexBenchmark.c -o RegexBenchmarks/c/regex_benchmark_c -lpcre2-8

# C#
dotnet build -c Release RegexBenchmarks/cs/RegexBenchmark.csproj

# Rust
cargo build --release --manifest-path RegexBenchmarks/rust/RegexBenchmark/Cargo.toml

# Python
# No compilation required
```

**Benchmark Command:**

```bash
wsl hyperfine -r 3 \
  -n "C" "./RegexBenchmarks/c/regex_benchmark_c" \
  -n "C#" "./RegexBenchmarks/cs/bin/Release/net10.0/linux-x64/RegexBenchmark" \
  -n "Python" "python3 ./RegexBenchmarks/py/RegexBenchmark.py" \
  -n "Rust" "./RegexBenchmarks/rust/RegexBenchmark/target/release/regex_benchmark" \
  --export-markdown regex_results.md
```

| Language |      Mean [s] | Min [s] | Max [s] |    Relative |
| :------- | ------------: | ------: | ------: | ----------: |
| `C`      | 1.147 ± 0.019 |   1.129 |   1.167 |        1.00 |
| `Rust`   | 1.619 ± 0.013 |   1.610 |   1.633 | 1.41 ± 0.03 |
| `C#`     | 2.129 ± 0.037 |   2.099 |   2.170 | 1.86 ± 0.04 |
| `Python` | 7.592 ± 0.106 |   7.490 |   7.702 | 6.62 ± 0.14 |

## 3. StringConcatBenchmark

_String concatenation performance tests._

**Compilation Commands:**

```bash
# C
gcc -O3 StringConcatBenchmark/c/StringConcatBenchmark.c -o StringConcatBenchmark/c/StringConcatBenchmark_c

# C#
dotnet build -c Release StringConcatBenchmark/cs/StringConcatBenchmark.csproj
```

**Benchmark Command:**

```bash
wsl hyperfine -r 3 \
  -n "C" "./StringConcatBenchmark/c/StringConcatBenchmark_c" \
  -n "C#" "./StringConcatBenchmark/cs/bin/Release/net10.0/StringConcatBenchmark"
```

| Language |      Mean [s] | Min [s] | Max [s] |    Relative |
| :------- | ------------: | ------: | ------: | ----------: |
| `C`      | 1.054 ± 0.018 |   1.034 |   1.067 |        1.00 |
| `C#`     | 1.208 ± 0.008 |   1.203 |   1.217 | 1.15 ± 0.02 |

## 4. WebServerBenchmark (Raw HTTP Server: Zerg io_uring vs Kestrel)

_Comparing the throughput of a basic plaintext HTTP "Hello World" response between ASP.NET Core Kestrel and the `zerg` io_uring library for Linux._

> **Note:** Logging is completely disabled in `Program.cs` (`builder.Logging.ClearProviders()`) and in Nginx (`access_log off;`) to prevent I/O overhead from dropping the Request-Per-Second (RPS) rate.

**Prerequisites:**
Download `bombardier` and make it executable:

```bash
wget https://github.com/codesenberg/bombardier/releases/download/v1.2.6/bombardier-linux-amd64 -O WebServerBenchmark/bombardier-linux-amd64
chmod +x WebServerBenchmark/bombardier-linux-amd64
```

**Compilation Commands:**

```bash
# Kestrel (WebServerBenchmark API mode)
dotnet build -c Release WebServerBenchmark/cs/WebServerBenchmark.csproj

# Zerg (csZerg)
dotnet build -c Release WebServerBenchmark/csZerg/ZergBenchmark.csproj
```

**Start Server Commands (Run in background):**

```bash
# Start Kestrel on port 5000
wsl bash -c "cd WebServerBenchmark/cs && dotnet bin/Release/net10.0/WebServerBenchmark.dll --urls 'http://127.0.0.1:5000' --mode api &"

# Start Zerg on port 5005
wsl bash -c "dotnet WebServerBenchmark/csZerg/bin/Release/net10.0/ZergBenchmark.dll &"
```

**Benchmark Commands:**

```bash
# Benchmark Kestrel
wsl ./WebServerBenchmark/bombardier-linux-amd64 -c 125 -d 60s http://127.0.0.1:5000/hello

# Benchmark Zerg
wsl ./WebServerBenchmark/bombardier-linux-amd64 -c 125 -d 60s http://127.0.0.1:5005/
```

**Results (60 seconds, 125 connections):**
| Server | Reqs/sec (Avg ± Stdev) | Relative RPS | Latency (Avg ± Stdev) | Relative Latency | Throughput | Relative Throughput |
|:---|---:|---:|---:|---:|---:|---:|
| **Zerg (io_uring)** | 433,225.04 ± 59,131.77 | 2.23x | 285.43 ± 196.37 µs | 1.00x | 57.42 MB/s | 1.40x |
| **Kestrel (epoll)** | 194,502.01 ± 20,924.64 | 1.00x | 640.68 ± 410.26 µs | 2.24x | 41.16 MB/s | 1.00x |

## 5. Proxy Server Benchmark (YARP vs Nginx)

_Comparing the C# YARP (Yet Another Reverse Proxy) against Nginx, both routing to the target API server on port 5000._

**Setup Commands:**

```bash
# Nginx
wsl -u root apt-get install -y nginx
wsl -u root cp WebServerBenchmark/nginx/nginx.conf /etc/nginx/nginx.conf
wsl -u root service nginx restart

# Start target API (port 5000) and YARP proxy (port 5001) in background
wsl bash -c "cd WebServerBenchmark/cs && dotnet bin/Release/net10.0/WebServerBenchmark.dll --urls 'http://127.0.0.1:5000' --mode api &"
wsl bash -c "cd WebServerBenchmark/cs && dotnet bin/Release/net10.0/WebServerBenchmark.dll --urls 'http://127.0.0.1:5001' --mode yarp &"
```

**Benchmark Commands:**

```bash
# Benchmark YARP (Port 5001)
wsl ./WebServerBenchmark/bombardier-linux-amd64 -c 125 -d 60s http://127.0.0.1:5001/hello

# Benchmark Nginx (Port 5002)
wsl ./WebServerBenchmark/bombardier-linux-amd64 -c 125 -d 60s http://127.0.0.1:5002/hello
```

**Results (60 seconds, 125 connections):**
| Proxy | Reqs/sec (Avg ± Stdev) | Relative RPS | Latency (Avg ± Stdev) | Relative Latency | Throughput | Relative Throughput |
|:---|---:|---:|---:|---:|---:|---:|
| **Nginx** | 109,443.38 ± 10,943.44 | 1.60x | 1.14 ms ± 215.57 µs | 1.00x | 28.90 MB/s | 2.00x |
| **YARP (C#)** | 68,312.23 ± 10,293.97 | 1.00x | 1.83 ± 0.95 ms | 1.61x | 14.46 MB/s | 1.00x |

