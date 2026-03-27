"""
Unit tests for prediction accuracy analysis.
"""

import unittest
import pandas as pd
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyze_predictions import (
    parse_actual_winners,
    compare_predictions,
    analyze_scoring_variables,
    generate_recommendations
)


class TestPredictionAnalysis(unittest.TestCase):
    
    def test_parse_actual_winners_dict(self):
        """Test parsing winners from dictionary."""
        winners_dict = {
            ('Track1', 1): 3,
            ('Track1', 2): 5
        }
        result = parse_actual_winners(winners_dict)
        self.assertEqual(result, winners_dict)
    
    def test_parse_actual_winners_string(self):
        """Test parsing winners from string."""
        winners_str = """
        Track1, R1, 3
        Track1, R2, 5
        # Comment line
        Track2, R1, 7
        """
        result = parse_actual_winners(winners_str)
        self.assertEqual(result[('Track1', 1)], 3)
        self.assertEqual(result[('Track1', 2)], 5)
        self.assertEqual(result[('Track2', 1)], 7)
    
    def test_compare_predictions(self):
        """Test comparison of predictions to actuals."""
        # Create sample predictions
        top_picks = pd.DataFrame({
            'Track': ['Track1', 'Track1', 'Track2'],
            'RaceNumber': [1, 2, 1],
            'Box': [3, 5, 7],
            'DogName': ['Dog1', 'Dog2', 'Dog3'],
            'FinalScore': [25.0, 30.0, 28.0]
        })
        
        actual_winners = {
            ('Track1', 1): 3,  # Correct
            ('Track1', 2): 4,  # Incorrect
            ('Track2', 1): 7   # Correct
        }
        
        result = compare_predictions(top_picks, actual_winners)
        
        self.assertEqual(len(result), 3)
        self.assertTrue(result.iloc[0]['Correct'])
        self.assertFalse(result.iloc[1]['Correct'])
        self.assertTrue(result.iloc[2]['Correct'])
    
    def test_analyze_scoring_variables(self):
        """Test scoring variable analysis."""
        # Create sample data
        df_all = pd.DataFrame({
            'Track': ['T1', 'T1', 'T1', 'T1'],
            'RaceNumber': [1, 1, 2, 2],
            'Box': [1, 2, 1, 2],
            'FinalScore': [30, 25, 28, 26],
            'Speed_kmh': [65, 60, 64, 61],
            'ConsistencyIndex': [0.5, 0.3, 0.6, 0.4]
        })
        
        comparison_results = pd.DataFrame({
            'Track': ['T1', 'T1'],
            'RaceNumber': [1, 2],
            'Correct': [True, False]
        })
        
        result = analyze_scoring_variables(df_all, comparison_results)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn('Variable', result.columns)
        self.assertIn('Cohens_D', result.columns)
    
    def test_generate_recommendations(self):
        """Test recommendation generation."""
        # Create sample variable analysis
        variable_analysis = pd.DataFrame({
            'Variable': ['Var1', 'Var2', 'Var3'],
            'Cohens_D': [0.5, -0.4, 0.1],
            'Significant': [True, True, False],
            'Mean_Diff': [0.2, -0.3, 0.05]
        })
        
        recommendations = generate_recommendations(variable_analysis, 40.0)
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        self.assertIn('type', recommendations[0])
        self.assertIn('variables', recommendations[0])


if __name__ == '__main__':
    unittest.main()
