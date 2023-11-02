# Endor Labs Automated Tool for Scanning Things (ATST)

*For use by Endor Labs customers and authorized users*

Simplify deployment of Endor Labs into your CI.

## Quick Start

In your CI, set your namespace and auth variables per Endor Labs docs and:

```zsh
python3 -m venv ../.atst
../.atst/bin/python3 -m pip install endorlabs-atst
../.atst/bin/endorlabs-atst setup
../.atst/bin/endorctl scan [OPTIIONS]
```

See [endorlabs/atst on GitHub](https://github.com/endorlabs/atst) for more details