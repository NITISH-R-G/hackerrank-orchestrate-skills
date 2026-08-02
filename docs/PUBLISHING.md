# Publishing `orchestrate-kit` to PyPI

One-time setup, then every future release is just `git tag v1.x.x && git push --tags`.

## 1. Confirm the name is still available

```bash
curl -s https://pypi.org/pypi/orchestrate-kit/json
```

A `{"message": "Not Found"}` (HTTP 404) means the name is free — this is the
authoritative check. `pip index versions orchestrate-kit` agrees (errors
with "no matching distribution"), but don't trust a plain `curl` to
`pypi.org/project/<name>/` — PyPI's bot-protection layer can return a
"Client Challenge" page with HTTP 200 for a name that doesn't exist, which
looks like a false positive if you're just checking the status code. Both
of the checks above were run before writing this doc, and both currently
agree the name is free.

## 2. Create a PyPI account and an API token

1. https://pypi.org/account/register/ (use 2FA — PyPI requires it for
   publishing as of a few years back).
2. https://pypi.org/manage/account/token/ → **Add API token**.
   - Scope: for the *first* publish, scope must be **"Entire account"**
     (a project-scoped token can't be created until the project exists on
     PyPI). After the first publish, come back and create a
     **project-scoped** token for `orchestrate-kit` specifically, then
     delete the account-wide one — least privilege for every publish after
     the first.
3. Copy the token (`pypi-...`) — PyPI shows it exactly once.

## 3. Add it as a GitHub Actions secret

```bash
gh secret set PYPI_API_TOKEN --repo NITISH-R-G/hackerrank-orchestrate-skills
# paste the pypi-... token when prompted
```

Or via the UI: repo → Settings → Secrets and variables → Actions → New
repository secret → name `PYPI_API_TOKEN`.

**Never paste the token into a commit, an issue, or this chat.** The
release workflow (`.github/workflows/release.yml`) reads it only from
`secrets.PYPI_API_TOKEN` — it is never logged or echoed.

## 4. Cut the first release

```bash
git tag v1.0.0
git push origin v1.0.0
```

This triggers `release.yml`, which — on this exact tagged commit — re-runs
the full test suite, `selftest`, and the example plugin's tests; builds the
sdist and wheel; runs `twine check`; verifies the wheel actually contains
the packaged seed data; verifies install into a clean venv with zero repo
context; attaches both artifacts to a GitHub Release; and **only then**
uploads to PyPI, using the token from step 3.

If `PYPI_API_TOKEN` isn't set, that last step prints a message and exits 0
— the release still gets verified and attached to GitHub either way.

## 5. Verify it actually worked

Don't trust the green checkmark — install it for real, the way any user
would, from a completely fresh environment:

```bash
python -m venv /tmp/pypi_verify
/tmp/pypi_verify/bin/pip install orchestrate-kit
/tmp/pypi_verify/bin/python -m orchestrate_kit memory why-not "embeddings"
```

If that prints the `D-dense-retrieval` entry from a directory with no repo
checkout present, the publish is real, not just "the workflow said success."

## 6. Every release after the first

```bash
# bump the version in BOTH places -- nothing currently keeps them in sync
# automatically, which is a real, known gap; see ROADMAP.md
$EDITOR pyproject.toml        # version = "1.x.x"
$EDITOR orchestrate_kit/__init__.py   # __version__ = "1.x.x"

git add pyproject.toml orchestrate_kit/__init__.py
git commit -m "Bump version to 1.x.x"
git tag v1.x.x
git push origin master v1.x.x
```

Update `CHANGELOG.md`'s `[Unreleased]` section into a new dated `[1.x.x]`
section before tagging — the changelog should describe what's actually in
the tag, not lag behind it.
