"""Static graph visualization using matplotlib"""
import matplotlib.pyplot as plt
import networkx as nx
from .builder import load_graph


def visualize_graph(output_path="output/graph_preview.png"):
    """
    Load the knowledge graph and render it as a static PNG.
    
    Args:
        output_path: Where to save the PNG file
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Load the graph
        G = load_graph()
        
        if G.number_of_nodes() == 0:
            print("⚠️  Graph is empty - no nodes to visualize")
            return False
        
        print(f"📊 Visualizing graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
        
        # Set up a larger figure for better spacing
        plt.figure(figsize=(16, 16))
        
        # Use spring layout with a larger k value for wider node distribution
        pos = nx.spring_layout(G, k=1.5, iterations=60, seed=42)
        
        # Color-code nodes by their extracted role type
        node_roles = nx.get_node_attributes(G, 'role')
        def get_node_color(node):
            role = str(node_roles.get(node, 'other')).lower()
            if any(p in role for p in ['person', 'operator', 'concierge', 'manager', 'executioner', 'king']):
                return '#ff8c69'  # Coral/Salmon for people
            elif any(o in role for o in ['org', 'syndicate', 'table', 'network', 'mob']):
                return '#6495ed'  # Cornflower Blue for organizations
            elif any(l in role for l in ['loc', 'sanctuary', 'hotel']):
                return '#3cb371'  # Medium Sea Green for locations
            else:
                return '#dda0dd'  # Plum for others (e.g. source material)
                
        node_colors = [get_node_color(node) for node in G.nodes()]
        
        # Draw the nodes
        nx.draw_networkx_nodes(
            G, pos,
            node_color=node_colors,
            node_size=1800,
            alpha=0.95,
            edgecolors='#555555',
            linewidths=1.5
        )
        
        # Draw the edges
        nx.draw_networkx_edges(
            G, pos,
            edge_color='#888888',
            alpha=0.6,
            width=1.5,
            arrows=True,
            arrowsize=18,
            arrowstyle='->'
        )
        
        # Draw the labels with high-readability background bboxes to prevent overlapping
        nx.draw_networkx_labels(
            G, pos,
            font_size=9,
            font_weight='bold',
            font_family='sans-serif',
            bbox=dict(boxstyle="round,pad=0.3", fc="#ffffff", ec="#dddddd", lw=1, alpha=0.9)
        )
        
        # Draw edge labels if they exist
        edge_labels = nx.get_edge_attributes(G, 'label')
        if edge_labels:
            nx.draw_networkx_edge_labels(
                G, pos,
                edge_labels,
                font_size=7.5,
                font_color='#8b0000',  # Dark red
                alpha=0.85,
                bbox=dict(boxstyle="round,pad=0.2", fc="#ffffff", ec="none", alpha=0.85)
            )
        
        plt.title("OSINT Graph Intelligence Map", fontsize=18, fontweight='bold', pad=20, color='#333333')
        plt.axis('off')
        plt.tight_layout()
        
        # Save the figure with high resolution
        plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
        print(f"✅ Graph saved to: {output_path}")
        
        plt.close()
        return True
        
    except FileNotFoundError:
        print("❌ Graph file not found. Run entity extraction first.")
        return False
    except Exception as e:
        print(f"❌ Visualization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    visualize_graph()
