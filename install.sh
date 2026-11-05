#!/bin/bash
# Installation script for doc-engine
# Tested on Ubuntu 22.04/24.04

set -e

echo "=== Installing doc-engine dependencies ==="

# Update package list
sudo apt-get update

# Install required system packages
echo "Installing system dependencies..."
sudo apt-get install -y \
    wget \
    curl \
    git \
    git-lfs \
    python3 \
    python3-pip \
    python3-venv \
    libfontconfig1 \
    libfreetype6 \
    libpng-dev \
    libjpeg-dev \
    libtiff-dev \
    libgflags-dev \
    libgif-dev

# Install Git LFS
echo "Setting up Git LFS..."
git lfs install

# Install Pandoc; PANDOC_VERSION pins the release, otherwise ask GitHub for the latest
echo "Installing Pandoc..."
PANDOC_RELEASE="${PANDOC_VERSION:-}"
if [ -z "$PANDOC_RELEASE" ]; then
    PANDOC_RELEASE=$(curl -fsSL --max-time 20 \
        https://api.github.com/repos/jgm/pandoc/releases/latest 2>/dev/null \
        | grep -Po '"tag_name": "\K.*?(?=")' || true)
fi
if [ -z "$PANDOC_RELEASE" ]; then
    echo "error: cannot detect the Pandoc release, set PANDOC_VERSION (e.g. 3.1.11.1)" >&2
    exit 1
fi
PANDOC_DEB="pandoc-${PANDOC_RELEASE}-1-amd64.deb"
echo "Pandoc ${PANDOC_RELEASE}"
wget -q "https://github.com/jgm/pandoc/releases/download/${PANDOC_RELEASE}/${PANDOC_DEB}" -O /tmp/pandoc.deb
sudo dpkg -i /tmp/pandoc.deb > /dev/null
rm -f /tmp/pandoc.deb

# Install TinyTeX
echo "Installing TinyTeX..."
if [ -d "$HOME/.TinyTeX" ] || [ -d "/usr/local/TinyTeX" ]; then
    echo "TinyTeX already installed, skipping..."
else
    wget -qO- "https://yihui.org/tinytex/install-bin-unix.sh" | sh
fi

# Add TinyTeX to PATH if not already there
if ! command -v tlmgr &> /dev/null; then
    export PATH="$HOME/.TinyTeX/bin/x86_64-linux:$PATH"
fi

# Install required LaTeX packages (tlmgr refuses to work until it updates itself)
echo "Installing LaTeX packages..."
tlmgr update --self
tlmgr install \
    gost \
    biblatex-gost \
    extsizes \
    babel-russian \
    titlesec \
    titling \
    tocloft \
    caption \
    enumitem \
    fancyhdr \
    microtype \
    parskip \
    etoolbox \
    hyphenat \
    setspace \
    unicode-math \
    upquote \
    xurl \
    geometry \
    graphics \
    hyperref \
    xcolor \
    url \
    float \
    fancyvrb \
    listings \
    booktabs \
    multirow \
    amsmath \
    amsfonts \
    tools \
    l3kernel \
    l3packages \
    iftex \
    lm \
    tex-gyre \
    tex-gyre-math \
    collection-fontsrecommended \
    collection-langcyrillic \
    cm-super \
    cm-unicode \
    ec \
    fontspec \
    koma-script \
    csquotes \
    biblatex \
    biber \
    latexmk \
    ieeetran

# Install Python dependencies for the interpreter that runs the scripts
echo "Installing Python dependencies..."
if python3 -m pip install --user -r requirements.txt > /dev/null 2>&1; then
    echo "Python packages installed for current user"
elif python3 -m venv .venv 2>/dev/null && .venv/bin/pip install -q -r requirements.txt; then
    echo "Python packages installed in .venv (use .venv/bin/python3)"
else
    echo "error: cannot install Python packages." >&2
    echo "Install python3-venv and rerun, or run:" >&2
    echo "  python3 -m pip install --break-system-packages -r requirements.txt" >&2
    exit 1
fi

echo "=== Installation complete ==="
echo "Please restart your terminal or run: export PATH=\"$HOME/.TinyTeX/bin/x86_64-linux:\$PATH\""
