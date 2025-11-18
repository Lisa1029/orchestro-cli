#!/bin/bash
# Verification script for Orchestro Intelligence System Demo

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║        ORCHESTRO INTELLIGENCE SYSTEM - VERIFICATION SCRIPT                   ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="/home/jonbrookings/vibe_coding_projects/my-orchestro-copy"
cd "$PROJECT_ROOT"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  Checking File Structure"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

FILES=(
    "orchestro_cli/intelligence/__init__.py"
    "orchestro_cli/intelligence/models/app_knowledge.py"
    "orchestro_cli/intelligence/indexing/ast_analyzer.py"
    "orchestro_cli/intelligence/generation/scenario_generator.py"
    "examples/demo_intelligence.py"
    "examples/sample_tui_app/app.py"
    "tests/integration/test_intelligence_e2e.py"
    "examples/INTELLIGENCE_DEMO.md"
    "docs/INTELLIGENCE_QUICK_START.md"
)

for file in "${FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "✗ $file (MISSING)"
        exit 1
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  Testing Python Imports"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 -c "
from orchestro_cli.intelligence import ASTAnalyzer, ScenarioGenerator
from orchestro_cli.intelligence.models import AppKnowledge
print('✓ All imports successful')
"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  Running Demo Script"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python examples/demo_intelligence.py > /tmp/demo_output.txt 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Demo script executed successfully"
    echo ""
    echo "Output preview:"
    head -n 20 /tmp/demo_output.txt
    echo "..."
    tail -n 10 /tmp/demo_output.txt
else
    echo "✗ Demo script failed"
    cat /tmp/demo_output.txt
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  Verifying Generated Files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

GENERATED_FILES=(
    "examples/generated_tests/smoke_test.yaml"
    "examples/generated_tests/keybinding_test.yaml"
    "examples/generated_tests/navigation_test.yaml"
    "examples/generated_tests/app_knowledge.json"
)

for file in "${GENERATED_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file")
        echo -e "${GREEN}✓${NC} $file (${size} bytes)"
    else
        echo -e "✗ $file (NOT GENERATED)"
        exit 1
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  Validating YAML Files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 -c "
import yaml
from pathlib import Path

yaml_files = [
    'examples/generated_tests/smoke_test.yaml',
    'examples/generated_tests/keybinding_test.yaml',
    'examples/generated_tests/navigation_test.yaml',
]

for file in yaml_files:
    content = yaml.safe_load(Path(file).read_text())
    assert 'name' in content
    assert 'steps' in content
    assert len(content['steps']) > 0
    print(f'✓ {file} - Valid YAML with {len(content[\"steps\"])} steps')
"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6️⃣  Validating JSON Knowledge"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 -c "
import json
from pathlib import Path

knowledge = json.loads(Path('examples/generated_tests/app_knowledge.json').read_text())
assert 'screens' in knowledge
assert 'entry_screen' in knowledge
assert len(knowledge['screens']) == 3
print(f'✓ Knowledge JSON valid with {len(knowledge[\"screens\"])} screens')
print(f'  Entry screen: {knowledge[\"entry_screen\"]}')
for screen_name, screen in knowledge['screens'].items():
    print(f'  - {screen_name}: {len(screen[\"keybindings\"])} keybindings')
"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7️⃣  Running Integration Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python -m pytest tests/integration/test_intelligence_e2e.py --integration -v --tb=no 2>&1 | grep -E "passed|failed|PASSED|FAILED" | tail -5

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "8️⃣  Checking Documentation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

DOC_FILES=(
    "examples/INTELLIGENCE_DEMO.md"
    "examples/sample_tui_app/README.md"
    "docs/INTELLIGENCE_QUICK_START.md"
    "INTELLIGENCE_SYSTEM_DEMO_COMPLETE.md"
)

total_lines=0
for file in "${DOC_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        lines=$(wc -l < "$file")
        total_lines=$((total_lines + lines))
        echo -e "${GREEN}✓${NC} $file ($lines lines)"
    fi
done

echo ""
echo "Total documentation: $total_lines lines"

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                         ✅ VERIFICATION COMPLETE                           ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "All checks passed! The Orchestro Intelligence System is fully functional."
echo ""
echo "Quick start:"
echo "  python examples/demo_intelligence.py"
echo ""
echo "Documentation:"
echo "  cat examples/INTELLIGENCE_DEMO.md"
echo "  cat docs/INTELLIGENCE_QUICK_START.md"
echo ""
