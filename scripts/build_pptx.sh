#!/usr/bin/env bash
set -euo pipefail

# build_pptx.sh — Idempotent workflow for validating, publishing, and rendering PPTX
# Usage: ./scripts/build_pptx.sh [example_file.xml]

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Activate virtualenv if present
if [ -d .venv ]; then
    source .venv/bin/activate
fi

# Default to current directory if no file specified
TARGET="${1:-.}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 XML-Lib Build Pipeline"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 1: Validate
echo "📋 Step 1/3: Validating XML documents..."
mkdir -p out
xml-lib validate "$TARGET" --strict --output out/assertions.xml --jsonl out/assertions.jsonl
echo "✅ Validation complete"
echo ""

# Step 2: Publish HTML documentation
echo "📚 Step 2/3: Publishing HTML documentation..."
xml-lib publish . --output-dir out/site
echo "✅ Documentation published to out/site"
echo ""

# Step 3: Render PPTX (only if a specific XML file is provided)
if [ -f "$TARGET" ] && [[ "$TARGET" == *.xml ]]; then
    echo "📊 Step 3/3: Rendering PowerPoint presentation..."
    BASENAME="$(basename "$TARGET" .xml)"
    xml-lib render-pptx "$TARGET" --output "out/${BASENAME}.pptx"
    echo "✅ PowerPoint created: out/${BASENAME}.pptx"
elif [ "$TARGET" = "." ]; then
    echo "📊 Step 3/3: Rendering PowerPoint for example_research_pitch.xml..."
    if [ -f "example_research_pitch.xml" ]; then
        xml-lib render-pptx example_research_pitch.xml --output out/research_pitch.pptx
        echo "✅ PowerPoint created: out/research_pitch.pptx"
    else
        echo "⚠️  No example_research_pitch.xml found, skipping PPTX rendering"
    fi
else
    echo "⚠️  Step 3/3: Skipping PPTX rendering (target is not an XML file)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ Build complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📂 Outputs:"
echo "   • out/assertions.xml      — Validation results (XML)"
echo "   • out/assertions.jsonl    — Validation results (JSON Lines)"
echo "   • out/site/               — HTML documentation"
if [ -f "$TARGET" ] && [[ "$TARGET" == *.xml ]]; then
    BASENAME="$(basename "$TARGET" .xml)"
    echo "   • out/${BASENAME}.pptx     — PowerPoint presentation"
elif [ "$TARGET" = "." ] && [ -f "example_research_pitch.xml" ]; then
    echo "   • out/research_pitch.pptx — PowerPoint presentation"
fi
echo ""
