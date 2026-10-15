import os, subprocess, threading, time, psutil, json, sys, urllib.request
env = dict(os.environ, PORT="8080", PDFTEXT_CONCURRENCY=sys.argv[1] if len(sys.argv)>1 else "2")
env.pop("PDFTEXT_ALLOW_CIDRS", None)
cmd = ".venv/bin/uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1 --no-access-log"
p = subprocess.Popen(["sh", "-c", "exec " + cmd], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
peak = {"v": 0, "py": 0}; stop = False
def sample():
    while not stop:
        try:
            pr = psutil.Process(p.pid); procs = [pr] + pr.children(recursive=True)
            tot = sum(x.memory_info().rss for x in procs if x.is_running())
            peak["v"] = max(peak["v"], tot); peak["py"] = max(peak["py"], pr.memory_info().rss)
        except psutil.Error: pass
        time.sleep(0.01)
threading.Thread(target=sample, daemon=True).start()
B = "http://127.0.0.1:8080"
for _ in range(50):
    try: urllib.request.urlopen(B + "/health", timeout=1); break
    except Exception: time.sleep(0.2)
def phase(name, fn):
    peak["v"] = peak["py"] = 0; t = time.time(); out = fn(); time.sleep(0.1)
    print(f"{name:28s} peak_tree={peak['v']/2**20:6.1f}MB peak_python={peak['py']/2**20:6.1f}MB {time.time()-t:5.2f}s {out}")
def up(path, *f):
    a = ["curl", "-s", "-F", f"file=@{path}"] + sum([["-F", x] for x in f], []) + [B + "/v1/extract/upload"]
    j = json.loads(subprocess.run(a, capture_output=True).stdout); return f"ocrPages={j.get('ocrPages')} text={j.get('text','')[:30]!r} err={j.get('error')}"
time.sleep(1)
phase("idle (after start)", lambda: urllib.request.urlopen(B + "/health").read()[:40])
phase("text PDF + CSV tables", lambda: up("tests/samples/text_table.pdf", "tableFormat=csv"))
phase("scanned eng OCR", lambda: up("tests/samples/scanned.pdf"))
phase("scanned chi_sim+eng OCR", lambda: up("tests/samples/scanned_chi_sim.pdf", "ocrLanguages=chi_sim+eng"))
phase("fw9 6p ocr=always (5 cap)", lambda: up("/tmp/fw9.pdf", "ocr=always", "tableFormat=both"))
phase("fw9 jpn+chi_sim+eng always", lambda: up("/tmp/fw9.pdf", "ocr=always", "ocrLanguages=jpn+chi_sim+eng"))
def par():
    ts = [threading.Thread(target=up, args=("/tmp/fw9.pdf", "ocr=always", "ocrLanguages=chi_sim+eng")) for _ in range(2)]
    [t.start() for t in ts]; [t.join() for t in ts]; return "2 parallel"
phase("2x parallel fw9 chi_sim OCR", par)
stop = True; p.terminate(); p.wait()
