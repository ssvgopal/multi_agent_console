"""
ThoughtGraphAnalyzer for MultiAgentConsole.

This module provides tools for analyzing user queries as graphs to identify
gaps in thinking and suggest improvements.
"""

import re
import logging
import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Set, Any, Optional
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Download required NLTK resources
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')


class ThoughtGraphAnalyzer:
    """Analyzes user queries as thought graphs to identify gaps and suggest improvements."""
    
    def __init__(self, language: str = "english"):
        """Initialize the ThoughtGraphAnalyzer.
        
        Args:
            language: Language for stopwords and analysis
        """
        self.language = language
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words(language))
        self.custom_stop_words = {
            "would", "could", "should", "may", "might", "must", "need",
            "want", "like", "please", "help", "thanks", "thank", "you"
        }
        self.stop_words.update(self.custom_stop_words)
        
        # Graph data
        self.graph = nx.Graph()
        self.query_history = []
        self.concept_frequency = Counter()
        self.concept_relations = defaultdict(int)
        
        logging.info("ThoughtGraphAnalyzer initialized")
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze a user query and extract concepts and relationships.
        
        Args:
            query: The user's query text
            
        Returns:
            Dictionary with analysis results
        """
        # Store query in history
        self.query_history.append(query)
        
        # Extract concepts and relationships
        concepts = self._extract_concepts(query)
        relationships = self._extract_relationships(concepts)
        
        # Update the graph
        self._update_graph(concepts, relationships)
        
        # Analyze the graph
        central_concepts = self._identify_central_concepts()
        missing_concepts = self._identify_missing_concepts()
        structural_gaps = self._identify_structural_gaps()
        
        # Generate suggestions
        suggestions = self._generate_suggestions(central_concepts, missing_concepts, structural_gaps)
        
        return {
            "concepts": concepts,
            "relationships": relationships,
            "central_concepts": central_concepts,
            "missing_concepts": missing_concepts,
            "structural_gaps": structural_gaps,
            "suggestions": suggestions
        }
    
    def visualize_graph(self, output_path: Optional[str] = None) -> str:
        """Visualize the thought graph.
        
        Args:
            output_path: Path to save the visualization (optional)
            
        Returns:
            Path to the saved visualization or description
        """
        if len(self.graph.nodes()) == 0:
            return "Graph is empty. No queries have been analyzed yet."
        
        plt.figure(figsize=(12, 8))
        
        # Calculate node sizes based on centrality
        centrality = nx.degree_centrality(self.graph)
        node_sizes = [5000 * centrality[node] for node in self.graph.nodes()]
        
        # Calculate edge weights
        edge_weights = [self.graph[u][v]['weight'] * 2 for u, v in self.graph.edges()]
        
        # Generate layout
        pos = nx.spring_layout(self.graph, k=0.3, iterations=50)
        
        # Draw the graph
        nx.draw_networkx_nodes(self.graph, pos, node_size=node_sizes, alpha=0.7, 
                              node_color="skyblue")
        nx.draw_networkx_edges(self.graph, pos, width=edge_weights, alpha=0.5, 
                              edge_color="gray")
        nx.draw_networkx_labels(self.graph, pos, font_size=10, font_family="sans-serif")
        
        plt.axis('off')
        plt.title("Thought Graph Analysis")
        
        if output_path:
            plt.savefig(output_path, format="png", dpi=300, bbox_inches="tight")
            plt.close()
            return output_path
        else:
            temp_path = "thought_graph_analysis.png"
            plt.savefig(temp_path, format="png", dpi=300, bbox_inches="tight")
            plt.close()
            return temp_path
    
    def get_query_improvement_suggestions(self, query: str) -> List[str]:
        """Generate suggestions to improve a query based on graph analysis.
        
        Args:
            query: The user's query text
            
        Returns:
            List of suggestions to improve the query
        """
        # Analyze the query
        analysis = self.analyze_query(query)
        
        # Return the suggestions
        return analysis["suggestions"]
    
    def reset_graph(self) -> None:
        """Reset the thought graph and analysis data."""
        self.graph = nx.Graph()
        self.query_history = []
        self.concept_frequency = Counter()
        self.concept_relations = defaultdict(int)
        logging.info("Thought graph reset")
    
    def _extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text.
        
        Args:
            text: Input text
            
        Returns:
            List of key concepts
        """
        # Tokenize and clean
        tokens = word_tokenize(text.lower())
        
        # Remove stopwords and punctuation
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens 
                 if token.isalnum() and token not in self.stop_words and len(token) > 2]
        
        # Count frequency
        for token in tokens:
            self.concept_frequency[token] += 1
        
        return tokens
    
    def _extract_relationships(self, concepts: List[str]) -> List[Tuple[str, str]]:
        """Extract relationships between concepts.
        
        Args:
            concepts: List of concepts
            
        Returns:
            List of concept pairs representing relationships
        """
        relationships = []
        
        # Create relationships between concepts that appear close to each other
        for i in range(len(concepts) - 1):
            for j in range(i + 1, min(i + 4, len(concepts))):
                relationship = tuple(sorted([concepts[i], concepts[j]]))
                relationships.append(relationship)
                self.concept_relations[relationship] += 1
        
        return relationships
    
    def _update_graph(self, concepts: List[str], relationships: List[Tuple[str, str]]) -> None:
        """Update the thought graph with new concepts and relationships.
        
        Args:
            concepts: List of concepts
            relationships: List of relationships between concepts
        """
        # Add nodes (concepts)
        for concept in concepts:
            if concept in self.graph:
                self.graph.nodes[concept]['weight'] = self.concept_frequency[concept]
            else:
                self.graph.add_node(concept, weight=self.concept_frequency[concept])
        
        # Add edges (relationships)
        for concept1, concept2 in relationships:
            if self.graph.has_edge(concept1, concept2):
                self.graph[concept1][concept2]['weight'] += 1
            else:
                self.graph.add_edge(concept1, concept2, weight=1)
    
    def _identify_central_concepts(self) -> List[Tuple[str, float]]:
        """Identify central concepts in the thought graph.
        
        Returns:
            List of (concept, centrality_score) tuples
        """
        if len(self.graph.nodes()) == 0:
            return []
        
        # Calculate centrality measures
        degree_centrality = nx.degree_centrality(self.graph)
        betweenness_centrality = nx.betweenness_centrality(self.graph)
        
        # Combine centrality measures
        combined_centrality = {
            node: (0.7 * degree_centrality[node] + 0.3 * betweenness_centrality[node])
            for node in self.graph.nodes()
        }
        
        # Sort by centrality score
        central_concepts = sorted(combined_centrality.items(), key=lambda x: x[1], reverse=True)
        
        # Return top concepts
        return central_concepts[:5]
    
    def _identify_missing_concepts(self) -> List[str]:
        """Identify potentially missing concepts based on the graph structure.
        
        Returns:
            List of potentially missing concepts
        """
        missing_concepts = []
        
        # Look for common co-occurrences in the general knowledge
        # This is a simplified approach - in a real system, you might use
        # external knowledge bases or word embeddings
        common_pairs = {
            "data": ["analysis", "processing", "visualization", "science"],
            "machine": ["learning", "intelligence", "algorithm"],
            "neural": ["network", "deep", "learning"],
            "user": ["interface", "experience", "interaction"],
            "software": ["development", "engineering", "design"],
            "cloud": ["computing", "storage", "service"],
            "security": ["privacy", "encryption", "protection"],
            "mobile": ["app", "device", "phone"],
            "web": ["development", "design", "application"],
            "database": ["sql", "nosql", "management"]
        }
        
        # Check if one concept is present but common pairs are missing
        for concept, related_concepts in common_pairs.items():
            if concept in self.graph:
                for related in related_concepts:
                    if related not in self.graph or not self.graph.has_edge(concept, related):
                        if related not in missing_concepts:
                            missing_concepts.append(related)
        
        return missing_concepts[:5]  # Limit to top 5
    
    def _identify_structural_gaps(self) -> List[Tuple[str, str]]:
        """Identify structural gaps in the thought graph.
        
        Returns:
            List of concept pairs that could be connected
        """
        if len(self.graph.nodes()) < 3:
            return []
        
        structural_gaps = []
        
        # Find nodes that are 2 hops away but not directly connected
        for node1 in self.graph.nodes():
            for node2 in self.graph.nodes():
                if node1 != node2 and not self.graph.has_edge(node1, node2):
                    # Check if they have common neighbors
                    common_neighbors = set(self.graph.neighbors(node1)) & set(self.graph.neighbors(node2))
                    if common_neighbors:
                        structural_gaps.append((node1, node2))
        
        # Sort by the number of common neighbors (most promising gaps first)
        def count_common_neighbors(pair):
            node1, node2 = pair
            return len(set(self.graph.neighbors(node1)) & set(self.graph.neighbors(node2)))
        
        structural_gaps.sort(key=count_common_neighbors, reverse=True)
        
        return structural_gaps[:3]  # Limit to top 3
    
    def _generate_suggestions(self, central_concepts, missing_concepts, structural_gaps) -> List[str]:
        """Generate suggestions to improve the query based on graph analysis.
        
        Args:
            central_concepts: List of central concepts
            missing_concepts: List of potentially missing concepts
            structural_gaps: List of structural gaps
            
        Returns:
            List of suggestions
        """
        suggestions = []
        
        # Suggest focusing on central concepts
        if central_concepts:
            central_terms = ", ".join([concept for concept, _ in central_concepts[:3]])
            suggestions.append(f"Consider focusing your query more on these key concepts: {central_terms}")
        
        # Suggest including missing concepts
        if missing_concepts:
            missing_terms = ", ".join(missing_concepts[:3])
            suggestions.append(f"You might want to include these related concepts: {missing_terms}")
        
        # Suggest exploring connections between concepts
        if structural_gaps:
            gap_pairs = [f"{a} and {b}" for a, b in structural_gaps[:2]]
            gap_text = ", ".join(gap_pairs)
            suggestions.append(f"Consider exploring the relationship between {gap_text}")
        
        # Suggest broadening or narrowing focus
        if len(self.graph.nodes()) > 15:
            suggestions.append("Your query covers many concepts. Consider narrowing your focus for more specific results.")
        elif len(self.graph.nodes()) < 3:
            suggestions.append("Your query is quite narrow. Consider broadening it to explore more connections.")
        
        return suggestions


