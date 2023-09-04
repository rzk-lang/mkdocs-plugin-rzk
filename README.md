# Rzk plugin for MkDocs

This is a [MkDocs plugin](https://www.mkdocs.org/dev-guide/plugins) for rendering SVG diagrams for Literate Rzk Markdown files (any file ending in `.rzk.md` extension). To use it, simply install the latest version (`pip install mkdocs-plugin-rzk`) and add it to your `mkdocs.yml` config file:

```yaml
plugins:
  - rzk
```

## Configuration

The following config options are supported:

| Name               | Type   | Default | Description                                     |
| ------------------ | ------ | ------- | ----------------------------------------------- |
| path               | `str`  | `rzk`   | Path to the Rzk executable                      |
| render_svg         | `bool` | `True`  | Enable/disable rendering SVGs for definitions (currently only works for files without dependencies) |
| anchor_definitions | `bool` | `True`  | Turn names of definitions into links to themselves (useful for generating a link to a particular `#define` in the generated MkDocs) |

## Development

To test this plugin while developing locally, run `pip install --editable <path/to/this/folder>` in the MkDocs project where this plugin is to be used. You will need to manually stop and rerun the MkDocs server on every update (hot reloading does not work).

## Packaging and Deployment

If you don't have them already, install the `build` and `twine` packages as such: `python3 -m pip install --upgrade build twine`.

Next, package your code by running `python3 -m build` to generate distribution archives (wheels) under the `dist` directory.

Lastly, run `twine upload dist/*` to upload the new version to PyPI.
