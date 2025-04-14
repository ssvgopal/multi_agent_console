"""
Graph Analysis Plugin Interface for MultiAgentConsole.

This module provides a base class and interface for graph analysis plugins.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class GraphAnalysisPlugin(ABC):
    """Base class for graph analysis plugins."""
    
    def __init__(self, plugin_id: str, name: str, description: str = ""):
        """Initialize a new graph analysis plugin.
        
        Args:
            plugin_id: Unique plugin ID
            name: Plugin name
            description: Plugin description
        """
        self.plugin_id = plugin_id
        self.name = name
        self.description = description
        self.is_enabled = False
        
        logging.info(f"Graph analysis plugin created: {name} ({plugin_id})")
    
    @abstractmethod
    def analyze(self, text: str) -> Dict[str, Any]:
        """Analyze text and return results.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with analysis results
        """
        pass
    
    @abstractmethod
    def visualize(self, text: str, output_path: Optional[str] = None) -> str:
        """Visualize text as a graph.
        
        Args:
            text: Text to visualize
            output_path: Path to save the visualization (optional)
            
        Returns:
            Path to the saved visualization or description
        """
        pass
    
    @abstractmethod
    def get_suggestions(self, text: str) -> List[str]:
        """Get suggestions to improve the text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of suggestions
        """
        pass
    
    def enable(self) -> bool:
        """Enable the plugin.
        
        Returns:
            True if successful, False otherwise
        """
        self.is_enabled = True
        logging.info(f"Graph analysis plugin enabled: {self.name} ({self.plugin_id})")
        return True
    
    def disable(self) -> bool:
        """Disable the plugin.
        
        Returns:
            True if successful, False otherwise
        """
        self.is_enabled = False
        logging.info(f"Graph analysis plugin disabled: {self.name} ({self.plugin_id})")
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the plugin to a dictionary.
        
        Returns:
            Dictionary representation of the plugin
        """
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "description": self.description,
            "is_enabled": self.is_enabled
        }


class InfraNodusPlugin(GraphAnalysisPlugin):
    """Plugin for InfraNodus-like text network analysis."""
    
    def __init__(self, api_key: str = None):
        """Initialize the InfraNodus plugin.
        
        Args:
            api_key: API key for InfraNodus (optional)
        """
        super().__init__(
            plugin_id="infranodus_plugin",
            name="InfraNodus Text Network Analysis",
            description="Analyzes text as a network to identify key concepts, relationships, and gaps"
        )
        self.api_key = api_key
        
        # Import the ThoughtGraphAnalyzer as a fallback if no API key is provided
        from ..thought_graph import ThoughtGraphAnalyzer
        self.analyzer = ThoughtGraphAnalyzer()
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """Analyze text using InfraNodus or local fallback.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with analysis results
        """
        if self.api_key:
            # In a real implementation, this would call the InfraNodus API
            # For now, we'll use our local implementation
            logging.info("Using local implementation instead of InfraNodus API")
            
        return self.analyzer.analyze_query(text)
    
    def visualize(self, text: str, output_path: Optional[str] = None) -> str:
        """Visualize text as a network graph.
        
        Args:
            text: Text to visualize
            output_path: Path to save the visualization (optional)
            
        Returns:
            Path to the saved visualization or description
        """
        if self.api_key:
            # In a real implementation, this would call the InfraNodus API
            logging.info("Using local implementation instead of InfraNodus API")
        
        # Analyze the text first to build the graph
        self.analyzer.analyze_query(text)
        
        # Then visualize it
        return self.analyzer.visualize_graph(output_path)
    
    def get_suggestions(self, text: str) -> List[str]:
        """Get suggestions to improve the text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of suggestions
        """
        if self.api_key:
            # In a real implementation, this would call the InfraNodus API
            logging.info("Using local implementation instead of InfraNodus API")
        
        return self.analyzer.get_query_improvement_suggestions(text)


class SimpleGraphPlugin(GraphAnalysisPlugin):
    """A simple graph analysis plugin for demonstration purposes."""
    
    def __init__(self):
        """Initialize the simple graph plugin."""
        super().__init__(
            plugin_id="simple_graph_plugin",
            name="Simple Graph Analysis",
            description="A basic graph analysis plugin for demonstration"
        )
        
        # Import necessary libraries
        import re
        from collections import Counter
        self.re = re
        self.Counter = Counter
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """Perform a simple analysis of the text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with analysis results
        """
        # Simple word frequency analysis
        words = self.re.findall(r'\b\w+\b', text.lower())
        word_freq = self.Counter(words)
        
        # Find most common words
        common_words = word_freq.most_common(5)
        
        # Simple sentence analysis
        sentences = text.split('.')
        sentence_count = len(sentences)
        
        return {
            "word_count": len(words),
            "sentence_count": sentence_count,
            "common_words": common_words,
            "average_words_per_sentence": len(words) / max(1, sentence_count)
        }
    
    def visualize(self, text: str, output_path: Optional[str] = None) -> str:
        """Create a simple visualization of the text.
        
        Args:
            text: Text to visualize
            output_path: Path to save the visualization (optional)
            
        Returns:
            Description of the visualization
        """
        # This is a placeholder - a real implementation would create a visualization
        return "Simple visualization not implemented. Use the InfraNodus plugin for visualization."
    
    def get_suggestions(self, text: str) -> List[str]:
        """Get simple suggestions to improve the text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of suggestions
        """
        analysis = self.analyze(text)
        suggestions = []
        
        # Simple suggestions based on text length
        if analysis["word_count"] < 10:
            suggestions.append("Your query is very short. Consider adding more details.")
        elif analysis["word_count"] > 50:
            suggestions.append("Your query is quite long. Consider breaking it into smaller, focused questions.")
        
        # Suggestions based on sentence structure
        if analysis["average_words_per_sentence"] > 20:
            suggestions.append("Your sentences are quite long. Consider using shorter, clearer sentences.")
        
        # Add a generic suggestion if no specific ones were generated
        if not suggestions:
            suggestions.append("Try to be more specific about what you're looking for.")
        
        return suggestions