class ThoughtGraphManager:
    """Manages thought graph analysis and plugin integrations."""
    
    def __init__(self, data_dir: str = "data/thought_graphs"):
        """Initialize the ThoughtGraphManager.
        
        Args:
            data_dir: Directory for storing thought graph data
        """
        self.data_dir = data_dir
        self.analyzer = ThoughtGraphAnalyzer()
        self.plugins = {}
        
        logging.info("ThoughtGraphManager initialized")
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze a user query using the thought graph analyzer.
        
        Args:
            query: The user's query text
            
        Returns:
            Dictionary with analysis results
        """
        return self.analyzer.analyze_query(query)
    
    def get_query_suggestions(self, query: str) -> List[str]:
        """Get suggestions to improve a query.
        
        Args:
            query: The user's query text
            
        Returns:
            List of suggestions
        """
        return self.analyzer.get_query_improvement_suggestions(query)
    
    def visualize_graph(self, output_path: Optional[str] = None) -> str:
        """Visualize the thought graph.
        
        Args:
            output_path: Path to save the visualization (optional)
            
        Returns:
            Path to the saved visualization or description
        """
        return self.analyzer.visualize_graph(output_path)
    
    def reset_graph(self) -> None:
        """Reset the thought graph and analysis data."""
        self.analyzer.reset_graph()
    
    def register_plugin(self, plugin_id: str, plugin) -> bool:
        """Register a graph analysis plugin.
        
        Args:
            plugin_id: Unique plugin ID
            plugin: Plugin instance
            
        Returns:
            True if successful, False otherwise
        """
        if plugin_id in self.plugins:
            logging.warning(f"Plugin {plugin_id} already registered")
            return False
        
        self.plugins[plugin_id] = plugin
        logging.info(f"Graph analysis plugin registered: {plugin_id}")
        return True
    
    def unregister_plugin(self, plugin_id: str) -> bool:
        """Unregister a graph analysis plugin.
        
        Args:
            plugin_id: Plugin ID to unregister
            
        Returns:
            True if successful, False otherwise
        """
        if plugin_id not in self.plugins:
            logging.warning(f"Plugin {plugin_id} not registered")
            return False
        
        del self.plugins[plugin_id]
        logging.info(f"Graph analysis plugin unregistered: {plugin_id}")
        return True
    
    def analyze_with_plugin(self, plugin_id: str, query: str) -> Dict[str, Any]:
        """Analyze a query using a specific plugin.
        
        Args:
            plugin_id: Plugin ID to use
            query: The user's query text
            
        Returns:
            Analysis results from the plugin
        """
        if plugin_id not in self.plugins:
            raise ValueError(f"Plugin {plugin_id} not registered")
        
        return self.plugins[plugin_id].analyze(query)
    
    def list_plugins(self) -> List[Dict[str, str]]:
        """List all registered graph analysis plugins.
        
        Returns:
            List of plugin information dictionaries
        """
        return [
            {"id": plugin_id, "name": plugin.name, "description": plugin.description}
            for plugin_id, plugin in self.plugins.items()
        ]
