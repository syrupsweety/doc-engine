# doc-engine: Document-as-Code System

A complete, production-ready **document-as-code** workflow that transforms Markdown documents into professionally formatted PDF, HTML, and DOCX outputs using Pandoc and LaTeX.

## Features

- **Multi-format publishing**: Generate PDF, HTML, and DOCX from a single Markdown source
- **Academic standards compliance**: Built-in profiles for GOST 7.32, IEEE Conference, and APA 7th Edition
- **Git-native workflow**: Full version control with Git LFS for binary assets
- **CI/CD integration**: Automated builds and GitHub Pages deployment
- **AI-assisted editing**: Designed for AI-proposed changes as diff patches

## Quick Start

### Prerequisites

- Ubuntu 22.04+ (or WSL on Windows)
- Git 2.30+
- Python 3.10+

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd doc-engine

# Installs system packages, Pandoc, TinyTeX, LaTeX packages and the Python
# dependencies listed in requirements.txt
./install.sh
```

### Usage

Build your document in all formats:

```bash
# Default profile (GOST 7.32)
make all

# Specific profile
make pdf PROFILE=ieee
make html PROFILE=apa-7th
make docx PROFILE=gost-7.32

# Custom input file
make pdf INPUT=docs/example/manuscript.md PROFILE=gost-7.32
```

## Available Profiles

| Profile | Standard | Supported Formats |
|---------|----------|-------------------|
| `gost-7.32` | GOST 7.32-2017 (Russian research reports) | PDF, HTML, DOCX |
| `ieee` | IEEE Conference proceedings | PDF, HTML, DOCX |
| `apa-7th` | APA 7th Edition | PDF, HTML, DOCX |

## Writing Documents

Documents are written in **Markdown** with **YAML front matter**:

```markdown
---
title: "Your Document Title"
author:
  - name: "Author Name"
    affiliation: "University"
date: "2024-02-12"
abstract: |
  Your abstract text here.
---

# Introduction

Your content here with **formatting** and $math$.
```

### Supported Features

- **LaTeX math**: `$inline$` and `$$display$$` formulas
- **Figures**: `![Caption](path.png){#fig:label}`
- **Tables**: Standard Markdown tables with captions
- **Code blocks**: Syntax-highlighted with language specification
- **Citations**: BibLaTeX/CSL bibliography support
- **Cross-references**: `@fig:label`, `@tbl:label`

## CI/CD Pipeline

The GitHub Actions workflow automatically:

1. Builds all output formats on every push to `main`
2. Validates YAML configurations
3. Deploys to GitHub Pages for easy access

Enable GitHub Pages in your repository settings to use this feature.

## License

MIT License - See LICENSE file for details.

## Acknowledgments

- [Pandoc](https://pandoc.org/) - Universal document converter
- [TinyTeX](https://yihui.org/tinytex/) - Lightweight LaTeX distribution
- [Citation Style Language](https://citationstyles.org/) - Citation formatting
