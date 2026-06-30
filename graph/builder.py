import networkx as nx
from ingestion.store import get_all_entity_data, get_all_relationship_data, get_all_aliases
import pickle

G = nx.Graph()


def add_all_entities():
    """Add all entities to the graph with their aliases as node attributes."""
    G.clear()
    entities, roles = get_all_entity_data()
    alias_map = get_all_aliases()
    
    nodes_with_attributes = []
    for node, role in zip(entities, roles):
        # Get aliases for this canonical entity
        aliases = alias_map.get(node, [])
        alias_names = [alias[0] for alias in aliases]
        
        # Create node with role and aliases as attributes
        nodes_with_attributes.append((
            node, 
            {
                "role": role,
                "aliases": alias_names,
                "alias_count": len(alias_names)
            }
        ))
    
    G.add_nodes_from(nodes_with_attributes)

def add_all_relationships():
    origins, destinations, labels = get_all_relationship_data()
    edges_with_attributes = [(origin, destination, {"label": label}) for origin, destination, label in zip(origins, destinations, labels)]
    G.add_edges_from(edges_with_attributes)

def add_entity(entity, role):
    G.add_node(entity, role = role)

def add_relationship(origin, destination, label):
    G.add_edge(origin, destination, label= label)

def save_graph(name= 'output/ER_Graph'):
    with open(f'{name}.pkl', 'wb') as f:
        pickle.dump(G, f)

def load_graph(name= 'output/ER_Graph'):
    with open(f'{name}.pkl', 'rb') as f:
        Graph = pickle.load(f)
        return Graph

if __name__ == "__main__":
    add_entity('hi', 'n')
    add_entity('hi2', 'n')
    add_entity('hi1', 'n')
    print(G.nodes(data=True))