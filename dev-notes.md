2026-06-14 Notes after first major commit in migration to python 3
===================================================================
With help from Antigravity, Gemini and Claude. 

Python 3 Migration — Complete for test/gold/
What passed
Test Suite	Tests	Status
test_state.py	41	✅ All pass
test_cmdline.py	3	✅ All pass
test_bb_read.py	36 (18 files × 2)	✅ All pass
test_bb_write.py	8	✅ All pass
Total	88	✅ 100%
Key changes made
2to3 — bulk syntax conversion across asynk/*.py (print, except, iteritems, metaclass, etc.)
Library replacements — demjson → demjson3, iso8601.tostring() → datetime.utcfromtimestamp().isoformat(), md5 → hashlib
string module — Replaced all deprecated string.replace(), string.strip(), string.upper(), string.lower() calls with str method equivalents
gdata removal — Removed unused atom/gdata imports from sync.py; guarded GC connector imports with try/except Exception in asynk_core.py and state_collection.py
Makefile — Updated to use venv python3 via PYTHON variable
Dependencies — Installed demjson3, iso8601, simplejson, vobject in venv
.gitignore — Added venv/
What's deferred
Google Contacts connector (*_gc.py) — needs People API migration
CardDAV connector (*_cd.py) — vendored caldavclientlibrary is Python 2; needs caldav package migration
Outlook connector (*_ol.py) — Windows-only, guarded