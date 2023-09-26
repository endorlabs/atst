# endorlabs-atst
A Python-based tool to help deploy, run, and manage Endor Labs in your CI pipeline

Examples of how to use this tool are provided in:

- [example-use-main.yml](.github/workflows/example-use-main.yml) -- GitHub Actions workflow example (note: you probably would be better off with the [Endor Labs GitHub Action](https://github.com/marketplace/actions/endor-labs-scan))
- [.gitlab-ci.yml](.gitlab-ci.yml) -- GitLab CI example

## Quick start

1. Make sure you have Python3, PIP, and the venv package installed in your runner
2. In your CI's setup (e.g. `before_script`) section, install this package with `python3 -m venv ../.atst ; ../.atst/bin/python3 -m pip -q install git+https://github.com/endorlabs/atst@main`
3. Run `../.atst/bin/endorlabs-atst setup --namespace NAMESPACE --auth AUTH_STRING` (see `--help` for information)
    - if you see `INFO  Running in Unknown CI or non-CI` message, we won't know how to set up the environment. You'll have to set your namespace and authentication data manually in your CI environment. See [the Endor Labs Documentation](https://docs.api.endorlabs.com) for details.
4. When you've build your project and are ready to test with Endor labs, use `../.atst/bin/endorlabs-atst ctl -- scan` and add any `endorctl` options you require

Remember to configure your scan environment variables and authentication as [the Endor Labs Documentation](https://docs.api.endorlabs.com) explains.

Here's an example of a script for setting everything up:

```bash
#!/usr/bin/env bash
set -e  # immediately exit if any command fails
python3 -m venv ../.atst
../.atst/bin/python3 -m pip -q install git+https://github.com/endorlabs/atst@main
../.atst/bin/endorlabs-atst setup --namespace $ENDOR_NAMESPACE --auth api:API_KEY:API_SECRET
```