# Benchmark Results

Here are the results for the benchmarking runs across different languages and test cases.

## Prerequisites

To run these benchmarks, you need `hyperfine` and `bombardier` installed on your system.

### Install Tools

```bash
# Install hyperfine
sudo apt install hyperfine

# Install bombardier
wget https://github.com/codesenberg/bombardier/releases/download/v1.2.6/bombardier-linux-amd64 -O ./WebServerBenchmark/bombardier
chmod +x ./WebServerBenchmark/bombardier
```

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
hyperfine \
-n "C#" "./CountPrimeBenchmark/cs/bin/Release/net10.0/linux-x64/CountPrimeBenchmark" \
-n "Rust" "./CountPrimeBenchmark/rust/target/release/multithread_benchmark" \
--export-json "./results/prime_results.json"
```

<!-- TABLE_START: prime -->

| Language |    Mean [ms] | Min [ms] | Max [ms] |    Relative |
| :------- | -----------: | -------: | -------: | ----------: |
| `Rust`   |  288.5 ± 6.8 |    280.6 |    302.0 | 1.00 ± 0.02 |
| `C#`     | 367.3 ± 11.2 |    358.0 |    391.6 | 1.27 ± 0.04 |

<!-- TABLE_END: prime -->

## 2. RegexBenchmark

_Executing regex pattern matching 10 million times._

**Compilation Commands:**

```bash
# C (Requires libpcre2-dev)
gcc -O3 RegexBenchmark/c/RegexBenchmark.c -o RegexBenchmark/c/regex_benchmark_c -lpcre2-8

# C#
dotnet build -c Release RegexBenchmark/cs/RegexBenchmark.csproj

# Rust
cargo build --release --manifest-path RegexBenchmark/rust/RegexBenchmark/Cargo.toml

# Python
# No compilation required
```

**Benchmark Command:**

```bash
hyperfine \
-n "C" "./RegexBenchmark/c/regex_benchmark_c" \
-n "C#" "./RegexBenchmark/cs/bin/Release/net10.0/linux-x64/RegexBenchmark" \
-n "Python" "python3 ./RegexBenchmark/py/RegexBenchmark.py" \
-n "Rust" "./RegexBenchmark/rust/target/release/regex_benchmark" \
--export-json "./results/regex_results.json"
```

<!-- TABLE_START: regex -->

| Language |      Mean [s] | Min [s] | Max [s] |    Relative |
| :------- | ------------: | ------: | ------: | ----------: |
| `C`      | 1.234 ± 0.042 |   1.190 |   1.320 | 1.00 ± 0.03 |
| `Rust`   | 1.707 ± 0.026 |   1.672 |   1.748 | 1.38 ± 0.02 |
| `C#`     | 2.274 ± 0.020 |   2.246 |   2.315 | 1.84 ± 0.02 |
| `Python` | 8.334 ± 0.123 |   8.201 |   8.628 | 6.76 ± 0.10 |

<!-- TABLE_END: regex -->

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
hyperfine -r 3 \
-n "C" "./StringConcatBenchmark/c/StringConcatBenchmark_c" \
-n "C#" "./StringConcatBenchmark/cs/bin/Release/net10.0/StringConcatBenchmark" \
--export-json "./results/string_concat_results.json"
```

<!-- TABLE_START: string -->

| Language |      Mean [s] | Min [s] | Max [s] |    Relative |
| :------- | ------------: | ------: | ------: | ----------: |
| `C`      | 1.158 ± 0.025 |   1.135 |   1.185 | 1.00 ± 0.02 |
| `C#`     | 1.331 ± 0.013 |   1.319 |   1.344 | 1.15 ± 0.01 |

<!-- TABLE_END: string -->

## 4. WebServerBenchmark (Raw HTTP Server: Zerg io_uring vs Kestrel)

_Comparing the throughput of a basic plaintext HTTP "Hello World" response between ASP.NET Core Kestrel and the `zerg` io_uring library for Linux._

> **Note:** Logging is completely disabled in `Program.cs` (`builder.Logging.ClearProviders()`) and in Nginx (`access_log off;`) to prevent I/O overhead from dropping the Request-Per-Second (RPS) rate.

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
dotnet WebServerBenchmark/cs/bin/Release/net10.0/WebServerBenchmark.dll --urls 'http://127.0.0.1:5000' --mode api &

# Start Zerg on port 5005
dotnet WebServerBenchmark/csZerg/bin/Release/net10.0/ZergBenchmark.dll > /dev/null 2>&1 &
```

**Benchmark Commands:**

```bash
# Benchmark Kestrel
./bombardier -c 125 -d 60s -p r -o j http://127.0.0.1:5000/ > ./results/kestrel_results.json

# Benchmark Zerg
./bombardier -c 125 -d 60s -p r -o j http://127.0.0.1:5005/ > ./results/zerg_results.json
```

**Results (60 seconds, 125 connections):**

<!-- TABLE_START: webserver -->

| Server              | Reqs/sec (Avg ± Stdev) | Relative RPS | Latency (Avg ± Stdev) | Relative Latency | Throughput | Relative Throughput |
| :------------------ | ---------------------: | -----------: | --------------------: | ---------------: | ---------: | ------------------: |
| **Kestrel (epoll)** |   199121.88 ± 21332.37 |        0.46x |        0.63 ± 0.06 ms |            2.22x | 29.44 MB/s |               0.92x |
| **Zerg (io_uring)** |   437121.63 ± 54377.63 |        1.00x |        0.28 ± 0.18 ms |            1.00x | 32.11 MB/s |               1.00x |

<!-- TABLE_END: webserver -->

## 5. Proxy Server Benchmark (YARP vs Nginx)

_Comparing the C# YARP (Yet Another Reverse Proxy) against Nginx, both routing to the target API server on port 5000._

**Setup Commands:**

```bash
# Nginx
-u root apt-get install -y nginx
-u root cp WebServerBenchmark/nginx/nginx.conf /etc/nginx/nginx.conf
-u root service nginx restart

# Start target API (port 5000) and YARP proxy (port 5001) in background
dotnet WebServerBenchmark/cs/bin/Release/net10.0/WebServerBenchmark.dll --urls 'http://127.0.0.1:5000' --mode api &
dotnet WebServerBenchmark/cs/bin/Release/net10.0/WebServerBenchmark.dll --urls 'http://127.0.0.1:5001' --mode yarp &
```

**Benchmark Commands:**

```bash
# Benchmark YARP (Port 5001)
./bombardier -c 125 -d 60s -p r -o j http://127.0.0.1:5001/ > ./results/yarp_results.json

# Benchmark Nginx (Port 5002)
./bombardier -c 125 -d 60s -p r -o j http://127.0.0.1:5002/ > ./results/nginx_results.json
```

**Results (60 seconds, 125 connections):**

<!-- TABLE_START: proxy -->

| Proxy         | Reqs/sec (Avg ± Stdev) | Relative RPS | Latency (Avg ± Stdev) | Relative Latency | Throughput | Relative Throughput |
| :------------ | ---------------------: | -----------: | --------------------: | ---------------: | ---------: | ------------------: |
| **Nginx**     |   116798.14 ± 11689.33 |        1.00x |        1.07 ± 0.13 ms |            1.00x | 23.39 MB/s |               1.00x |
| **YARP (C#)** |     76256.88 ± 9553.22 |        0.65x |        1.64 ± 0.11 ms |            1.53x | 11.27 MB/s |               0.48x |

<!-- TABLE_END: proxy -->
