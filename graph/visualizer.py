"""Static graph visualization using matplotlib"""
import matplotlib.pyplot as plt
import networkx as nx
from .builder import load_graph


def visualize_graph(output_path="graph/graph_preview.png"):
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
        
        # Set up the figure
        plt.figure(figsize=(12, 12))
        
        # Use spring layout for node positioning
        pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)
        
        # Draw the nodes
        nx.draw_networkx_nodes(
            G, pos,
            node_color='lightblue',
            node_size=1500,
            alpha=0.9
        )
        
        # Draw the edges
        nx.draw_networkx_edges(
            G, pos,
            edge_color='gray',
            alpha=0.5,
            width=1.5,
            arrows=True,
            arrowsize=15,
            arrowstyle='->'
        )
        
        # Draw the labels
        nx.draw_networkx_labels(
            G, pos,
            font_size=9,
            font_weight='bold',
            font_family='sans-serif'
        )
        
        # Draw edge labels if they exist
        edge_labels = nx.get_edge_attributes(G, 'label')
        if edge_labels:
            nx.draw_networkx_edge_labels(
                G, pos,
                edge_labels,
                font_size=7,
                font_color='darkred',
                alpha=0.7
            )
        
        plt.title("OSINT Knowledge Graph", fontsize=16, fontweight='bold', pad=20)
        plt.axis('off')
        plt.tight_layout()
        
        # Save the figure
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
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
