import re
import logging
import subprocess
import tempfile
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
        self.rzk_code_block = re.compile(r'(^```\s*rzk[^\n]*\s+(.*?)\s+^```)', flags=re.MULTILINE | re.DOTALL)
        self.define_name = re.compile(r'(<span class="nf">(.*?)</span>)')
        self.svg_element = re.compile(r'^(<svg.*?</svg>)', flags=re.MULTILINE | re.DOTALL)
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
        # Some snippets can depend on terms defined in previous snippets, so we need to store them all
        previous_snippets = ['#lang rzk-1\n#set-option "render" = "svg"\n\n']
        # Since each snippet will contain previous ones, the previously printed SVGs should not be repeated
        previous_svgs: set[str] = set()
        code_blocks = self.rzk_code_block.findall(md)
        for (fenced_block, code) in code_blocks:
            previous_snippets.append(code.replace('#lang rzk-1', ''))
            full_code = '\n'.join(previous_snippets).encode()
            with tempfile.NamedTemporaryFile(suffix='.rzk', delete_on_close=False) as f:
                f.write(full_code)
                f.close()
                process = subprocess.run([self.config.path, 'typecheck', f.name], capture_output=True)
            if process.returncode != 0:
                logger.debug(process.stderr.decode())
                continue

            output = process.stderr.decode()
            svgs: list[str] = self.svg_element.findall(output)
            # One snippet might have more than one diagram, so we shouldn't just use svgs[-1]
            # However, there is probably a more efficient way than iterating over all matches everytime
            for svg in svgs:
                if svg in previous_svgs: continue
                previous_svgs.add(svg)
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
