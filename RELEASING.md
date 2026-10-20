# Releasing Visualific

Releases are published by the `release` workflow in `.github/workflows/release.yml` when a version tag is pushed. It uses PyPI Trusted Publishing, so no API token is stored in the repository or in GitHub secrets.

## One-time setup (maintainer only)

1. Create accounts on [PyPI](https://pypi.org/account/register/) and [TestPyPI](https://test.pypi.org/account/register/), and turn on two-factor authentication on both.
2. On TestPyPI, add a pending trusted publisher at <https://test.pypi.org/manage/account/publishing/>:
   - PyPI project name: `visualific`
   - owner: `arshahvaran`
   - repository: `visualific`
   - workflow: `release.yml`
   - environment: `testpypi`
3. In the GitHub repository settings, create two environments named `pypi` and `testpypi`:
   - For both, set *Deployment branches and tags* to *Selected branches and tags* and add a **tag** rule `v*`.
   - On `pypi`, add yourself as a required reviewer, so that every PyPI upload waits for your approval. Leave *Prevent self-review* unticked, or you could not approve your own release.
4. Under *Settings → Rules → Rulesets*, add a tag ruleset for `v*` that restricts creating, updating and deleting matching tags, with repository admins allowed to bypass it.
5. Sign in to [Zenodo](https://zenodo.org) with GitHub, open <https://zenodo.org/account/settings/github/>, press *Sync now* and switch on `visualific`. Do this before the first final release. Each GitHub release then gets a DOI. Zenodo reads `CITATION.cff`; do not add a `.zenodo.json`, because Zenodo would then ignore `CITATION.cff`. After the first archive, add the concept DOI to `CITATION.cff` and the README.

The PyPI publisher is added later (step 4 below), because a pending publisher does not reserve the project name and pre-releases only go to TestPyPI.

## Each release

1. Set the same version in `src/visualific/__init__.py` and `CITATION.cff`, for example `0.1.0rc1`, and move the "Unreleased" notes in `CHANGELOG.md` under the new version with the date. Commit and push to `main`.
2. Tag the release candidate and push the tag:

   ```bash
   git tag v0.1.0rc1
   git push origin v0.1.0rc1
   ```

   The workflow checks that the tag matches the version, builds and tests the wheel, and publishes it to TestPyPI.
3. Try the candidate in a fresh environment (in Colab, put `%` before `pip`). Install Visualific alone from TestPyPI, then its dependencies from PyPI only:

   ```bash
   pip install --no-deps -i https://test.pypi.org/simple/ visualific==0.1.0rc1
   pip install visualific==0.1.0rc1
   ```

4. Before the first final release only: check that <https://pypi.org/project/visualific/> does not exist yet, then add the PyPI pending publisher at <https://pypi.org/manage/account/publishing/> with the same fields as in setup step 2, but environment `pypi`.
5. Set the final version (`0.1.0`) in `src/visualific/__init__.py` and `CITATION.cff`, commit and push to `main`, then tag `v0.1.0` and push the tag. Approve the `pypi` deployment in the Actions tab when it asks. The workflow then publishes to PyPI and creates the GitHub release.

Never delete a release from PyPI. If a release is broken, publish a fixed one with a higher version number.
