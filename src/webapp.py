#!/usr/bin/env python3
"""
Flask webapp for visualizing biomedical knowledge graph edge influences.
"""

from flask import Flask, render_template, request, jsonify
import csv
import os
import json
from collections import defaultdict

app = Flask(__name__)

class GraphData:
    def __init__(self):
        self.data = []
        self.test_edges = set()
        self.train_edges = set()
        
    def load_data(self, filename, max_edges=None):
        """Load CSV data and prepare for visualization."""
        self.data = []
        self.test_edges = set()
        self.train_edges = set()
        
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for i, row in enumerate(reader):
                    if max_edges and i >= max_edges:
                        break
                        
                    # Store the row data
                    self.data.append(row)
                    
                    # Track unique edges
                    test_edge = (row['TestHead'], row['TestRel'], row['TestTail'])
                    train_edge = (row['TrainHead'], row['TrainRel'], row['TrainTail'])
                    
                    self.test_edges.add(test_edge)
                    self.train_edges.add(train_edge)
                    
        except Exception as e:
            print(f"Error loading data: {e}")
            
    def get_graph_data(self, dehair=False):
        """Convert data to format suitable for D3.js visualization."""
        nodes = {}
        links = []
        test_edge_info = None
        
        # Process all rows to collect training edges and entities
        for row in self.data:
            # Store test edge info (should be same for all rows)
            if test_edge_info is None:
                test_edge_info = {
                    'head': row['TestHead'],
                    'head_label': row['TestHead_label'],
                    'tail': row['TestTail'], 
                    'tail_label': row['TestTail_label'],
                    'relation': row['TestRel_label']
                }
            
            score = float(row['TracInScore'])
            
            # Only add entities that appear in training edges
            train_entities = [
                (row['TrainHead'], row['TrainHead_label']),
                (row['TrainTail'], row['TrainTail_label'])
            ]
            
            for curie, label in train_entities:
                if curie not in nodes:
                    # Determine entity type based on where it appears
                    entity_type = 'train_entity'  # Default
                    
                    # Check if this is a test entity (TestHead or TestTail)
                    if curie == row['TestHead'] or curie == row['TestTail']:
                        entity_type = 'test_entity'  # Red for test entities
                    
                    nodes[curie] = {
                        'id': curie,
                        'label': label,
                        'type': entity_type,
                        'curie': curie,
                        'degree': 0  # Will count edges
                    }
                else:
                    # If entity already exists and we find it's also a test entity, mark it as test
                    if (curie == row['TestHead'] or curie == row['TestTail']) and nodes[curie]['type'] == 'train_entity':
                        nodes[curie]['type'] = 'test_entity'
            
            # Track unique connections for each node
            if 'connections' not in nodes[row['TrainHead']]:
                nodes[row['TrainHead']]['connections'] = set()
            if 'connections' not in nodes[row['TrainTail']]:
                nodes[row['TrainTail']]['connections'] = set()
            
            nodes[row['TrainHead']]['connections'].add(row['TrainTail'])
            nodes[row['TrainTail']]['connections'].add(row['TrainHead'])
            
            # Add train edge (this is the actual edge we want to show)
            train_edge = {
                'source': row['TrainHead'],
                'target': row['TrainTail'],
                'type': 'train_edge',
                'relation': row['TrainRel_label'],
                'score': score,
                'width': max(1, score * 10)  # Scale line width by score
            }
            links.append(train_edge)
            
            # Debug: print first few edges
            if len(links) <= 3:
                print(f"Added edge: {row['TrainHead']} -> {row['TrainTail']}")
                print(f"Score: {score}, Relation: {row['TrainRel_label']}")
        
        # Calculate degree based on unique connections
        for node in nodes.values():
            node['degree'] = len(node.get('connections', set()))
        
        # Store original counts before de-hairing
        original_node_count = len(nodes)
        original_link_count = len(links)
        
        # Apply iterative de-hairing if requested
        if dehair:
            iterations = 0
            max_iterations = 100  # Safety limit
            
            while iterations < max_iterations:
                # Find nodes with degree = 1
                degree_one_nodes = {curie for curie, node in nodes.items() if node['degree'] == 1}
                
                if not degree_one_nodes:
                    break  # No more degree-1 nodes to remove
                
                print(f"De-hairing iteration {iterations + 1}: removing {len(degree_one_nodes)} degree-1 nodes")
                
                # Remove degree-1 nodes
                nodes = {curie: node for curie, node in nodes.items() if node['degree'] > 1}
                
                # Remove links that involve degree-1 nodes
                links = [link for link in links if 
                        link['source'] not in degree_one_nodes and 
                        link['target'] not in degree_one_nodes]
                
                # Recalculate unique connections for remaining nodes
                for node in nodes.values():
                    node['connections'] = set()
                
                for link in links:
                    if link['source'] in nodes and link['target'] in nodes:
                        nodes[link['source']]['connections'].add(link['target'])
                        nodes[link['target']]['connections'].add(link['source'])
                
                # Update degrees based on unique connections
                for node in nodes.values():
                    node['degree'] = len(node['connections'])
                
                iterations += 1
            
            print(f"De-hairing completed after {iterations} iterations")
        
        # Add prediction info as metadata
        prediction_info = {
            'test_edge': test_edge_info,
            'total_influences': len(self.data)
        } if test_edge_info else None
        
        # Add statistics
        stats = {
            'original_nodes': original_node_count,
            'original_links': original_link_count,
            'filtered_nodes': len(nodes),
            'filtered_links': len(links),
            'removed_nodes': original_node_count - len(nodes),
            'removed_links': original_link_count - len(links),
            'dehaired': dehair
        }
        
        # Clean up nodes - remove non-serializable connections set
        cleaned_nodes = []
        for node in nodes.values():
            cleaned_node = {k: v for k, v in node.items() if k != 'connections'}
            cleaned_nodes.append(cleaned_node)
        
        return {
            'nodes': cleaned_nodes,
            'links': links,
            'prediction_info': prediction_info,
            'stats': stats
        }

