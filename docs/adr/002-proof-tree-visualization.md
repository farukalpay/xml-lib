# ADR 002: Multi-Backend Proof Tree Visualization

**Status:** Accepted

**Date:** 2025-11-10

## Context

Formal verification produces complex proof trees with axioms, lemmas, theorems, and their dependencies. These proof structures need to be:

1. **Visualized** for human understanding and review
2. **Interactive** for exploring large proof trees
3. **Shareable** for documentation and collaboration
4. **Exportable** for integration with other tools

Requirements:
- Support hierarchical proof structures (axioms → lemmas → theorems)
- Show verification status (verified, failed, unknown)
- Enable interactive exploration (zoom, pan, click for details)
- Generate static images for documentation
- Export to machine-readable formats (JSON)
- Work offline (no cloud dependencies)

## Decision

We will implement a **multi-backend proof tree visualization system** with three rendering engines:

### 1. Graphviz (Static Visualization)

**Purpose**: High-quality static diagrams for documentation

**Formats**: SVG, PNG, PDF

**Features**:
- Hierarchical layout with automatic positioning
- Color-coded nodes by type and status
- Styled borders indicating verification status
- Professional appearance for papers/reports

**Use Cases**:
- Documentation generation
- Presentation slides
- Academic papers
- Offline viewing

### 2. Plotly (Interactive Visualization)

**Purpose**: Browser-based interactive exploration

**Formats**: HTML with embedded JavaScript

**Features**:
- Zoom and pan
- Hover tooltips with proof details
- Click to view full statements
- Responsive layout
- Client-side only (no server required)

**Use Cases**:
- Development and debugging
- Code reviews
- Interactive documentation
- Proof exploration

### 3. NetworkX (Graph Analysis)

**Purpose**: Graph-theoretic analysis and layout

**Features**:
- Topological sorting for level assignment
- Hierarchical layout algorithm
- Graph metrics (depth, breadth, connectivity)
- Foundation for both rendering backends

**Use Cases**:
- Layout computation
- Proof tree analysis
- Custom visualizations
- Export to other formats

### Architecture

```
ProofTree → ProofTreeVisualizer
              ↓
              ├─→ NetworkX Graph (internal representation)
              ├─→ Graphviz (.svg, .png, .pdf)
              ├─→ Plotly (.html)
              ├─→ JSON (.json)
              └─→ HTML Report (.html)
```

## Alternatives Considered

### D3.js

**Pros**: Maximum flexibility, beautiful visualizations
**Cons**: Requires JavaScript expertise, complex integration
**Verdict**: Too heavyweight for our needs

### Cytoscape.js

**Pros**: Designed for graph visualization, good performance
**Cons**: Requires web server, complex setup
**Verdict**: Overkill for proof trees

### Mermaid

**Pros**: Simple syntax, GitHub integration
**Cons**: Limited to predefined diagrams, not programmable
**Verdict**: Not flexible enough

### GraphML + yEd

**Pros**: Standard format, manual editing
**Cons**: Requires external tool, not automated
**Verdict**: Not suitable for automated generation

### Why Our Approach?

1. **Multiple Output Formats**: Users choose based on context
2. **No External Services**: Fully offline capable
3. **Python Native**: Integrates seamlessly with existing codebase
4. **Proven Libraries**: Mature, well-maintained dependencies
5. **Progressive Enhancement**: Start simple, add interactivity as needed

## Implementation Details

### Color Scheme

**Node Types**:
- Root: Gray (`#EEEEEE`)
- Axiom: Green (`#E8F5E9`)
- Lemma: Blue (`#E3F2FD`)
- Theorem: Orange (`#FFF3E0`)
- Corollary: Purple (`#F3E5F5`)

**Verification Status** (border colors):
- Verified: Green (`#4CAF50`)
- Failed: Red (`#F44336`)
- Unknown: Orange (`#FF9800`)
- Timeout: Gray (`#9E9E9E`)

### Hierarchical Layout Algorithm

```python
def hierarchical_layout(proof_tree):
    1. Assign levels via topological sort
    2. Group nodes by level
    3. Spread nodes horizontally within level
    4. Position root at (0, 0)
    5. Position children below parents (y = -level)
    6. Optimize x-positions to minimize edge crossings
```

### Interactive Features (Plotly)

- **Hover**: Show full statement and proof steps
- **Zoom**: Mouse wheel or pinch to zoom
- **Pan**: Click and drag to move
- **Legend**: Color-coded status indicators
- **Responsive**: Adapts to window size

### HTML Report Generation

Generates comprehensive reports with:
- Verification statistics
- Proof tree visualization
- Detailed proof elements grouped by type
- Proof steps for each element
- Filterable by status

## Consequences

### Positive

✅ **Flexibility**: Users choose visualization format based on needs

✅ **Offline Capability**: No external services required

✅ **Integration**: Works with CI/CD for automated documentation

✅ **Accessibility**: Both interactive and static formats

✅ **Debugging**: Interactive exploration helps understand complex proofs

✅ **Documentation**: High-quality diagrams for papers and reports

### Negative

⚠️ **Dependency Weight**: Adds Plotly (~10MB) and Graphviz dependencies

⚠️ **Layout Complexity**: Hierarchical layout can be slow for very large trees (>1000 nodes)

⚠️ **Browser Dependency**: Interactive visualization requires modern browser

### Mitigation Strategies

1. **Lazy Loading**: Plotly only imported when needed
2. **Layout Caching**: Cache layout for repeated renders
3. **Fallback Options**: Provide simple text dump if visualization fails
4. **Size Limits**: Warn on trees with >500 nodes

## Usage Examples

### Generate All Formats

```python
from xml_lib.proof_visualization import ProofTreeVisualizer

visualizer = ProofTreeVisualizer(proof_tree)

# Static SVG for documentation
visualizer.render_graphviz(
    Path("out/proof_tree.svg"),
    format="svg"
)

# Interactive HTML for exploration
visualizer.render_interactive_plotly(
    Path("out/proof_tree.html")
)

# JSON for tooling
visualizer.export_json(
    Path("out/proof_tree.json")
)

# Comprehensive report
visualizer.generate_proof_report(
    Path("out/proof_report.html")
)
```

### Custom Styling

```python
# Subclass for custom visualization
class CustomVisualizer(ProofTreeVisualizer):
    def custom_colors(self, node_type):
        # Override color scheme
        pass
```

## Future Enhancements

1. **Graph Metrics**: Calculate proof complexity metrics
2. **Diff Visualization**: Show changes between proof versions
3. **Collapsible Nodes**: Hide/show subtrees in interactive view
4. **Search/Filter**: Find specific lemmas or theorems
5. **Export to LaTeX**: TikZ diagrams for papers
6. **3D Visualization**: For very deep proof trees

## References

- [Graphviz Documentation](https://graphviz.org/documentation/)
- [Plotly Python](https://plotly.com/python/)
- [NetworkX Documentation](https://networkx.org/documentation/stable/)
- [Information Visualization Principles](https://www.interaction-design.org/literature/article/information-visualization)
