"""Visual proof tree generator with interactive exploration.

This module provides interactive visualization of formal verification proof trees
using multiple rendering backends (Graphviz, Plotly, NetworkX).
"""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx
from graphviz import Digraph

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from xml_lib.formal_verification import (
    ProofNode,
    ProofResult,
    ProofStatus,
    ProofTree,
)


class ProofTreeVisualizer:
    """Visualizer for proof trees with multiple backend support."""

    def __init__(self, proof_tree: ProofTree):
        """Initialize visualizer with a proof tree.

        Args:
            proof_tree: The proof tree to visualize
        """
        self.proof_tree = proof_tree
        self.graph = nx.DiGraph()
        self._build_networkx_graph()

    def _build_networkx_graph(self) -> None:
        """Build NetworkX graph from proof tree."""

        def add_node_recursive(node: ProofNode, parent_id: Optional[str] = None):
            """Recursively add nodes to the graph."""
            # Add node with attributes
            self.graph.add_node(
                node.id,
                label=node.label,
                type=node.type,
                statement=node.statement,
                status=node.status.value,
                proof_steps=node.proof_steps,
            )

            # Add edge from parent
            if parent_id is not None:
                self.graph.add_edge(parent_id, node.id)

            # Recursively add children
            for child in node.children:
                add_node_recursive(child, node.id)

        # Build graph starting from root
        add_node_recursive(self.proof_tree.root)

    def render_graphviz(
        self, output_path: Path, format: str = "svg", view: bool = False
    ) -> Path:
        """Render proof tree using Graphviz.

        Args:
            output_path: Path to save the rendered graph
            format: Output format (svg, png, pdf, etc.)
            view: Whether to open the file after rendering

        Returns:
            Path to the rendered file
        """
        dot = Digraph(comment="Proof Tree", format=format)
        dot.attr(rankdir="TB", splines="ortho")
        dot.attr("node", shape="box", style="rounded,filled", fontname="Arial")

        # Color scheme based on node type and status
        color_map = {
            "axiom": "#E8F5E9",
            "lemma": "#E3F2FD",
            "theorem": "#FFF3E0",
            "corollary": "#F3E5F5",
            "root": "#EEEEEE",
        }

        status_border_map = {
            ProofStatus.VERIFIED.value: "#4CAF50",
            ProofStatus.FAILED.value: "#F44336",
            ProofStatus.UNKNOWN.value: "#FF9800",
            ProofStatus.TIMEOUT.value: "#9E9E9E",
        }

        def add_node_to_dot(node: ProofNode):
            """Recursively add nodes to Graphviz graph."""
            # Determine colors
            fill_color = color_map.get(node.type, "#FFFFFF")
            border_color = status_border_map.get(
                node.status.value, "#000000"
            )

            # Create label with HTML-like formatting
            label = f"<<B>{node.label}</B><BR/>"
            label += f"<FONT POINT-SIZE='10'>{node.type}</FONT>"

            if node.status != ProofStatus.UNKNOWN:
                label += f"<BR/><FONT POINT-SIZE='9' COLOR='{border_color}'>"
                label += f"Status: {node.status.value}</FONT>"

            label += ">"

            # Add node with styling
            dot.node(
                node.id,
                label,
                fillcolor=fill_color,
                color=border_color,
                penwidth="2",
            )

            # Add edges to children
            for child in node.children:
                dot.edge(node.id, child.id)
                add_node_to_dot(child)

        # Build the graph
        add_node_to_dot(self.proof_tree.root)

        # Render
        output_file = output_path.with_suffix("")
        dot.render(str(output_file), view=view, cleanup=True)

        return output_path

    def render_interactive_plotly(self, output_path: Path) -> Path:
        """Render interactive proof tree using Plotly.

        Args:
            output_path: Path to save the HTML file

        Returns:
            Path to the HTML file
        """
        if not PLOTLY_AVAILABLE:
            raise ImportError("Plotly is required for interactive visualization")

        # Use hierarchical layout
        pos = self._hierarchical_layout()

        # Prepare edge traces
        edge_x = []
        edge_y = []

        for edge in self.graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        edge_trace = go.Scatter(
            x=edge_x,
            y=edge_y,
            line=dict(width=2, color="#888"),
            hoverinfo="none",
            mode="lines",
        )

        # Prepare node traces
        node_x = []
        node_y = []
        node_text = []
        node_color = []
        node_size = []

        status_color_map = {
            ProofStatus.VERIFIED.value: "#4CAF50",
            ProofStatus.FAILED.value: "#F44336",
            ProofStatus.UNKNOWN.value: "#FF9800",
            ProofStatus.TIMEOUT.value: "#9E9E9E",
        }

        type_size_map = {
            "root": 30,
            "axiom": 20,
            "lemma": 18,
            "theorem": 25,
            "corollary": 16,
        }

        for node_id in self.graph.nodes():
            x, y = pos[node_id]
            node_x.append(x)
            node_y.append(y)

            node_data = self.graph.nodes[node_id]
            label = node_data.get("label", node_id)
            node_type = node_data.get("type", "unknown")
            status = node_data.get("status", ProofStatus.UNKNOWN.value)
            statement = node_data.get("statement", "")

            # Create hover text
            hover_text = f"<b>{label}</b><br>"
            hover_text += f"Type: {node_type}<br>"
            hover_text += f"Status: {status}<br>"
            hover_text += f"Statement: {statement[:100]}"
            if len(statement) > 100:
                hover_text += "..."

            node_text.append(hover_text)
            node_color.append(status_color_map.get(status, "#999999"))
            node_size.append(type_size_map.get(node_type, 15))

        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            hovertemplate="%{text}<extra></extra>",
            text=[self.graph.nodes[n].get("label", n)[:15] for n in self.graph.nodes()],
            textposition="bottom center",
            textfont=dict(size=8),
            customdata=node_text,
            marker=dict(
                size=node_size,
                color=node_color,
                line=dict(width=2, color="#FFF"),
            ),
        )

        # Update hover template to use custom data
        node_trace.hovertemplate = "%{customdata}<extra></extra>"

        # Create figure
        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title=dict(text="<b>Formal Verification Proof Tree</b>", font=dict(size=20)),
                showlegend=False,
                hovermode="closest",
                margin=dict(b=20, l=5, r=5, t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor="#FAFAFA",
            ),
        )

        # Add annotations for legend
        fig.add_annotation(
            text="<b>Status Colors:</b><br>"
            "<span style='color:#4CAF50'>● Verified</span><br>"
            "<span style='color:#F44336'>● Failed</span><br>"
            "<span style='color:#FF9800'>● Unknown</span>",
            xref="paper",
            yref="paper",
            x=0.02,
            y=0.98,
            showarrow=False,
            align="left",
            bgcolor="white",
            bordercolor="#DDD",
            borderwidth=1,
        )

        # Write to file
        fig.write_html(str(output_path))

        return output_path

    def _hierarchical_layout(self) -> Dict[str, Tuple[float, float]]:
        """Compute hierarchical layout for the graph.

        Returns:
            Dictionary mapping node IDs to (x, y) positions
        """
        # Use topological sort to determine levels
        levels: Dict[str, int] = {}

        def assign_level(node_id: str, level: int = 0):
            """Recursively assign levels to nodes."""
            if node_id in levels:
                levels[node_id] = max(levels[node_id], level)
            else:
                levels[node_id] = level

            for child in self.graph.successors(node_id):
                assign_level(child, level + 1)

        # Start from root
        root_id = self.proof_tree.root.id
        assign_level(root_id)

        # Group nodes by level
        level_groups: Dict[int, List[str]] = {}
        for node_id, level in levels.items():
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(node_id)

        # Assign positions
        pos: Dict[str, Tuple[float, float]] = {}
        max_level = max(level_groups.keys()) if level_groups else 0

        for level, nodes in level_groups.items():
            y = -level  # Negative to go top to bottom
            num_nodes = len(nodes)

            for i, node_id in enumerate(nodes):
                # Spread nodes horizontally
                if num_nodes == 1:
                    x = 0.0
                else:
                    x = (i - (num_nodes - 1) / 2) * 2

                pos[node_id] = (x, float(y))

        return pos

    def generate_proof_report(self, output_path: Path) -> Path:
        """Generate a comprehensive proof verification report in HTML.

        Args:
            output_path: Path to save the HTML report

        Returns:
            Path to the HTML report
        """
        html = self._generate_html_report()

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return output_path

    def _generate_html_report(self) -> str:
        """Generate HTML report content."""
        # Count statistics
        total_nodes = len(self.graph.nodes())
        verified_count = sum(
            1
            for n in self.graph.nodes()
            if self.graph.nodes[n].get("status") == ProofStatus.VERIFIED.value
        )
        failed_count = sum(
            1
            for n in self.graph.nodes()
            if self.graph.nodes[n].get("status") == ProofStatus.FAILED.value
        )

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Formal Verification Proof Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1976D2;
            border-bottom: 3px solid #1976D2;
            padding-bottom: 10px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-card.verified {{
            background: #E8F5E9;
            border-left: 4px solid #4CAF50;
        }}
        .stat-card.failed {{
            background: #FFEBEE;
            border-left: 4px solid #F44336;
        }}
        .stat-card.total {{
            background: #E3F2FD;
            border-left: 4px solid #2196F3;
        }}
        .stat-value {{
            font-size: 36px;
            font-weight: bold;
            margin: 10px 0;
        }}
        .stat-label {{
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
        }}
        .proof-tree {{
            margin: 30px 0;
        }}
        .node-list {{
            margin: 20px 0;
        }}
        .node-item {{
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
            border-left: 4px solid #ccc;
        }}
        .node-item.axiom {{ background: #E8F5E9; border-color: #4CAF50; }}
        .node-item.lemma {{ background: #E3F2FD; border-color: #2196F3; }}
        .node-item.theorem {{ background: #FFF3E0; border-color: #FF9800; }}
        .node-item.verified {{ border-color: #4CAF50; }}
        .node-item.failed {{ border-color: #F44336; }}
        .node-header {{
            font-weight: bold;
            margin-bottom: 8px;
        }}
        .node-statement {{
            font-style: italic;
            color: #555;
            margin: 8px 0;
        }}
        .proof-steps {{
            margin-top: 10px;
            padding-left: 20px;
        }}
        .proof-step {{
            margin: 5px 0;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Formal Verification Proof Report</h1>

        <div class="stats">
            <div class="stat-card total">
                <div class="stat-value">{total_nodes}</div>
                <div class="stat-label">Total Proof Elements</div>
            </div>
            <div class="stat-card verified">
                <div class="stat-value">{verified_count}</div>
                <div class="stat-label">Verified</div>
            </div>
            <div class="stat-card failed">
                <div class="stat-value">{failed_count}</div>
                <div class="stat-label">Failed</div>
            </div>
        </div>

        <h2>Proof Tree Elements</h2>
        <div class="node-list">
"""

        # Add nodes grouped by type
        for node_type in ["axiom", "lemma", "theorem", "corollary"]:
            nodes_of_type = [
                (node_id, data)
                for node_id, data in self.graph.nodes(data=True)
                if data.get("type") == node_type
            ]

            if nodes_of_type:
                html += f"<h3>{node_type.title()}s</h3>\n"

                for node_id, data in nodes_of_type:
                    status = data.get("status", "unknown")
                    label = data.get("label", node_id)
                    statement = data.get("statement", "")
                    proof_steps = data.get("proof_steps", [])

                    html += f'<div class="node-item {node_type} {status}">\n'
                    html += f'  <div class="node-header">{label}</div>\n'

                    if statement:
                        html += f'  <div class="node-statement">{statement}</div>\n'

                    if proof_steps:
                        html += '  <div class="proof-steps">\n'
                        html += "    <strong>Proof steps:</strong>\n"
                        for step in proof_steps:
                            html += f'    <div class="proof-step">• {step}</div>\n'
                        html += "  </div>\n"

                    html += "</div>\n"

        html += """
        </div>
    </div>
</body>
</html>
"""

        return html

    def export_json(self, output_path: Path) -> Path:
        """Export proof tree as JSON for further processing.

        Args:
            output_path: Path to save JSON file

        Returns:
            Path to JSON file
        """
        # Convert results to dict and handle enum serialization
        results_data = []
        for result in self.proof_tree.results:
            result_dict = asdict(result)
            # Convert ProofStatus enum to string value
            if "status" in result_dict and hasattr(result_dict["status"], "value"):
                result_dict["status"] = result_dict["status"].value
            results_data.append(result_dict)

        data: Dict[str, Any] = {
            "nodes": {},
            "edges": [],
            "results": results_data,
        }

        for node_id, node_data in self.graph.nodes(data=True):
            data["nodes"][node_id] = {
                "id": node_id,
                "label": node_data.get("label", ""),
                "type": node_data.get("type", ""),
                "statement": node_data.get("statement", ""),
                "status": node_data.get("status", "unknown"),
                "proof_steps": node_data.get("proof_steps", []),
            }

        edges_list: List[Dict[str, Any]] = []
        for edge in self.graph.edges():
            edges_list.append({"source": edge[0], "target": edge[1]})
        data["edges"] = edges_list

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        return output_path
