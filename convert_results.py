import argparse
import json
import os
import re
import subprocess

SECTIONS = (
    'prime',
    'partitioner',
    'regex',
    'string',
    'webserver',
    'proxy',
    'throw_vs_result',
    'linq',
)


def get_cli_version(cmd, pattern=r"(\d+\.\d+\.\d+)"):
    env = os.environ.copy()
    tools_dir = os.path.expanduser("~/.bench-tools")
    dotnet_dir = os.path.join(tools_dir, "dotnet")
    cargo_bin = os.path.join(tools_dir, "cargo", "bin")
    nginx_sbin = os.path.join(tools_dir, "nginx", "sbin")
    env["DOTNET_ROOT"] = dotnet_dir
    env["CARGO_HOME"] = os.path.join(tools_dir, "cargo")
    env["RUSTUP_HOME"] = os.path.join(tools_dir, "rustup")
    env["PATH"] = f"{tools_dir}:{dotnet_dir}:{cargo_bin}:{nginx_sbin}:/usr/sbin:/sbin:{env.get('PATH', '')}"
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, env=env).strip()
        match = re.search(pattern, out)
        return match.group(1) if match else out.splitlines()[0]
    except Exception:
        return "N/A"


def get_versions():
    return {
        "dotnet": get_cli_version(["dotnet", "--version"]),
        "rust": get_cli_version(["rustc", "--version"]),
        "gcc": get_cli_version(["gcc", "--version"], r"\)\s+(\d+\.\d+\.\d+)"),
        "gpp": get_cli_version(["g++", "--version"], r"\)\s+(\d+\.\d+\.\d+)"),
        "python": get_cli_version(["python3", "--version"]),
        "nginx": get_cli_version(["nginx", "-v"], r"nginx/(\d+\.\d+\.\d+)")
    }


def resolve_version(name, versions):
    if any(k in name for k in ("C#", "Kestrel", "Zerg", "YARP")):
        return versions["dotnet"]
    if "Rust" in name or "Actix" in name:
        return versions["rust"]
    if "C++" in name:
        return versions["gpp"]
    if name.startswith("C"):
        return versions["gcc"]
    if "Python" in name:
        return versions["python"]
    if "Nginx" in name:
        return versions["nginx"]
    return "N/A"


def format_count(value):
    if value is None:
        return "N/A"
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:.0f}"


def format_label(label, sources=None):
    if isinstance(sources, str):
        path = sources
    elif isinstance(sources, dict):
        path = sources.get(label)
    else:
        path = None
    return f"[`{label}`]({path})" if path else f"`{label}`"


