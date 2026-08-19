import pathlib, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = pathlib.Path("extension/content/save.js"); t = p.read_text(encoding="utf-8")
before = t
# Σπάμε και στις τελείες, ώστε η πρόταση «Ζητείται …» να γίνει δική της γραμμή
t = re.sub(r'text\.split\(/\[[^\]]*\]/\)', r'text.split(/[\n·|]|(?<=[.!?])\s+/)', t, count=1)
assert t != before, "δεν άλλαξε το split"
p.write_text(t, encoding="utf-8")
m = re.search(r'const lines = .*', t)
print("  " + m.group(0))
