#!/usr/bin/env python3
"""Pandoc command construction."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from loader import ConfigLoader


class CommandBuilder:
    """Builds Pandoc commands with proper argument handling."""

    def __init__(self, profile_name: str, input_file: Path, output_file: Path, format_type: str):
        self.profile_name = profile_name
        self.input_file = input_file
        self.output_file = output_file
        self.format_type = format_type.lower()

        self.profile_config = ConfigLoader.load_profile_config(profile_name)
        self.shared_metadata = ConfigLoader.load_shared_metadata()

        if not self.profile_config:
            raise ValueError(f"Failed to load profile configuration for {profile_name}")

    def build_command(self, intermediate: bool = False) -> list[str]:
        """Build the complete Pandoc command."""
        cmd = ["pandoc"]

        cmd.extend([str(self.input_file)])

        if intermediate:
            tex_file = self.output_file.with_suffix(".tex")
            cmd.extend(["-o", str(tex_file)])
            cmd.extend(["-t", "latex"])
        else:
            cmd.extend(["-o", str(self.output_file)])

        self._add_resource_paths(cmd)

        self._add_format_options(cmd, intermediate)

        self._add_bibliography_options(cmd)

        self._add_pandoc_options(cmd)

        self._add_filters(cmd)

        self._add_metadata(cmd)

        return cmd

    def _add_resource_paths(self, cmd: list[str]) -> None:
        """Add resource paths for images and templates."""
        cmd.extend(["--resource-path", str(self.input_file.parent)])

        if self.format_type == "pdf":
            tex_path = Path(f"profiles/{self.profile_name}/tex")
            if tex_path.exists():
                cmd.extend(["--resource-path", str(tex_path)])

    def _add_format_options(self, cmd: list[str], intermediate: bool) -> None:
        """Add format-specific options."""
        output_config = ConfigLoader.get_output_config(self.profile_config, self.format_type)

        if not intermediate:
            engine = output_config.get("engine")
            if engine and self.format_type == "pdf":
                cmd.extend(["--pdf-engine", engine])

        template = output_config.get("template")
        if template:
            template_path = Path(f"profiles/{self.profile_name}/{template}")
            if self.format_type == "docx":
                cmd.extend(["--reference-doc", str(template_path)])
            else:
                cmd.extend(["--template", str(template_path)])

        if self.format_type == "html" and not intermediate:
            cmd.extend(["--standalone", "--embed-resources"])

        extensions = output_config.get("extensions", [])
        for ext in extensions:
            cmd.append(ext)

        additional_args = output_config.get("additional_args", [])
        for arg in additional_args:
            cmd.append(arg)

    def _add_bibliography_options(self, cmd: list[str]) -> None:
        """Add bibliography configuration."""
        bib_method = ConfigLoader.get_bibliography_method(self.profile_config, self.format_type)

        if bib_method == "csl":
            cmd.append("--citeproc")
            csl_file = self._get_csl_file()
            if csl_file:
                cmd.extend(["--csl", str(csl_file)])

            self._add_bibliography_file(cmd)

            options = self.profile_config.get("bibliography", {}).get("options", [])
            for opt in options:
                if opt not in cmd:
                    cmd.append(opt)

        elif bib_method in ["bibtex", "biblatex"] and self.format_type == "pdf":
            cmd.extend(["--variable", f"bib-method.{bib_method}=true"])

            bib_style = self._get_bib_style()
            cmd.extend(["--variable", f"bib-style={bib_style}"])

            self._add_bibliography_file(cmd)

            if bib_method == "bibtex":
                cmd.extend(["--variable", "natbib=true"])
            elif bib_method == "biblatex":
                cmd.extend(["--variable", "biblatex=true"])

    def _add_pandoc_options(self, cmd: list[str]) -> None:
        """Add Pandoc-specific options."""
        pandoc_opts = self.profile_config.get("pandoc_options", {})

        if pandoc_opts.get("toc", False):
            cmd.append("--toc")

        toc_depth = pandoc_opts.get("toc_depth")
        if toc_depth:
            cmd.extend(["--toc-depth", str(toc_depth)])

        if pandoc_opts.get("number_sections", False):
            cmd.append("--number-sections")

        highlight_style = pandoc_opts.get("highlight_style")
        if highlight_style:
            cmd.extend(["--highlight-style", highlight_style])

        reference_location = pandoc_opts.get("reference_location")
        if reference_location:
            cmd.extend(["--reference-location", reference_location])

    def _add_filters(self, cmd: list[str]) -> None:
        """Add filters."""
        filters = self.profile_config.get("filters", [])
        for filter_name in filters:
            filter_path = Path(f"profiles/{self.profile_name}/{filter_name}")
            if filter_path.exists():
                if filter_name.endswith(".lua"):
                    cmd.extend(["--lua-filter", str(filter_path)])
                else:
                    cmd.extend(["--filter", str(filter_path)])
            else:
                cmd.extend(["--filter", filter_name])

    def _add_metadata(self, cmd: list[str]) -> None:
        """Add metadata variables."""
        metadata_as_meta = {
            "figPrefix",
            "eqPrefix",
            "tblPrefix",
            "secPrefix",
            "figPrefixTemplate",
            "eqPrefixTemplate",
            "tblPrefixTemplate",
            "secPrefixTemplate",
        }

        merged_metadata = ConfigLoader.merge_metadata(self.profile_config, self.shared_metadata)

        for key, value in merged_metadata.items():
            if value is not None and value != "":
                if isinstance(value, list):
                    value = ",".join(str(v) for v in value)

                if key in metadata_as_meta:
                    cmd.extend([f"--metadata={key}:{value}"])
                else:
                    cmd.extend([f"--variable={key}:{value}"])

    def _get_csl_file(self) -> Path | None:
        """Get the CSL file path."""
        output_config = ConfigLoader.get_output_config(self.profile_config, self.format_type)
        csl_file = output_config.get("csl_file") or self.profile_config.get("bibliography", {}).get(
            "csl_file"
        )
        if csl_file:
            profile_path = Path(f"profiles/{self.profile_name}")
            return profile_path / csl_file
        return None

    def _get_bib_style(self) -> str:
        """Get the bibliography style."""
        output_config = ConfigLoader.get_output_config(self.profile_config, self.format_type)
        return output_config.get("bib_style", "ugost2008")

    def _add_bibliography_file(self, cmd: list[str]) -> None:
        """Add bibliography file to command."""
        bibliography = self.profile_config.get("metadata_defaults", {}).get("bibliography")
        if bibliography:
            bib_path = self.input_file.parent / bibliography
            if bib_path.exists():
                if (
                    ConfigLoader.get_bibliography_method(self.profile_config, self.format_type)
                    == "csl"
                ):
                    cmd.extend(["--bibliography", str(bib_path)])
                else:
                    cmd.extend(["--variable", f"bibliography={bib_path}"])
