#!/bin/bash

echo "Setting up development environment..."

# Enable pnpm via corepack (ships with Node.js)
sudo corepack enable

# Install Node.js dependencies from all package.json files
while IFS= read -r -d '' pkg_file; do
    dir=$(dirname "$pkg_file")
    echo "  Installing from $dir..."
    (cd "$dir" && pnpm install)
done < <(find . -name "package.json" -not -path "*/node_modules/*" -type f -print0 2>/dev/null)

# Install Python dependencies from all requirements.txt files
echo "Installing Python dependencies..."
while IFS= read -r -d '' req_file; do
    echo "  Installing from $req_file..."
    pip install -r "$req_file"
done < <(find . -name "requirements.txt" -type f -print0 2>/dev/null)

# Install Python dependencies from all pyproject.toml files (editable installs)
while IFS= read -r -d '' pyproject_file; do
    dir=$(dirname "$pyproject_file")
    echo "  Installing from $dir..."
    pip install -e "$dir"
done < <(find . -name "pyproject.toml" -type f -print0 2>/dev/null)

# Fix ownership on Claude volume mount (fresh volumes are root-owned)
sudo chown -R vscode:vscode /home/vscode/.claude || true

# Install Claude Code plugins (fallback for fresh Docker volumes)
if command -v claude &> /dev/null; then
    if ! claude plugin list 2>/dev/null | grep -q everything-claude-code; then
        echo "Installing everything-claude-code plugin..."
        claude plugin marketplace add affaan-m/everything-claude-code || true
        claude plugin install everything-claude-code@everything-claude-code --scope project || true
    fi
    if ! claude plugin list 2>/dev/null | grep -q caveman; then
        echo "Installing caveman plugin..."
        claude plugin marketplace add JuliusBrussee/caveman || true
        claude plugin install caveman@caveman --scope project || true
    fi
fi

# Optional: Headroom token compression proxy (https://github.com/chopratejas/headroom)
# Reduces token usage 60-95% by compressing context sent to the LLM.
# Uncomment to enable:
# pip install "headroom-ai[proxy]"
# headroom init claude

gh auth status 2>/dev/null || echo "Note: Run 'gh auth login' to enable GitHub CLI (gh pr, gh issue, etc.)"

echo "Development environment setup complete!"