# Global graph data instance
graph_data = GraphData()

@app.route('/')
def index():
    """Main page with graph visualization."""
    return render_template('index.html')

@app.route('/api/datasets')
def get_datasets():
    """API endpoint to get list of available datasets."""
    filtered_dir = '../filtered_data'
    datasets = []
    
    if os.path.exists(filtered_dir):
        for file in os.listdir(filtered_dir):
            if file.endswith('.csv'):
                # Create a clean display name from filename
                display_name = file.replace('.csv', '').replace('_', ' ').title()
                datasets.append({
                    'filename': file,
                    'display_name': display_name,
                    'path': os.path.join(filtered_dir, file)
                })
    
    # Sort by display name for consistent ordering
    datasets.sort(key=lambda x: x['display_name'])
    
    return jsonify(datasets)

@app.route('/api/data')
def get_data():
    """API endpoint to get graph data."""
    max_edges = request.args.get('max_edges', type=int)
    dehair = request.args.get('dehair', 'false').lower() == 'true'
    dataset = request.args.get('dataset')  # New parameter for dataset selection
    
    # Find available data files
    filtered_dir = '../filtered_data'
    available_files = []
    
    if os.path.exists(filtered_dir):
        for file in os.listdir(filtered_dir):
            if file.endswith('.csv'):
                available_files.append(os.path.join(filtered_dir, file))
    
    if not available_files:
        return jsonify({'error': 'No data files found'})
    
    # Select data file based on dataset parameter
    data_file = None
    if dataset:
        # Look for the specified dataset
        for file_path in available_files:
            if os.path.basename(file_path) == dataset:
                data_file = file_path
                break
        
        if not data_file:
            return jsonify({'error': f'Dataset "{dataset}" not found'})
    else:
        # Use first available file as default
        data_file = available_files[0]
    
    graph_data.load_data(data_file, max_edges)
    
    result = graph_data.get_graph_data(dehair=dehair)
    # Add dataset info to response
    result['dataset_info'] = {
        'filename': os.path.basename(data_file),
        'display_name': os.path.basename(data_file).replace('.csv', '').replace('_', ' ').title()
    }
    
    return jsonify(result)

@app.route('/api/stats')
def get_stats():
    """Get statistics about the loaded data."""
    return jsonify({
        'total_rows': len(graph_data.data),
        'test_edges': len(graph_data.test_edges),
        'train_edges': len(graph_data.train_edges)
    })

if __name__ == '__main__':
    # Create templates directory
    os.makedirs('templates', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5090)