# Contributing

[fork]: https://github.com/IBM/risk-atlas-nexus/fork
[pr]: https://github.com/IBM/risk-atlas-nexus/compare
[released]: https://help.github.com/articles/github-terms-of-service/

We are pleased that you would like to contribute to Risk Atlas Nexus. We welcome both reporting issues and submitting pull requests.

## Reporting issues
Please make sure to include any potentially useful information in the issue, so we can pinpoint the issue faster without going back and forth.

- What SHA of Risk atlas nexus are you running? If this is not the latest SHA on the main branch, please try if the problem persists with the latest version.
- Python versions
- TBC

## Contributing a change
Contributions to this project are [released][released] to the public under the project's [opensource license](https://github.com/IBM/risk-atlas-nexus/blob/main/LICENSE).

Contributors must _sign off_ that they adhere to these requirements by adding a `Signed-off-by` line to all commit messages with an email address that matches the commit author:

```
feat: this is my commit message

Signed-off-by: Random J Developer <random@developer.example.org>
```


Coding Style Guidelines
We are using tools to enforce code style:
- iSort, to sort imports
- Black, to format code

We run a series of checks on the codebase on every commit using pre-commit. To install the hooks, run:
`pre-commit install`

To run the checks on-demand, run:
`pre-commit run --all-files`

## Secret scanning
This repository uses IBM's [detect-secrets](https://github.com/ibm/detect-secrets) to scan for secrets before the code is pushed to GitHub. Follow installation instructions in their repository: https://github.com/ibm/detect-secrets?tab=readme-ov-file#example-usage

To update the secrets database manually, run:
```
detect-secrets scan --update .secrets.baseline
```
To audit detected secrets, use:
```
detect-secrets audit .secrets.baseline
```
If the pre-commit hook raises an error but the audit command succeeds with just `Nothing to audit!` then run `detect-secrets scan --update .secrets.baseline` to perform a full scan and then repeat the audit command.


## Contributing to documentation
`pip install -e ".[docs]"`

We use [MkDocs](https://www.mkdocs.org/) to write documentation.

To build documentation, run
```bash
JUPYTER_PLATFORM_DIRS=1 mkdocs build
```
To run the documentation server, run:

```bash
JUPYTER_PLATFORM_DIRS=1 mkdocs serve
```

The server will be available at [http://localhost:8000](http://localhost:8000).

### Pushing Documentation to GitHub Pages

Run the following:

```bash
mkdocs gh-deploy
```


## Submitting a pull request

1. [Fork][fork] and clone the repository
2. Create a new branch: `git checkout -b my-branch-name`
3. Make your change, push to your fork and [submit a pull request][pr]
4. Wait for your pull request to be reviewed and merged.
