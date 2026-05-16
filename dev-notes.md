2026-05-15 00:30am
==================

**Phase 3 Complete ✅**
All three *_gc.py files have been migrated:

| Phase | File | Status |
|---|---|---|
| Phase 1 | pimdb_gc.py — Auth + Groups | ✅ Done |
| Phase 2 | folder_gc.py — Folder operations | ✅ Done |
| Phase 3 | contact_gc.py — Contact model | ✅ Done |

**Test results:**

- 88 core tests: ✅
- 9 GC integration tests: ✅

**What remains (from the original plan):**

- Phase 4: Testing — Add more integration tests (list contacts, create/update/delete a contact via the API)
- Phase 5: Cleanup — Remove remaining try/except import guards in asynk_core.py and state_collection.py, final integration verification


2026-05-14 9pm Phase 1
====================

**Phase 1 complete and committed.**

**Summary**
Phase 1: Auth + Groups rewrite for pimdb_gc.py — Done:

| What | Old (GData) | New (People API) |
|---|---|---|
| Auth | oauth2client + custom webserver on port 1977 | InstalledAppFlow.run_local_server(port=0) |
| Token storage | oauth2client.file.Storage → .dat file | pickle → .token.pickle file |
| API client | gdata.contacts.client.ContactsClient | build('people', 'v1', credentials=creds) |
| List groups | GetGroups() → XML feed | contactGroups().list() → JSON |
| Create group | create_group(GroupEntry) | contactGroups().create(body={...}) |
| Delete group | delete_group(entry) | contactGroups().delete(resourceName=...) |
| Default folder | Match 'System Group: My Contacts' | Match 'contactGroups/myContacts' |
| Batch feeds | new_feed() + exec_batch() | NotImplementedError (People API uses different batch mechanics — will be in folder_gc.py) |

Removed: MyAuthToken, patched_post(), _oauth_dance(), _init_webserver(), all atom/gdata imports.

Next up: Phase 2 — rewrite folder_gc.py for People API contact operations (list, get, batch create/update/delete).

2026-05-14 5:30pm Phase 0 complete and committed. ✅
==========================================================

**Summary**

Phase 0: Dependencies & Scaffolding — Done:

- ✅ Removed lib/.gdata/ (vendored tree) + lib/atom and lib/gdata symlinks
- ✅ Cleaned up stale backup files (demjson.py.bak, iso8601.py.bak, lib/s/)
- ✅ Installed google-api-python-client, google-auth-httplib2, google-auth-oauthlib in venv
- ✅ Verified from googleapiclient.discovery import build works
- ✅ Updated requirements.txt with all direct dependencies
- ✅ All 88 test/gold/ tests still pass
- ✅ Committed to python3 branch

Ready to proceed with Phase 1 (Auth rewrite) whenever you are. That phase will rewrite pimdb_gc.py to use InstalledAppFlow + build('people', 'v1') instead of oauth2client + gdata.contacts.client.ContactsClient.


2026-06-14 Notes after first major commit in migration to python 3
===================================================================
With help from Antigravity, Gemini and Claude. 

**Python 3 Migration — Complete for test/gold/**

**What passed***
| Test Suite | Tests | Status |
|---|---|---|
| test_state.py | 41 | ✅ All pass |
| test_cmdline.py | 3 | ✅ All pass |
| test_bb_read.py | 36 (18 files × 2) | ✅ All pass |
| test_bb_write.py | 8 | ✅ All pass |
| **Total** | **88** | **✅ 100%** |
Key changes made
- **2to3** — bulk syntax conversion across asynk/*.py (print, except, iteritems, metaclass, etc.)
- **Library replacements** — demjson → demjson3, iso8601.tostring() → datetime.utcfromtimestamp().isoformat(), md5 → hashlib
- **string module** — Replaced all deprecated string.replace(), string.strip(), string.upper(), string.lower() calls with str method equivalents
- **gdata removal** — Removed unused atom/gdata imports from sync.py; guarded GC connector imports with try/except Exception in asynk_core.py and state_collection.py
- **Makefile** — Updated to use venv python3 via PYTHON variable
- **Dependencies** — Installed demjson3, iso8601, simplejson, vobject in venv
- **.gitignore** — Added venv/

**What's deferred**
- **Google Contacts connector** (*_gc.py) — needs People API migration
- **CardDAV connector** (*_cd.py) — vendored caldavclientlibrary is Python 2; needs caldav package migration
- **Outlook connector** (*_ol.py) — Windows-only, guarded