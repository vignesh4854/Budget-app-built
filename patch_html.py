"""Turns budget-splitter.html into www/index.html for the Android app.
Run automatically by the GitHub Action - no manual patching needed."""
import sys

SRC, DST = "budget-splitter.html", "www/index.html"
s = open(SRC, encoding="utf-8").read()

NEW_FN = '''  function downloadCopy() {
    var bytes = db.export();
    var cap = window.Capacitor;
    if (cap && cap.isNativePlatform && cap.isNativePlatform() && cap.registerPlugin) {
      /* Android app: WebViews ignore blob downloads, so write to cache and open the share sheet */
      var FS = cap.Plugins.Filesystem || cap.registerPlugin('Filesystem');
      var SH = cap.Plugins.Share || cap.registerPlugin('Share');
      var bin = '', CH = 0x8000;
      for (var i = 0; i < bytes.length; i += CH) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + CH));
      FS.writeFile({ path: 'budget.sqlite', data: btoa(bin), directory: 'CACHE' })
        .then(function (r) { return SH.share({ title: 'budget.sqlite', url: r.uri, dialogTitle: 'Save budget.sqlite' }); })
        .then(function () { setDataMsg('Choose Drive, Files or another app to keep budget.sqlite.'); })
        .catch(function (e) {
          if (e && /cancel/i.test(String(e.message || e))) return;
          setDataMsg('Could not export the database.', true);
        });
      return;
    }
    var blob = new Blob([bytes], { type: 'application/octet-stream' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'budget.sqlite';
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 5000);
    setDataMsg('Downloaded budget.sqlite. Keep it in the same folder as this page.');
  }
'''

def fail(msg):
    sys.exit("PATCH FAILED: " + msg)

if "function downloadCopy()" not in s:
    fail("function downloadCopy() not found in " + SRC + " - the app's download code was renamed. Ask Claude to update patch_html.py.")
start = s.index("function downloadCopy()")
start = s.rfind("\n", 0, start) + 1               # start of that line
end = s.find("async function reconnect()", start)
if end == -1:
    fail("async function reconnect() not found after downloadCopy - patch markers changed.")
end = s.rfind("\n", 0, end) + 1
s = s[:start] + NEW_FN + s[end:]

if "capacitor.js" not in s:
    i = s.find("<script>")
    if i == -1:
        fail("no <script> tag found")
    s = s[:i] + '<script src="capacitor.js"></script>\n' + s[i:]

import os
os.makedirs("www", exist_ok=True)
open(DST, "w", encoding="utf-8").write(s)
print("Patched %s -> %s (%d bytes)" % (SRC, DST, len(s)))
