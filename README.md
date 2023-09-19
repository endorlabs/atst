# endorlabs-atst
A Python-based tool to help deploy, run, and manage Endor Labs in your CI pipeline

Examples of how to use this tool are provided in:

- [example-use-main.yml](.github/workflows/example-use-main.yml) -- GitHub Actions workflow example (note: you probably would be better off with the [Endor Labs GitHub Action](https://github.com/marketplace/actions/endor-labs-scan))
- [.gitlab-ci.yml](.gitlab-ci.yml) -- GitLab CI example

## Quick start

1. Make sure you have Python3, PIP, and the venv package installed in your runner
2. In your setup section, install this package with `python3 -m venv ../.atst ; ../.atst/bin/python3 -m pip -q install git+https://github.com/endorlabs/atst@main`
3. Run `../.atst/bin/endorlabs-atst setup`
4. When you've build your project and are ready to test with Endor labs, use `../.atst/bin/endorlabs-atst ctl -- scan` and add any `endorctl` options you require

Remember to configure your scan environment variables and authentication as [the Endor Labs Documentation](https://docs.api.endorlabs.com) explains.