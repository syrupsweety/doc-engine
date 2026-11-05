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

# Install latest Pandoc from GitHub releases
echo "Installing Pandoc..."
PANDOC_VERSION=$(curl -s https://api.github.com/repos/jgm/pandoc/releases/latest | grep -Po '"tag_name": "\K.*?(?=")')
PANDOC_DEB="pandoc-${PANDOC_VERSION}-1-amd64.deb"
wget "https://github.com/jgm/pandoc/releases/download/${PANDOC_VERSION}/${PANDOC_DEB}" -O /tmp/pandoc.deb
sudo dpkg -i /tmp/pandoc.deb
rm /tmp/pandoc.deb

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

# Install required LaTeX packages
echo "Installing LaTeX packages..."
tlmgr install \
    gost \
    biblatex-gost \
    collection-fontsrecommended \
    collection-langcyrillic \
    IEEEtran \
    biblatex \
    biber \
    csquotes \
    graphics \
    geometry \
    hyperref \
    xcolor \
    url \
    bookmark \
    fontspec \
    l3packages \
    l3kernel \
    koma-script \
    ec \
    cm-super \
    cm-unicode \
    tex-gyre \
    tex-gyre-math \
    amsmath \
    amssymb \
    listings \
    fancyvrb \
    longtable \
    float \
    latexmk \
    titlesec \
    titling \
    chngcntr \
    tocloft \
    enumitem \
    caption \
    tabularx \
    hyphenat \
    scrextend \
    indentfirst \
    setspace \
    booktabs \
    array

# Install Python dependencies
echo "Installing Python dependencies..."
if pip3 install --user -r requirements.txt > /dev/null 2>&1; then
    echo "Python packages installed for current user"
elif python3 -m venv .venv 2>/dev/null && .venv/bin/pip install -q -r requirements.txt; then
    echo "Python packages installed in .venv (use .venv/bin/python3)"
else
    echo "error: cannot install Python packages." >&2
    echo "Install python3-venv and rerun this script, or run:" >&2
    echo "  pip3 install --break-system-packages -r requirements.txt" >&2
    exit 1
fi

echo "=== Installation complete ==="
echo "Please restart your terminal or run: export PATH=\"$HOME/.TinyTeX/bin/x86_64-linux:\$PATH\""
