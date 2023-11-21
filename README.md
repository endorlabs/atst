# endorlabs-atst
A Python-based tool to help deploy, run, and manage Endor Labs in your CI pipeline

Examples of how to use this tool are provided in:

- [example-use-main.yml](.github/workflows/example-use-main.yml) -- GitHub Actions workflow example (note: you probably would be better off with the [Endor Labs GitHub Action](https://github.com/marketplace/actions/endor-labs-scan))
- [.gitlab-ci.yml](.gitlab-ci.yml) -- GitLab CI example

## Quick start

See example [GitHub Action worfklow](.github/workflows/example-use-main.yml) and [GitLab CI config](.gitlab-ci.yml).

1. Make sure you have Python3, PIP, and the venv package installed in your runner
2. In your setup section, install this package with `python3 -m venv ../.atst ; ../.atst/bin/python3 -m pip -q install endorlabs-atst`
3. Ensure your Endor Labs environment is established; setting `ENDOR_NAMESPACE` and any authentication configuration required (in some CI environments, `setup` can do this for you; see "**Automatic CI Setup**" below)
4. Run `../.atst/bin/endorlabs-atst setup`
5. When you've build your project and are ready to test with Endor labs, use `../.atst/bin/endorlabs-atst ctl -- scan` and add any `endorctl` options you require

Remember to configure your scan environment variables and authentication as [the Endor Labs Documentation](https://docs.api.endorlabs.com) explains.

## Pinning and verifying endorctl versions

`endorlabs-atst setup` by default installs the latest version (unless there's already an `endorctl` of the current minor version installed) and verifies it using the SHA256 data provided by the Endor Labs API. However, you can pin a particular version of endorctl as well by providing the option `--endorlabs-version`

When specifying a version, you also have the option of specifying a SHA256 hash of the binary you expect for your OS and architecture (using `--endorlabs-sah256sum` option), so that ATST can verify the download. If you do not provide this, ATST will attempt to look one up from its cache of known versions; however, this cache is only updated when ATST is changed, so recent versions may not exist.

Note that a provided SHA256 hash will always override cached or API-derived values

For example, when downloading version 1.6.8 for macOS on Arm64, one might:

```bash
endorlabs-atst setup --endorlabs-version 1.6.8 --endorlabs-sha256sum e4ffa898606e53b78925e4618f095641c52b21d57522d9aa965db8aef1f5f4f1
```

In all cases, if there is no SHA256 data available, ATST will warn you of this and proceed; while if SHA256 data is available and does not match the `endorctl` that ATST downloads, ATST will terminate with an error.

## Automatic CI setup

***NB:*** *currently only available in GitHub Actions CI workflow environments*

For supported CI systems, you don't need to pre-set your Endor Labs environment variables for auth and namespace before running `endorlabs-atst`, so long as you provide the data as command-line options when you run `endorlabs-atst setup`:

```bash
../.atst/bin/endorlabs-atst setup --namespace MY_NAMESPACE --auth api:API_KEY:API_SECRET --endorlabs-version latest
```

Will (for GitHub only, currently):

1. set the `PATH` to include `../.atst/bin`, so you can run future ATST or `endorctl` invocations without a full path
2. set the `ENDOR_NAMESPACE` environment variable
3. set the appropriate Endor Labs authentication environment variables

This is designe to make testing and setup faster, however for production deployments we recommend configuring environment variables and secrets using your CI configuration system -- it's more maintainable
