import pathlib, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = pathlib.Path("extension/content/save.js"); t = p.read_text(encoding="utf-8")
old = "    return { title: title.slice(0, 120), email };"
new = ("    // Οι αναρτήσεις ξεκινούν με χρονόσημο («3 ώρες», «2h», «πριν 5 λεπτά»)·" + chr(10) +
       "    // δεν είναι μέρος του τίτλου." + chr(10) +
       "    const clean = title" + chr(10) +
       "      .replace(/^(πριν\\s+)?\\d+\\s*(ώρ\\w*|λεπτ\\w*|ημέρ\\w*|h|hr|hrs|m|min|d|days?)\\b\\s*/i, \\"\\")" + chr(10) +
       "      .replace(/^[-–—:·,\\s]+/, \\"\\")" + chr(10) +
       "      .trim();" + chr(10) +
       "    return { title: clean.slice(0, 120), email };")
assert old in t
p.write_text(t.replace(old, new, 1), encoding="utf-8")
print("  save.js: αφαίρεση χρονοσήμου ✓")
