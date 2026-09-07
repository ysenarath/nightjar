# Building the docs

The site uses [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
and [mkdocstrings](https://mkdocstrings.github.io/python/usage/) to render API
documentation from the source docstrings.

From the repository root, start a local preview:

```bash
uv run --group docs mkdocs serve
```

Open the local URL printed by MkDocs. Changes to Markdown and source docstrings
trigger a rebuild.

Build the site with warnings treated as errors:

```bash
uv run --group docs mkdocs build --strict
```

The output is written to `site/`, which is ignored by Git. These commands build
or preview locally; they do not publish the site. Equivalent Makefile targets
are `make docs` and `make docs-build`.

Edit `mkdocs.yml` to change navigation or theme settings. Guide pages live in
`docs/`; API reference pages use `:::` directives to select source objects.
Keep examples compatible with Python 3.9 and both supported Pydantic versions.

## GitHub Pages

In the repository's **Settings → Pages → Build and deployment**, select
**GitHub Actions** as the source. Push to `main` to build and deploy the site,
or run the **Documentation** workflow manually from that branch. Pull requests
build the documentation without deploying it.

After a successful deployment, the site is available at
<https://ysenarath.github.io/nightjar/>. See GitHub's
[custom workflow guide](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
for Pages setup details.