def parse_hyperfine(json_path, versions, unit='ms', command_filter=None, sources=None):
    if not os.path.exists(json_path):
        print(f"Warning: Skipping '{json_path}' (file not found)")
        return None
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if data.get('schema_version', 1) < 2:
        raise ValueError(f"'{json_path}' uses legacy hyperfine v1 schema; re-run with hyperfine 2.0+.")

    raw_results = data['results']
    if command_filter is not None:
        raw_results = [r for r in raw_results if command_filter(r.get('name') or r['command'])]
    if not raw_results:
        return None

    parsed = []
    for r in raw_results:
        summary = r['summary']
        wall = summary['time_wall_clock']
        cpu = summary.get('time_cpu')
        mem = summary.get('memory_peak_resident')
        inst = summary.get('instructions')
        cycles = summary.get('cpu_cycles')
        cache_refs = summary.get('cache_references')
        cache_miss = summary.get('cache_misses')
        branches = summary.get('branch_misses')

        inst_mean = inst['mean'] if inst else None
        cycles_mean = cycles['mean'] if cycles else None
        ipc = (inst_mean / cycles_mean) if (inst_mean and cycles_mean and cycles_mean > 0) else None

        cm_mean = cache_miss['mean'] if cache_miss else None
        cr_mean = cache_refs['mean'] if cache_refs else None
        cm_pct = (cm_mean / cr_mean * 100.0) if (cm_mean is not None and cr_mean and cr_mean > 0) else None

        parsed.append({
            'label': r.get('name') or r['command'],
            'mean': wall['mean'],
            'stddev': wall['stddev'],
            'min': wall['min'],
            'max': wall['max'],
            'cpu': cpu['mean'] if cpu else None,
            'mem_mib': (mem['mean'] / (1024 * 1024)) if mem else None,
            'instructions': inst_mean,
            'ipc': ipc,
            'cache_misses': cm_mean,
            'cache_miss_pct': cm_pct,
            'branch_misses': branches['mean'] if branches else None
        })

    min_mean = min(p['mean'] for p in parsed)
    parsed.sort(key=lambda x: x['mean'])

    rows = []
    for p in parsed:
        ver = resolve_version(p['label'], versions)
        mean = p['mean']
        stddev = p['stddev']
        min_val = p['min']
        max_val = p['max']
        relative = mean / min_mean
        rel_std = (stddev / mean * relative) if mean > 0 else 0.0

        if unit == 's':
            time_cols = f"{mean:.3f} ± {stddev:.3f} | {min_val:.3f}..{max_val:.3f}"
            cpu_col = f"{p['cpu']:.3f}" if p['cpu'] is not None else "N/A"
        else:
            time_cols = f"{mean*1000:.1f} ± {stddev*1000:.1f} | {min_val*1000:.1f}..{max_val*1000:.1f}"
            cpu_col = f"{p['cpu']*1000:.1f}" if p['cpu'] is not None else "N/A"

        mem_col = f"{p['mem_mib']:.1f}" if p['mem_mib'] is not None else "N/A"
        inst_col = format_count(p['instructions'])
        ipc_col = f"{p['ipc']:.2f}" if p['ipc'] is not None else "N/A"
        if p['cache_misses'] is not None and p['cache_miss_pct'] is not None:
            cache_col = f"{format_count(p['cache_misses'])} ({p['cache_miss_pct']:.1f}%)"
        else:
            cache_col = format_count(p['cache_misses'])
        br_col = format_count(p['branch_misses'])

        rows.append(
            f"| {format_label(p['label'], sources)} | `{ver}` | {time_cols} | {cpu_col} | {mem_col} | {inst_col} | {ipc_col} | {cache_col} | {br_col} | {relative:.2f} ± {rel_std:.2f} |"
        )

    return rows


def parse_bombardier(entries_map, versions, sort_by='rps', reverse=True):
    parsed = []
    for label, (path, source) in entries_map.items():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            res = data['result']
            parsed.append({
                'label': label,
                'source': source,
                'ver': resolve_version(label, versions),
                'rps': res['rps']['mean'],
                'rps_std': res['rps']['stddev'],
                'lat': res['latency']['mean'] / 1000,
                'lat_std': res['latency']['stddev'] / 1000,
                'throughput': res['bytesRead'] / (1024 * 1024 * res['timeTakenSeconds'])
            })
        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            print(f"Warning: Skipping '{path}' due to error: {e}")
            continue

    if not parsed:
        return None

    parsed.sort(key=lambda x: x[sort_by], reverse=reverse)

    max_rps = max(p['rps'] for p in parsed)
    min_lat = min(p['lat'] for p in parsed)
    max_tp = max(p['throughput'] for p in parsed)

    rows = []
    for p in parsed:
        rows.append(
            f"| {format_label(p['label'], p['source'])} | `{p['ver']}` | {p['rps']:.2f} ± {p['rps_std']:.2f} | {p['rps']/max_rps:.2f}x"
            f" | {p['lat']:.2f} ± {p['lat_std']:.2f} ms | {p['lat']/min_lat:.2f}x"
            f" | {p['throughput']:.2f} MB/s | {p['throughput']/max_tp:.2f}x |"
        )
    return rows


def replace_table(content, tag, header, rows):
    if rows is None:
        return content
    pattern = re.compile(rf"<!-- TABLE_START: {tag} -->(.*?)<!-- TABLE_END: {tag} -->", re.DOTALL)
    new_content = "\n".join(header + rows)
    replacement = f"<!-- TABLE_START: {tag} -->\n{new_content}\n<!-- TABLE_END: {tag} -->"
    return pattern.sub(replacement, content)


