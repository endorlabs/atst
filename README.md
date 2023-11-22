# endorlabs-atst
A Python-based tool to help deploy, run, and manage Endor Labs in your CI pipeline

## Quick start

See example [GitHub Action worfklow](.github/workflows/example-use-main.yml) and [GitLab CI config](.gitlab-ci.yml).

**Note:** if  using GitHub Actions, you're probably better off with the [Endor Labs GitHub Action](https://github.com/marketplace/actions/endor-labs-scan)) instead

1. Make sure you have Python3, PIP, and the venv package installed in your runner
2. In your setup section, install this package with `python3 -m venv ../.atst ; ../.atst/bin/python3 -m pip -q install endorlabs-atst`
3. Configure your environment for an Endor Labs scan -- see [Endor Labs scan flags and variables documentation](https://docs.api.endorlabs.com/endorctl/environment-variables/#endorctl-scan-flags-and-variables)
4. When you've build your project and are ready to test with Endor labs, use `../.atst/bin/endorlabs-atst ctl -- scan` and add any `endorctl` options you require -- note the freestanding `--`; this separates options for ATST from options for `endorctl`

Remember to configure your scan environment variables and authentication as [the Endor Labs Documentation](https://docs.api.endorlabs.com) explains.

## Pinning and verifying endorctl versions

```
endorlabs-atst setup --endorlabs-version VERSION [--endorlabs-sha256sum SHA256_SUM]
endorlabs-atst ctl -- scan
```

AT-ST by default installs the latest version (unless there's already an `endorctl` of the current minor version installed) and verifies it using the SHA256 data provided by the Endor Labs API. However, you can pin a particular version of endorctl as well by running the `setup` subcommand and providing the option `--endorlabs-version`

When specifying a pinned version, the SHA256 digest used for verification is loaded from this module rather than the API. Because this internal database is only updated when AT-ST is updated, recent version digests may not be available. You have the option of specifying the SHA256 digest to use (using `--endorlabs-sah256sum` option) yourself -- if no digest is available, verification will be skipped with a warning.

Note that a provided SHA256 hash will always override cached or API-derived values.

For example, when downloading version 1.6.8 for macOS on Arm64, one might:

```bash
endorlabs-atst setup --endorlabs-version 1.6.8 --endorlabs-sha256sum e4ffa898606e53b78925e4618f095641c52b21d57522d9aa965db8aef1f5f4f1
```

In all cases, if there is no SHA256 data available, ATST will warn you of this and proceed; while if SHA256 data is available and does not match the `endorctl` that ATST downloads, ATST will terminate with an error.
