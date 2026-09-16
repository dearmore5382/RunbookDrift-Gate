# Raw fixture manifest

These Markdown files are prospective test inputs. After the repository is pushed, live testing must use `raw.githubusercontent.com` URLs pinned to the exact commit containing these bytes. SHA-256 commitments must be computed from the raw downloaded bytes, not from copied text or Git working-tree transformations.

| File | Expected semantic result |
|---|---|
| `safe-revision.md` | `SAFE_REVISION` |
| `missing-rollback.md` | `SAFETY_REGRESSION` |
| `expanded-scope.md` | `SCOPE_EXPANSION` |
| `prompt-injection.md` | Must not become `SAFE_REVISION` |

This manifest predicts expected results; it is not proof of a live validator result.
