#!/usr/bin/env python3
"""Rendering engine: builds the pandoc command and runs it."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).parent))

from builder import CommandBuilder  # noqa: E402,I001
from docx_export import patch_layout, prepare  # noqa: E402
from loader import ConfigLoader  # noqa: E402


class DocEngineRenderer:
    """Renders a document from markdown using a profile."""

    def __init__(
        self,
        profile_name: str,
        input_file: Path,
        output_file: Path,
        format_type: str,
    ) -> None:
        self.profile_name = profile_name
        self.input_file = input_file
        self.output_file = output_file
        self.format_type = format_type.lower()
        self._combined_content: str | None = None
        self._section_offsets: list[int] = []
        self._bibliography_files: list[Path] = []
        if self.input_file.is_dir():
            self._combined_content = self._concat_markdown_files(self.input_file)

    def render(self) -> bool:
        try:
            ConfigLoader.ensure_output_dir(self.output_file)
            if self._needs_bibtex():
                return self._run_bibtex_compilation()
            return self._run_standard_rendering()
        except Exception as exc:  # noqa: BLE001 - CLI boundary
            print(f"error: {exc}", file=sys.stderr)
            return False

    def _run_standard_rendering(self) -> bool:
        env = self._get_environment()
        cmd = CommandBuilder(
            self.profile_name, self.input_file, self.output_file, self.format_type
        ).build_command()
        if self._combined_content:
            cmd = self._use_combined_content(cmd)
        if self._docx_prepass():
            cmd = self._prepare_docx_input(cmd)

        print(f"{self.format_type}: {self.input_file.name} -> {self.output_file}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=env)
        except subprocess.CalledProcessError as exc:
            print(f"error: pandoc exited with {exc.returncode}", file=sys.stderr)
            print(exc.stderr, file=sys.stderr)
            return False
        except FileNotFoundError:
            print("error: pandoc not found in PATH", file=sys.stderr)
            return False

        if result.stdout:
            print(result.stdout)
        if self._docx_prepass():
            patch_layout(self.output_file)
        return True

    def _run_bibtex_compilation(self) -> bool:
        env = self._get_environment()
        engine = self._get_latex_engine()
        output_dir = self.output_file.parent

        cmd = CommandBuilder(
            self.profile_name, self.input_file, self.output_file, self.format_type
        ).build_command(intermediate=True)
        if self._combined_content:
            cmd = self._use_combined_content(cmd)

        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True, env=env)
        except subprocess.CalledProcessError as exc:
            print(f"error: pandoc exited with {exc.returncode}", file=sys.stderr)
            print(exc.stderr, file=sys.stderr)
            return False

        tex_file = self.output_file.with_suffix(".tex")
        aux_file = self.output_file.with_suffix(".aux")
        latex_cmd = [
            engine,
            "-interaction=nonstopmode",
            "-output-directory",
            str(output_dir),
            str(tex_file),
        ]

        subprocess.run(latex_cmd, capture_output=True, text=True, env=env)

        bib_method = ConfigLoader.get_bibliography_method(
            ConfigLoader.load_profile_config(self.profile_name), self.format_type
        )
        if bib_method == "bibtex":
            subprocess.run(
                ["bibtex", str(aux_file.name)],
                capture_output=True,
                text=True,
                cwd=str(output_dir),
                env=env,
            )
        elif bib_method == "biblatex":
            stem = self.output_file.with_suffix(".bcf").stem
            subprocess.run(
                ["biber", stem], capture_output=True, text=True, cwd=str(output_dir), env=env
            )

        for _ in range(2):
            result = subprocess.run(latex_cmd, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            print(f"error: {engine} failed", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            return False
        return True

    def _docx_prepass(self) -> bool:
        """True when the profile wants a title page and real tables in the DOCX."""
        if self.format_type != "docx":
            return False
        config = ConfigLoader.load_profile_config(self.profile_name)
        if not config:
            return False
        return bool(ConfigLoader.get_output_config(config, "docx").get("docx_prepass", False))

    def _prepare_docx_input(self, cmd: list[str]) -> list[str]:
        prepared = Path(tempfile.mkdtemp()) / "docx-source.md"
        prepare(Path(cmd[1]), prepared)
        cmd[1] = str(prepared)
        return cmd

    def _needs_bibtex(self) -> bool:
        if self.format_type != "pdf":
            return False
        config = ConfigLoader.load_profile_config(self.profile_name)
        if not config:
            return False
        return ConfigLoader.get_bibliography_method(config, self.format_type) in (
            "bibtex",
            "biblatex",
        )

    def _get_environment(self) -> dict[str, str]:
        env = dict(os.environ)
        if self.format_type == "pdf":
            profile_path = Path("profiles") / self.profile_name
            for var, subdir in (("TEXINPUTS", "tex"), ("BSTINPUTS", "bibtex/bst")):
                path = profile_path / subdir
                if path.exists():
                    env[var] = f"{path}:{env.get(var, '')}"
        return env

    def _get_latex_engine(self) -> str:
        config = ConfigLoader.load_profile_config(self.profile_name)
        if not config:
            return "xelatex"
        return ConfigLoader.get_output_config(config, self.format_type).get("engine", "xelatex")

    def _use_combined_content(self, cmd: list[str]) -> list[str]:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(self._combined_content or "")
        cmd[1] = tmp.name
        return cmd

    def _concat_markdown_files(self, input_path: Path) -> str:
        contents_file = input_path / "contents.txt"
        self._bibliography_files = []

        if contents_file.exists():
            md_files = self._read_contents_file(contents_file, input_path)
        else:
            md_files = sorted(input_path.glob("*.md"))
        if not md_files:
            raise FileNotFoundError(f"no markdown files in {input_path}")

        parts: list[str] = []
        metadata: dict[str, Any] = {}
        offsets: list[int] = []
        sections = 0

        for md_file in md_files:
            content = md_file.read_text(encoding="utf-8")
            body = content
            if content.startswith("---"):
                split = content.split("---", 2)
                if len(split) >= 3:
                    file_meta = yaml.safe_load(split[1]) or {}
                    for key, value in file_meta.items():
                        if key not in metadata or (key == "bibliography" and value):
                            metadata[key] = value
                    body = split[2].strip()

            if self._is_section_numerated(body):
                offsets.append(sections)
                sections += self._count_sections(body)
            else:
                offsets.append(0)

            parts.append(body)
            if md_file != md_files[-1]:
                page_break = self._get_page_break()
                if page_break:
                    parts.append(page_break)

        self._section_offsets = offsets
        if self._bibliography_files:
            metadata["bibliography"] = str(self._bibliography_files[0].resolve())

        if not metadata:
            return "\n\n".join(parts)
        front = yaml.dump(metadata, allow_unicode=True, default_flow_style=False)
        return f"---\n{front}---\n\n" + "\n\n".join(parts)

    def _read_contents_file(self, contents_file: Path, input_path: Path) -> list[Path]:
        try:
            lines = contents_file.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise ValueError(f"cannot read contents.txt: {exc}") from exc
        if not lines:
            raise ValueError("contents.txt is empty")

        files: list[Path] = []
        for num, raw in enumerate(lines, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            path = input_path / line
            if not path.exists():
                raise FileNotFoundError(f"{line} (contents.txt line {num}) does not exist")
            if path.suffix == ".bib":
                self._bibliography_files.append(path)
                continue
            if path.suffix != ".md":
                print(f"warning: skipping {line} (line {num})", file=sys.stderr)
                continue
            files.append(path)

        if not files:
            raise ValueError("contents.txt lists no markdown files")

        unlisted = set(input_path.glob("*.md")) - set(files)
        for missing in sorted(unlisted):
            print(f"warning: {missing.name} is not listed in contents.txt", file=sys.stderr)
        return files

    def _get_page_break(self) -> str:
        config = ConfigLoader.load_profile_config(self.profile_name)
        if not config:
            return ""
        output_config = ConfigLoader.get_output_config(config, self.format_type)
        if not output_config.get("page_break_between_files", False):
            return ""
        if self.format_type in ("pdf", "docx"):
            return "\\newpage"
        if self.format_type == "html":
            return '<div style="page-break-before: always;"></div>'
        return ""

    @staticmethod
    def _count_sections(content: str) -> int:
        return sum(1 for line in content.splitlines() if line.strip().startswith("# "))

    @staticmethod
    def _is_section_numerated(content: str) -> bool:
        if not content.startswith("---"):
            return True
        try:
            split = content.split("---", 2)
            if len(split) >= 3:
                return bool((yaml.safe_load(split[1]) or {}).get("numbered", True))
        except yaml.YAMLError:
            pass
        return True
