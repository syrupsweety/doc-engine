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
    collection-fontsrecommended \
    collection-langcyrillic \
    amsmath \
    amsfonts \
    tools \
    booktabs \
    caption \
    cm-super \
    cm-unicode \
    csquotes \
    ec \
    enumitem \
    fancyvrb \
    float \
    fontspec \
    geometry \
    graphics \
    hyperref \
    hyphenat \
    l3kernel \
    l3packages \
    latexmk \
    listings \
    setspace \
    titlesec \
    titling \
    tocloft \
    xcolor \
    url \
    tex-gyre \
    tex-gyre-math \
    koma-script \
    biber \
    biblatex \
    ieeetran

echo "=== Installation complete ==="
echo "Please restart your terminal or run: export PATH=\"$HOME/.TinyTeX/bin/x86_64-linux:\$PATH\""