def update_hyperfine_table(content, tag, json_path, versions, first_col='Language', unit='ms', command_filter=None, sources=None):
    rows = parse_hyperfine(json_path, versions, unit=unit, command_filter=command_filter, sources=sources)
    header = [
        f"| {first_col} | Version | Wall [{unit}] | Min..Max [{unit}] | CPU [{unit}] | Peak RAM [MiB] | Instructions | IPC | Cache Miss | Branch Misses | Relative |",
        "| :------- | :------ | ----------: | ----------------: | ---------: | -------------: | -----------: | --: | ---------: | ------------: | ----------: |"
    ]
    return replace_table(content, tag, header, rows)


def update_readme(only=None):
    selected = set(only) if only else set(SECTIONS)
    versions = get_versions()
    results_dir = os.environ.get("BENCH_RESULTS_DIR", os.path.expanduser("~/.bench-tools/results"))
    res = lambda name: os.path.join(results_dir, name)

    with open('README.md', 'r', encoding='utf-8') as f:
        content = f.read()

    # Hyperfine v2 benchmarks
    if 'prime' in selected:
        content = update_hyperfine_table(
            content, 'prime', res('prime.json'), versions, 'Language', 'ms',
            sources={
                'C# (JIT)': 'src/CountPrimeBenchmark/cs/Program.cs',
                'C# (AOT)': 'src/CountPrimeBenchmark/cs/Program.cs',
                'Rust': 'src/CountPrimeBenchmark/rust/src/main.rs',
            }
        )
    if 'partitioner' in selected:
        content = update_hyperfine_table(
            content, 'partitioner', res('partitioner.json'), versions, 'Language', 'ms',
            sources={
                'C++ (g++)': 'src/PartitionerBenchmark/cpp/PartitionerBenchmark.cpp',
                'C# (JIT)': 'src/PartitionerBenchmark/cs/Program.cs',
                'C# (AOT)': 'src/PartitionerBenchmark/cs/Program.cs',
                'Rust': 'src/PartitionerBenchmark/rust/src/main.rs',
            }
        )
    if 'regex' in selected:
        content = update_hyperfine_table(
            content, 'regex', res('regex.json'), versions, 'Language', 's',
            sources={
                'C': 'src/RegexBenchmark/c/RegexBenchmark.c',
                'C# (JIT)': 'src/RegexBenchmark/cs/Program.cs',
                'C# (AOT)': 'src/RegexBenchmark/cs/Program.cs',
                'Python': 'src/RegexBenchmark/py/RegexBenchmark.py',
                'Rust': 'src/RegexBenchmark/rust/src/main.rs',
            }
        )
    if 'string' in selected:
        content = update_hyperfine_table(
            content, 'string', res('string_concat.json'), versions, 'Language', 's',
            sources={
                'C': 'src/StringConcatBenchmark/c/StringConcatBenchmark.c',
                'C# (JIT)': 'src/StringConcatBenchmark/cs/Program.cs',
                'C# (AOT)': 'src/StringConcatBenchmark/cs/Program.cs',
            }
        )
    if 'throw_vs_result' in selected:
        throw_sources = {
            'Rust Result': 'src/ThrowVsResultBenchmark/rust/src/main.rs',
            'Rust AsyncResult': 'src/ThrowVsResultBenchmark/rust/src/main.rs',
            'Rust Panic (catch_unwind)': 'src/ThrowVsResultBenchmark/rust/src/main.rs',
            'C# TryOut': 'src/ThrowVsResultBenchmark/cs/Program.cs',
            'C# Result': 'src/ThrowVsResultBenchmark/cs/Program.cs',
            'C# AsyncResult (runtime-async)': 'src/ThrowVsResultBenchmark/cs/Program.cs',
            'C# AsyncResult (no runtime-async)': 'src/ThrowVsResultBenchmark/cs/Program.cs',
            'C# Throw': 'src/ThrowVsResultBenchmark/cs/Program.cs',
            'C# AsyncThrow (runtime-async)': 'src/ThrowVsResultBenchmark/cs/Program.cs',
            'C# AsyncThrow (no runtime-async)': 'src/ThrowVsResultBenchmark/cs/Program.cs',
        }
        content = update_hyperfine_table(
            content, 'throw_vs_result_sync', res('throw_vs_result.json'), versions,
            'Variant', 's', command_filter=lambda c: 'Async' not in c, sources=throw_sources
        )
        content = update_hyperfine_table(
            content, 'throw_vs_result_async', res('throw_vs_result.json'), versions,
            'Variant', 's', command_filter=lambda c: 'Async' in c, sources=throw_sources
        )
    if 'linq' in selected:
        linq_sources = {
            'Rust Iterator': 'src/LinqBenchmark/rust/src/main.rs',
            'C# StructFunctor (JIT)': 'src/LinqBenchmark/cs/Program.cs',
            'C# StructFunctor (AOT)': 'src/LinqBenchmark/cs/Program.cs',
            'C# LINQ (JIT)': 'src/LinqBenchmark/cs/Program.cs',
            'C# LINQ (AOT)': 'src/LinqBenchmark/cs/Program.cs',
        }
        content = update_hyperfine_table(
            content, 'linq_sum', res('linq_sum.json'), versions,
            'Variant', 's', sources=linq_sources
        )
        content = update_hyperfine_table(
            content, 'linq_pipeline', res('linq_pipeline.json'), versions,
            'Variant', 's', sources=linq_sources
        )

    # WebServer
    if 'webserver' in selected:
        header_web = [
            "| Server | Version | Reqs/sec (Avg ± Stdev) | Relative RPS | Latency (Avg ± Stdev) | Relative Latency | Throughput | Relative Throughput |",
            "|:---|:---|---:|---:|---:|---:|---:|---:|"
        ]
        content = replace_table(content, 'webserver', header_web, parse_bombardier({
            'Zerg (JIT)': (res('webserver_zerg_jit.json'), 'src/WebServerBenchmark/csZerg/Program.cs'),
            'Zerg (AOT)': (res('webserver_zerg_aot.json'), 'src/WebServerBenchmark/csZerg/Program.cs'),
            'Actix-web (Rust)': (res('webserver_actix.json'), 'src/WebServerBenchmark/rust_actix/src/main.rs'),
            'Kestrel (JIT)': (res('webserver_kestrel_jit.json'), 'src/WebServerBenchmark/cs/Program.cs'),
            'Kestrel (AOT)': (res('webserver_kestrel_aot.json'), 'src/WebServerBenchmark/cs/Program.cs'),
        }, versions, sort_by='rps'))

    # Proxy
    if 'proxy' in selected:
        header_proxy = [
            "| Proxy | Version | Reqs/sec (Avg ± Stdev) | Relative RPS | Latency (Avg ± Stdev) | Relative Latency | Throughput | Relative Throughput |",
            "|:---|:---|---:|---:|---:|---:|---:|---:|"
        ]
        content = replace_table(content, 'proxy', header_proxy, parse_bombardier({
            'Nginx': (res('proxy_nginx.json'), 'src/WebServerBenchmark/nginx/nginx.conf'),
            'YARP (JIT)': (res('proxy_yarp_jit.json'), 'src/WebServerBenchmark/cs/Program.cs'),
            'YARP (AOT)': (res('proxy_yarp_aot.json'), 'src/WebServerBenchmark/cs/Program.cs'),
        }, versions, sort_by='rps'))

    with open('README.md', 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update README.md benchmark tables from JSON results.")
    parser.add_argument(
        "--only",
        nargs="+",
        choices=SECTIONS,
        help="Update only the specified benchmark section(s) instead of all tables.",
    )
    args = parser.parse_args()
    update_readme(only=args.only)
    scope = ", ".join(args.only) if args.only else "all"
    print(f"README.md updated via anchors ({scope}).")
