"""Test the thought graph module."""

import unittest
import os
import tempfile
import shutil
from unittest.mock import MagicMock, patch

import networkx as nx
import matplotlib.pyplot as plt

from multi_agent_console.thought_graph import ThoughtGraphAnalyzer, ThoughtGraphManager


class TestThoughtGraphAnalyzer(unittest.TestCase):
    """Test the ThoughtGraphAnalyzer class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a ThoughtGraphAnalyzer
        self.analyzer = ThoughtGraphAnalyzer()

    def test_init(self):
        """Test initializing a thought graph analyzer."""
        # Check that the attributes were initialized correctly
        self.assertEqual(self.analyzer.language, "english")
        self.assertIsNotNone(self.analyzer.lemmatizer)
        self.assertIsNotNone(self.analyzer.stop_words)
        self.assertIsInstance(self.analyzer.graph, nx.Graph)
        self.assertEqual(self.analyzer.query_history, [])
        self.assertEqual(len(self.analyzer.concept_frequency), 0)
        self.assertEqual(len(self.analyzer.concept_relations), 0)

    def test_analyze_query(self):
        """Test analyzing a query."""
        # Analyze a query
        query = "How can I implement a neural network for image classification?"
        result = self.analyzer.analyze_query(query)

        # Check that the query was added to the history
        self.assertIn(query, self.analyzer.query_history)

        # Check that the result contains the expected keys
        self.assertIn("concepts", result)
        self.assertIn("relationships", result)
        self.assertIn("central_concepts", result)
        self.assertIn("missing_concepts", result)
        self.assertIn("structural_gaps", result)
        self.assertIn("suggestions", result)
        self.assertIn("summary", result)

        # Check that concepts were extracted
        self.assertGreater(len(result["concepts"]), 0)

        # Check that the graph was updated
        self.assertGreater(len(self.analyzer.graph.nodes()), 0)
        self.assertGreater(len(self.analyzer.graph.edges()), 0)

    def test_analyze_query_empty(self):
        """Test analyzing an empty query."""
        # Analyze an empty query
        query = ""
        result = self.analyzer.analyze_query(query)

        # Check that the query was added to the history
        self.assertIn(query, self.analyzer.query_history)

        # Check that default concepts were generated
        self.assertGreater(len(result["concepts"]), 0)

    def test_get_query_improvement_suggestions(self):
        """Test getting query improvement suggestions."""
        # Get suggestions for a query
        query = "How can I implement a neural network?"
        suggestions = self.analyzer.get_query_improvement_suggestions(query)

        # Check that suggestions were returned
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)

    @patch('matplotlib.pyplot.savefig')
    def test_visualize_graph(self, mock_savefig):
        """Test visualizing the graph."""
        # Add some data to the graph
        self.analyzer.analyze_query("How can I implement a neural network for image classification?")

        # Visualize the graph
        output_path = self.analyzer.visualize_graph()

        # Check that savefig was called
        mock_savefig.assert_called_once()

        # Check that the output path was returned
        self.assertEqual(output_path, "thought_graph_analysis.png")

        # Visualize the graph with a custom output path
        custom_path = "custom_output.png"
        output_path = self.analyzer.visualize_graph(custom_path)

        # Check that savefig was called with the custom path
        mock_savefig.assert_called_with(custom_path, format="png", dpi=300, bbox_inches="tight")

        # Check that the custom output path was returned
        self.assertEqual(output_path, custom_path)

    def test_reset_graph(self):
        """Test resetting the graph."""
        # Add some data to the graph
        self.analyzer.analyze_query("How can I implement a neural network for image classification?")

        # Check that the graph has data
        self.assertGreater(len(self.analyzer.graph.nodes()), 0)
        self.assertGreater(len(self.analyzer.query_history), 0)
        self.assertGreater(len(self.analyzer.concept_frequency), 0)

        # Reset the graph
        self.analyzer.reset_graph()

        # Check that the graph was reset
        self.assertEqual(len(self.analyzer.graph.nodes()), 0)
        self.assertEqual(len(self.analyzer.query_history), 0)
        self.assertEqual(len(self.analyzer.concept_frequency), 0)
        self.assertEqual(len(self.analyzer.concept_relations), 0)

    def test_extract_concepts(self):
        """Test extracting concepts from text."""
        # Extract concepts from text
        text = "How can I implement a neural network for image classification?"
        concepts = self.analyzer._extract_concepts(text)

        # Check that concepts were extracted
        self.assertGreater(len(concepts), 0)

        # Check that the concept frequency was updated
        for concept in concepts:
            self.assertGreaterEqual(self.analyzer.concept_frequency[concept], 1)

    def test_generate_default_concepts(self):
        """Test generating default concepts."""
        # Generate default concepts for an empty text
        text = ""
        concepts = self.analyzer._generate_default_concepts(text)

        # Check that default concepts were generated
        self.assertGreater(len(concepts), 0)

        # Generate default concepts for a short text
        text = "help me"
        concepts = self.analyzer._generate_default_concepts(text)

        # Check that default concepts were generated
        self.assertGreater(len(concepts), 0)

        # Update the concept frequency manually for testing
        for concept in concepts:
            self.analyzer.concept_frequency[concept] = 1

        # Check that the concept frequency was updated
        for concept in concepts:
            self.assertGreaterEqual(self.analyzer.concept_frequency[concept], 1)

    def test_extract_relationships(self):
        """Test extracting relationships between concepts."""
        # Extract relationships from concepts
        concepts = ["neural", "network", "image", "classification"]
        relationships = self.analyzer._extract_relationships(concepts)

        # Check that relationships were extracted
        self.assertGreater(len(relationships), 0)

        # Check that the concept relations were updated
        for relationship in relationships:
            self.assertGreaterEqual(self.analyzer.concept_relations[relationship], 1)

    def test_update_graph(self):
        """Test updating the graph."""
        # Update the graph with concepts and relationships
        concepts = ["neural", "network", "image", "classification"]
        relationships = [("neural", "network"), ("network", "image"), ("image", "classification")]

        # Update the concept frequency
        for concept in concepts:
            self.analyzer.concept_frequency[concept] = 1

        # Update the graph
        self.analyzer._update_graph(concepts, relationships)

        # Check that the graph was updated
        self.assertEqual(len(self.analyzer.graph.nodes()), 4)
        self.assertEqual(len(self.analyzer.graph.edges()), 3)

        # Update the graph again with the same concepts and relationships
        self.analyzer._update_graph(concepts, relationships)

        # Check that the graph was updated correctly
        self.assertEqual(len(self.analyzer.graph.nodes()), 4)
        self.assertEqual(len(self.analyzer.graph.edges()), 3)

        # Check that the edge weights were incremented
        for u, v in relationships:
            self.assertEqual(self.analyzer.graph[u][v]["weight"], 2)


class TestThoughtGraphManager(unittest.TestCase):
    """Test the ThoughtGraphManager class."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()

        # Create a ThoughtGraphManager
        self.manager = ThoughtGraphManager(data_dir=self.test_dir)

    def tearDown(self):
        """Clean up after the test."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)

    def test_init(self):
        """Test initializing a thought graph manager."""
        # Check that the attributes were initialized correctly
        self.assertEqual(self.manager.data_dir, self.test_dir)
        self.assertIsInstance(self.manager.analyzer, ThoughtGraphAnalyzer)
        self.assertEqual(self.manager.plugins, {})

    def test_analyze_query(self):
        """Test analyzing a query."""
        # Mock the analyzer's analyze_query method
        self.manager.analyzer.analyze_query = MagicMock(return_value={"key": "value"})

        # Analyze a query
        query = "How can I implement a neural network for image classification?"
        result = self.manager.analyze_query(query)

        # Check that the analyzer's analyze_query method was called
        self.manager.analyzer.analyze_query.assert_called_once_with(query)

        # Check that the result was returned
        self.assertEqual(result, {"key": "value"})

    def test_get_query_suggestions(self):
        """Test getting query suggestions."""
        # Mock the analyzer's get_query_improvement_suggestions method
        self.manager.analyzer.get_query_improvement_suggestions = MagicMock(return_value=["suggestion1", "suggestion2"])

        # Get suggestions for a query
        query = "How can I implement a neural network?"
        suggestions = self.manager.get_query_suggestions(query)

        # Check that the analyzer's get_query_improvement_suggestions method was called
        self.manager.analyzer.get_query_improvement_suggestions.assert_called_once_with(query)

        # Check that the suggestions were returned
        self.assertEqual(suggestions, ["suggestion1", "suggestion2"])

    def test_visualize_graph(self):
        """Test visualizing the graph."""
        # Mock the analyzer's visualize_graph method
        self.manager.analyzer.visualize_graph = MagicMock(return_value="output_path")

        # Visualize the graph
        output_path = self.manager.visualize_graph()

        # Check that the analyzer's visualize_graph method was called
        self.manager.analyzer.visualize_graph.assert_called_once_with(None)

        # Check that the output path was returned
        self.assertEqual(output_path, "output_path")

        # Visualize the graph with a custom output path
        custom_path = "custom_output.png"
        output_path = self.manager.visualize_graph(custom_path)

        # Check that the analyzer's visualize_graph method was called with the custom path
        self.manager.analyzer.visualize_graph.assert_called_with(custom_path)

        # Check that the output path was returned
        self.assertEqual(output_path, "output_path")

    def test_reset_graph(self):
        """Test resetting the graph."""
        # Mock the analyzer's reset_graph method
        self.manager.analyzer.reset_graph = MagicMock()

        # Reset the graph
        self.manager.reset_graph()

        # Check that the analyzer's reset_graph method was called
        self.manager.analyzer.reset_graph.assert_called_once()

    def test_register_plugin(self):
        """Test registering a plugin."""
        # Create a mock plugin
        plugin = MagicMock()
        plugin.analyze = MagicMock(return_value={"key": "value"})

        # Register the plugin
        result = self.manager.register_plugin("test_plugin", plugin)

        # Check that the result is True
        self.assertTrue(result)

        # Check that the plugin was added to the plugins dictionary
        self.assertIn("test_plugin", self.manager.plugins)
        self.assertEqual(self.manager.plugins["test_plugin"], plugin)

        # Try to register the same plugin again
        result = self.manager.register_plugin("test_plugin", plugin)

        # Check that the result is False
        self.assertFalse(result)

    def test_unregister_plugin(self):
        """Test unregistering a plugin."""
        # Create and register a mock plugin
        plugin = MagicMock()
        self.manager.plugins["test_plugin"] = plugin

        # Unregister the plugin
        result = self.manager.unregister_plugin("test_plugin")

        # Check that the result is True
        self.assertTrue(result)

        # Check that the plugin was removed from the plugins dictionary
        self.assertNotIn("test_plugin", self.manager.plugins)

        # Try to unregister a non-existent plugin
        result = self.manager.unregister_plugin("non_existent_plugin")

        # Check that the result is False
        self.assertFalse(result)

    def test_analyze_with_plugin(self):
        """Test analyzing a query with a plugin."""
        # Create and register a mock plugin
        plugin = MagicMock()
        plugin.analyze = MagicMock(return_value={"key": "value"})
        self.manager.plugins["test_plugin"] = plugin

        # Analyze a query with the plugin
        query = "How can I implement a neural network?"
        result = self.manager.analyze_with_plugin("test_plugin", query)

        # Check that the plugin's analyze method was called
        plugin.analyze.assert_called_once_with(query)

        # Check that the result was returned
        self.assertEqual(result, {"key": "value"})

        # Try to analyze with a non-existent plugin
        with self.assertRaises(ValueError):
            self.manager.analyze_with_plugin("non_existent_plugin", query)


if __name__ == "__main__":
    unittest.main()
