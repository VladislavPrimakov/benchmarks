import json
import re

def parse_hyperfine(json_path):
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    results = data['results']
    min_mean = min(r['mean'] for r in results)
    
    rows = []
    sorted_results = sorted(results, key=lambda x: x['mean'])
    
    for r in sorted_results:
        mean = r['mean']
        stddev = r['stddev']
        min_val = r['min']
        max_val = r['max']
        relative = mean / min_mean
        
        if mean > 1:
            rows.append(f"| `{r['command']}` | {mean:.3f} ± {stddev:.3f} | {min_val:.3f} | {max_val:.3f} | {relative:.2f} ± {stddev/mean*relative:.2f} |")
        else:
            rows.append(f"| `{r['command']}` | {mean*1000:.1f} ± {stddev*1000:.1f} | {min_val*1000:.1f} | {max_val*1000:.1f} | {relative:.2f} ± {stddev/mean*relative:.2f} |")
            
    return rows

def parse_bombardier(json_paths_map):
    parsed = []
    for label, path in json_paths_map.items():
        with open(path, 'r') as f:
            data = json.load(f)
        res = data['result']
        parsed.append({
            'label': label,
            'rps': res['rps']['mean'],
            'rps_std': res['rps']['stddev'],
            'lat': res['latency']['mean'] / 1000,
            'lat_std': res['latency']['stddev'] / 1000,
            'throughput': res['bytesRead'] / (1024 * 1024 * res['timeTakenSeconds'])
        })
    
    max_rps = max(p['rps'] for p in parsed)
    min_lat = min(p['lat'] for p in parsed)
    max_tp = max(p['throughput'] for p in parsed)
    
    rows = []
    for p in parsed:
        rows.append(f"| **{p['label']}** | {p['rps']:.2f} ± {p['rps_std']:.2f} | {p['rps']/max_rps:.2f}x | {p['lat']:.2f} ± {p['lat_std']:.2f} ms | {p['lat']/min_lat:.2f}x | {p['throughput']:.2f} MB/s | {p['throughput']/max_tp:.2f}x |")
    return rows

def replace_table(content, tag, new_lines):
    pattern = re.compile(rf"<!-- TABLE_START: {tag} -->(.*?)<!-- TABLE_END: {tag} -->", re.DOTALL)
    new_content = "\n".join(new_lines)
    replacement = f"<!-- TABLE_START: {tag} -->\n{new_content}\n<!-- TABLE_END: {tag} -->"
    return pattern.sub(replacement, content)

def update_readme():
    with open('README.md', 'r', encoding='utf-8') as f:
        content = f.read()

    # Prime
    header_prime = ["| Language | Mean [ms] | Min [ms] | Max [ms] | Relative |", "| :------- | ----------: | -------: | -------: | ----------: |"]
    content = replace_table(content, 'prime', header_prime + parse_hyperfine('results/prime_results.json'))

    # Regex
    header_regex = ["| Language | Mean [s] | Min [s] | Max [s] | Relative |", "| :------- | ------------: | ------: | ------: | ----------: |"]
    content = replace_table(content, 'regex', header_regex + parse_hyperfine('results/regex_results.json'))
    
    # String
    header_string = ["| Language | Mean [s] | Min [s] | Max [s] | Relative |", "| :------- | ------------: | ------: | ------: | ----------: |"]
    content = replace_table(content, 'string', header_string + parse_hyperfine('results/string_concat_results.json'))

    # WebServer
    header_web = ["| Server | Reqs/sec (Avg ± Stdev) | Relative RPS | Latency (Avg ± Stdev) | Relative Latency | Throughput | Relative Throughput |", "|:---|---:|---:|---:|---:|---:|---:|"]
    content = replace_table(content, 'webserver', header_web + parse_bombardier({'Kestrel (epoll)': 'results/kestrel_results.json', 'Zerg (io_uring)': 'results/zerg_results.json'}))

    # Proxy
    header_proxy = ["| Proxy | Reqs/sec (Avg ± Stdev) | Relative RPS | Latency (Avg ± Stdev) | Relative Latency | Throughput | Relative Throughput |", "|:---|---:|---:|---:|---:|---:|---:|"]
    content = replace_table(content, 'proxy', header_proxy + parse_bombardier({'Nginx': 'results/nginx_results.json', 'YARP (C#)': 'results/yarp_results.json'}))
    
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    update_readme()
    print("README.md updated via anchors.")
