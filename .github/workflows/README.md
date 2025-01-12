# GitHub Workflows

GitHub Actions workflows for the `certbot-regfish-hooks` repository.

Primary workflow(s):

- [`integration-test.yml`](/.github/workflows/integration-test.yml)
- [`pre-commit-hooks.yml`](/.github/workflows/pre-commit-hooks.yml)
- [`release-please.yml`](/.github/workflows/release-please.yml)
- _(more to come)_

## Integration Test

The workflow for integration test is intended to validate the package end-to-end by
requesting a certificate from the Let's Encrypt staging environment. This should act as
a smoke test to ensure that the package is working as expected before publishing a new
release.

![Integration Test Workflow Diagram](/assets/integration-test-workflow.png)

As depicted above, the integration test runs in two steps:

1. [Build Package](/.github/workflows/build-package.yml): Builds the package from the
   source code.
2. [Request Test Certificate](/.github/workflows/request-test-certificate.yml): Uses the
   built package to request a test certificate from the Let's Encrypt staging
   environment.

### Considerations

Let's Encrypt writes the following in their
[staging environment documentation](https://letsencrypt.org/docs/staging-environment/):

> The staging environment has generous rate limits to enable testing but it is not a
> great fit for integration with development environments or continuous integration
> (CI).

Hence, it's not optimal to run the integration test workflow on every commit. Currently,
it executes on push and merge events to the `main` branch. While this isn't problematic
due to low commit frequency, the workflow should be triggered more selectively (e.g.,
only on release tags) to respect Let's Encrypt's staging environment guidelines.

## Pre-Commit Hooks

But why? Max, it's called _pre-commit_ for a reason.

Yeah, about that... Too often I've encountered code that didn't pass all hooks after
checkout. Running _pre-commit_ hooks in CI helps catch these issues early and ensures
consistent code across all contributions.
