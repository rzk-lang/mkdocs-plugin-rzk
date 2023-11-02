import re
import logging
import subprocess
from typing import Literal

from mkdocs.plugins import BasePlugin
from mkdocs.config import base, config_options as c
from mkdocs.structure.pages import Page
from mkdocs.structure.files import Files
from mkdocs.config.defaults import MkDocsConfig

logger = logging.getLogger('mkdocs')


class RzkPluginConfig(base.Config):
    path = c.Type(str, default='rzk')
    render_svg = c.Type(bool, default=True)
    anchor_definitions = c.Type(bool, default=True)

class RzkPlugin(BasePlugin[RzkPluginConfig]):
    def __init__(self):
        self.define_svg = re.compile(
            r'\[ \d+ out of \d+ \] Checking (#def(?:ine)? \S+)' # Match the definition name
            r'(?!\s*\[ \d+ out of \d+ \]).+?' # Eat everything up to <svg> or next definition
            r'(<svg.*?<\/svg>)', # Match the SVG
        flags=re.MULTILINE | re.DOTALL)
        self.define_name = re.compile(r'(<span class="nf">(.*?)</span>)')
        self.rzk_installed = True

    def on_startup(self, *, command: Literal['build', 'gh-deploy', 'serve'], dirty: bool) -> None:
        logger.info('Checking if rzk is available (to render SVG diagrams)')
        try:
            # Capture output to prevent logging usage
            subprocess.run(self.config.path, capture_output=True)
        except FileNotFoundError:
            logger.warning('rzk executable not found (will not generate diagrams)')
            self.rzk_installed = False

    def on_page_markdown(self, md: str, page: Page, config: MkDocsConfig, files: Files) -> str:
        if not self.config.render_svg: return md
        if not page.file.src_uri.endswith('.rzk.md'): return md
        if not self.rzk_installed: return md
        logger.info('Inserting SVG diagrams in ' + page.file.src_uri)
        process = subprocess.run([self.config.path, 'typecheck', page.file.abs_src_path], capture_output=True)
        output = process.stderr.decode()
        if process.returncode != 0:
            logger.debug(output)
            return md

        svgs = self.define_svg.findall(output)
        for (name, svg) in svgs:
            # Find the code block that includes the given name and prepend it with the svg
            fenced_block_pattern = rf'```rzk[^`]*{re.escape(name)}\s[^`]*```'
            match = re.search(fenced_block_pattern, md)
            if match is None:
                logger.warning(f'Failed to find the code block containing "{name}"')
                continue
            fenced_block = match[0]
            md = md.replace(fenced_block, svg + '\n\n' + fenced_block)

        return md

    def on_page_content(self, html: str, *, page: Page, config: MkDocsConfig, files: Files) -> str:
        if not self.config.anchor_definitions: return html
        defines = self.define_name.findall(html)
        for (span, name) in defines:
            a = f'<a href="#define:{name}" id="define:{name}" style="visibility: visible; position: relative; color: inherit">{name}</a>'
            span_with_link = span.replace(name, a)
            html = html.replace(span, span_with_link)
        return html
