#!/bin/bash
#
# Example 1: Basic XML Validation
#
# This script demonstrates basic validation pipeline usage.

set -e  # Exit on error

echo "========================================="
echo "Example 1: Basic XML Validation"
echo "========================================="
echo ""

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Create output directory
mkdir -p output

echo "1. Validating a VALID XML document..."
echo "   Command: xml-lib pipeline run pipeline.yaml input/sample-valid.xml"
echo ""

if xml-lib pipeline run pipeline.yaml input/sample-valid.xml; then
    echo ""
    echo "✅ Validation succeeded!"
    echo ""
    echo "Output files created:"
    echo "  - output/validation-report.html"
    echo "  - output/summary.json"
    echo ""
else
    echo ""
    echo "❌ Validation failed (unexpected)"
    exit 1
fi

echo "========================================="
echo "Example completed successfully!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  - View output/validation-report.html in a browser"
echo "  - Check output/summary.json for JSON summary"
echo "  - Try with different XML files"
echo "  - Explore other examples in ../02-multi-format-output/"
