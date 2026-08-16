"""Generate JSON and HTML performance reports from benchmark results."""
import json, os
from datetime import datetime, timezone

WARN_MS = 50.0
FAIL_MS = 200.0


def generate_report(results, output_dir="benchmark_results", fmt="both"):
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    base = os.path.join(output_dir, f"benchmark_report_{ts}")
    written = []
    if fmt in ("json", "both"):
        path = f"{base}.json"
        with open(path, "w") as f:
            json.dump({"generated_at": ts, "suites": results,
                       "summary": _summary(results)}, f, indent=2)
        written.append(path)
    if fmt in ("html", "both"):
        path = f"{base}.html"
        with open(path, "w") as f:
            f.write(_html(results, ts))
        written.append(path)
    return written


def _summary(results):
    total = errors = 0; slowest = {}; slow_ms = -1
    for s in results:
        if s.get("error"): errors += 1; continue
        for b in s.get("benchmarks", []):
            total += 1
            if b.get("error"): errors += 1; continue
            if b.get("mean_ms", 0) > slow_ms:
                slow_ms = b["mean_ms"]; slowest = {"name": b["name"], "mean_ms": slow_ms}
    return {"total_benchmarks": total, "total_errors": errors, "slowest": slowest}


def _badge(ms):
    if ms >= FAIL_MS: return "🔴 SLOW"
    if ms >= WARN_MS: return "🟡 WARN"
    return "🟢 OK"


def _html(results, ts):
    rows = ""
    for s in results:
        rows += f"<tr><td colspan='8' style='background:#e8f5e9;font-weight:bold'>{s['suite']}</td></tr>\n"
        if s.get("error"):
            rows += f"<tr><td colspan='8' style='color:red'>ERROR: {s['error']}</td></tr>\n"
            continue
        for b in s.get("benchmarks", []):
            if b.get("error"):
                rows += f"<tr><td>{b['name']}</td><td colspan='7' style='color:red'>{b['error']}</td></tr>\n"
                continue
            m = b.get("mean_ms", 0)
            bg = "#ffebee" if m >= FAIL_MS else "#fff9c4" if m >= WARN_MS else ""
            rows += (f"<tr style='background:{bg}'>"
                     f"<td>{b['name']}</td><td>{b['iterations']}</td>"
                     f"<td>{b['min_ms']}ms</td><td>{b['max_ms']}ms</td>"
                     f"<td><b>{m}ms</b></td><td>{b['median_ms']}ms</td>"
                     f"<td>{b['stdev_ms']}ms</td><td>{b['peak_memory_kb']}KB</td>"
                     f"<td>{_badge(m)}</td></tr>\n")
    sm = _summary(results)
    return f"""<!DOCTYPE html><html><head><meta charset='UTF-8'>
<title>EcoBuddy Benchmark Report</title>
<style>body{{font-family:sans-serif;margin:24px}}table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ddd;padding:6px 10px;font-size:.82em}}
th{{background:#2e7d32;color:#fff}}tr:nth-child(even){{background:#f9f9f9}}</style></head>
<body>
<h2>🌿 EcoBuddy AI – Benchmark Report</h2>
<p>Generated: {ts} UTC &nbsp;|&nbsp;
   Benchmarks: {sm['total_benchmarks']} &nbsp;|&nbsp;
   Errors: {sm['total_errors']} &nbsp;|&nbsp;
   Slowest: {sm['slowest'].get('name','–')} ({sm['slowest'].get('mean_ms',0):.2f}ms)</p>
<table><thead><tr>
<th>Benchmark</th><th>Iters</th><th>Min</th><th>Max</th>
<th>Mean</th><th>Median</th><th>StdDev</th><th>Peak Mem</th><th>Status</th>
</tr></thead><tbody>
{rows}</tbody></table>
<p style='font-size:.75em;color:#888'>🟢 OK &lt;{WARN_MS:.0f}ms &nbsp; 🟡 WARN {WARN_MS:.0f}–{FAIL_MS:.0f}ms &nbsp; 🔴 SLOW &gt;{FAIL_MS:.0f}ms</p>
</body></html>"""
