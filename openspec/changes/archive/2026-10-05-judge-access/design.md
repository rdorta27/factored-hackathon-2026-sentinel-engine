---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Design

## Decisions

| Topic | Choice | Reason |
|---|---|---|
| Separate flag | `SENTINEL_DEMO_PERSONAS`, default follows `SENTINEL_DEMO_AUTH` | `SENTINEL_DEMO_AUTH` also loads the advisor role. The public link needs the advisor and no one-click entry. The default keeps `test_demo_auth.py` green |
| Users file | `SENTINEL_USERS_PATH` on the Azure Files share | The app already reads this variable. The file holds salted hashes only |
| Accounts | One login for each customer of the personas (CUST-0001, CUST-0002, CUST-0003) and one advisor | The persona map uses these three customers. The normal and the ambiguous cases share one customer and differ by locale |
| Judge set | One shared set for all judges (owner decision, 2026-10-05) | It is simple to send. The judges share the state of the cases. The email says so |
| Passwords | Random, written by a script, never committed | The repository is public |
| Where the passwords go | The submission email only | The slides and the video are public. The video must not show a password |
| Banner | Driven by `gold_source` from `/health` | The notice must show when the one-click entry is off |
| Lockout | Keep the existing one (HTTP 429 after repeated failures) | It protects a public password form. The email states the rule so a judge does not lock out by mistake |

## Risks

| Risk | Control |
|---|---|
| A judge loses the email | The email repeats the logins. The sheet is kept by the owner |
| A judge changes the state that another judge sees | The email says that the accounts are shared. The state reset (post-freeze 4.4) clears it before the entry |
| Judges lock an account with wrong tries | The email states the lockout rule. A redeploy clears sessions only if the state is reset |
| The fixture password still works on the link | Task 4.2 tests it after the final redeploy |
| The change lands late | Work before gate G3. The redeploy is in `post-freeze` |
