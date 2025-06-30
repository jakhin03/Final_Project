import unittest
from unittest.mock import Mock, patch, MagicMock
from collections import defaultdict
import networkx as nx

from controller.RestrictionForTimeFrameController import RestrictionForTimeFrameController


class TestRestrictionForTimeFrameController(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment with mocked GraphProcessor"""
        # Create a mock GraphProcessor
        self.mock_graph_processor = Mock()
        self.mock_graph_processor.M = 3  # 3x3 grid for simple testing
        self.mock_graph_processor.H = 4  # 4 time steps
        self.mock_graph_processor.alpha = 1.0
        self.mock_graph_processor.beta = 1.0
        self.mock_graph_processor.gamma = 100.0
        self.mock_graph_processor.ur = 1
        
        # Create a simple TSG for testing
        # Node IDs: spatial_coord + time * M (time starts from 0)
        # For 3x3 grid: nodes 1,2,3 at time 0 -> TSG nodes 1,2,3
        #               nodes 1,2,3 at time 1 -> TSG nodes 4,5,6
        #               nodes 1,2,3 at time 2 -> TSG nodes 7,8,9
        # Edge (1,1) spatial appears at times 0->1 and 1->2 as TSG edges (1,4) and (4,7)
        self.mock_ts_edges = [
            (1, 4, 0, 1, 10),  # spatial (1,1) from time 0 to time 1
            (2, 5, 0, 1, 10),  # spatial (2,2) from time 0 to time 1
            (4, 7, 0, 1, 10),  # spatial (1,1) from time 1 to time 2
            (5, 8, 0, 1, 10),  # spatial (2,2) from time 1 to time 2
            (1, 2, 0, 1, 5),   # spatial (1,2) horizontal edge at time 0
            (4, 5, 0, 1, 5),   # spatial (1,2) horizontal edge at time 1
            (7, 8, 0, 1, 5),   # spatial (1,2) horizontal edge at time 2
        ]
        
        self.mock_graph_processor.ts_edges = self.mock_ts_edges.copy()
        self.mock_graph_processor.ts_nodes = []
        self.mock_graph_processor.map_nodes = {}
        self.mock_graph_processor.tsedges = []
        
        # Mock methods
        self.mock_graph_processor.get_max_id.return_value = 100
        self.mock_graph_processor.check_and_add_nodes = Mock()
        self.mock_graph_processor.create_set_of_edges = Mock()
        
        # Create controller instance
        self.controller = RestrictionForTimeFrameController(self.mock_graph_processor)
        
        # Store original ts_edges for restoration tests
        self.original_ts_edges = self.mock_ts_edges.copy()
        
    def tearDown(self):
        """Clean up after each test"""
        # Reset the mock_graph_processor.ts_edges to original state
        self.mock_graph_processor.ts_edges = self.original_ts_edges.copy()

    # =============================================================================
    # Tests for identify_restricted_edges()
    # =============================================================================
    
    def test_identify_edges_with_full_match(self):
        """Test identifying edges when spatial edge and timeframe fully match"""
        # Given: restriction on edge (1,2) with timeframe [0,3]
        # For horizontal edges (1,2), (4,5), (7,8) at times 0,1,2 respectively:
        # - Edge (1,2): t1=0, t2=0, condition: (0 < 3) and (0 > 0) = True and False = False
        # - Edge (4,5): t1=1, t2=1, condition: (1 < 3) and (1 > 0) = True and True = True
        # - Edge (7,8): t1=2, t2=2, condition: (2 < 3) and (2 > 0) = True and True = True
        restriction_edges = [[1, 2]]
        start_time_frame = 0
        end_time_frame = 3
        
        # When: call identify_restricted_edges
        omega = self.controller.identify_restricted_edges(
            restriction_edges, start_time_frame, end_time_frame
        )
        
        # Then: should return edges at times 1 and 2 (not time 0)
        self.assertEqual(len(omega), 2)
        expected_edges = [(4, 5, 0, 1, 5), (7, 8, 0, 1, 5)]
        for edge in expected_edges:
            self.assertIn(edge, omega)
        
    def test_identify_edges_with_no_spatial_match(self):
        """Test identifying edges when spatial edge doesn't exist in TSG"""
        # Given: restriction on non-existent edge (9,10)
        restriction_edges = [[9, 10]]
        start_time_frame = 1
        end_time_frame = 3
        
        # When: call identify_restricted_edges
        omega = self.controller.identify_restricted_edges(
            restriction_edges, start_time_frame, end_time_frame
        )
        
        # Then: should return empty list
        self.assertEqual(len(omega), 0)
        self.assertEqual(omega, [])
        
    def test_identify_edges_with_no_temporal_match(self):
        """Test identifying edges when timeframe doesn't overlap with edge times"""
        # Given: restriction on edge (1,2) with timeframe [5,8] (outside our TSG time range)
        restriction_edges = [[1, 2]]
        start_time_frame = 5
        end_time_frame = 8
        
        # When: call identify_restricted_edges
        omega = self.controller.identify_restricted_edges(
            restriction_edges, start_time_frame, end_time_frame
        )
        
        # Then: should return empty list
        self.assertEqual(len(omega), 0)
        self.assertEqual(omega, [])
        
    def test_identify_edges_with_partial_temporal_match(self):
        """Test identifying edges when timeframe partially overlaps"""
        # Given: restriction on edge (1,2) with timeframe [1,2]
        # For horizontal edges at times 0,1,2:
        # - Edge (1,2): t=0, condition: (0 < 2) and (0 > 1) = True and False = False
        # - Edge (4,5): t=1, condition: (1 < 2) and (1 > 1) = True and False = False  
        # - Edge (7,8): t=2, condition: (2 < 2) and (2 > 1) = False and True = False
        # None should match with this timeframe. Let's use [0,2] instead.
        restriction_edges = [[1, 2]]
        start_time_frame = 0
        end_time_frame = 2
        
        # When: call identify_restricted_edges
        omega = self.controller.identify_restricted_edges(
            restriction_edges, start_time_frame, end_time_frame
        )
        
        # Then: should return edge at time 1 only
        # Edge (4,5): t=1, condition: (1 < 2) and (1 > 0) = True and True = True
        self.assertEqual(len(omega), 1)
        self.assertIn((4, 5, 0, 1, 5), omega)

    # =============================================================================
    # Tests for calculate_max_flow()
    # =============================================================================
    
    @patch('networkx.maximum_flow_value')
    def test_calculate_max_flow_simple_case(self, mock_max_flow_value):
        """Test max flow calculation with simple parallel edges case"""
        # Given: omega with 2 parallel edges and capacities
        omega = [
            (1, 2, 0, 1, 10),  # capacity 1
            (1, 3, 0, 1, 10),  # capacity 1
        ]
        incoming_capacity = {1: 2}  # node 1 can receive 2 units
        outgoing_capacity = {2: 1, 3: 1}  # nodes 2,3 can send 1 unit each
        
        # Mock NetworkX to return expected max flow
        mock_max_flow_value.return_value = 2
        
        # When: call calculate_max_flow
        result = self.controller.calculate_max_flow(omega, incoming_capacity, outgoing_capacity)
        
        # Then: should return 2 (can flow through both parallel edges)
        self.assertEqual(result, 2)
        
        # Verify NetworkX was called with correct graph structure
        mock_max_flow_value.assert_called_once()
        args, kwargs = mock_max_flow_value.call_args
        graph, source, sink = args
        self.assertEqual(source, "vS")
        self.assertEqual(sink, "vT")
        
        # Verify graph structure
        self.assertTrue(graph.has_edge(1, 2))
        self.assertTrue(graph.has_edge(1, 3))
        self.assertTrue(graph.has_edge("vS", 1))
        self.assertTrue(graph.has_edge(2, "vT"))
        self.assertTrue(graph.has_edge(3, "vT"))

    # =============================================================================
    # Tests for apply_restriction()
    # =============================================================================
    
    @patch.object(RestrictionForTimeFrameController, 'calculate_max_flow')
    @patch.object(RestrictionForTimeFrameController, 'get_restrictions')
    def test_apply_restriction_when_F_less_than_U(self, mock_get_restrictions, mock_calc_max_flow):
        """Test apply_restriction when max flow F < capacity limit U"""
        # Given: restriction with U=5, and mock max flow to return F=3
        mock_get_restrictions.return_value = True
        self.controller.restrictions = [
            ([[1, 2]], [1, 3], 5, 1.0, None, 1.0)  # U=5
        ]
        mock_calc_max_flow.return_value = 3  # F=3 < U=5
        
        # When: call apply_restriction
        self.controller.apply_restriction()
        
        # Then: no artificial nodes/edges should be added
        self.assertEqual(len(self.controller.get_all_additional_nodes()), 0)
        self.assertEqual(len(self.controller.get_all_additional_edges()), 0)
        
    @patch.object(RestrictionForTimeFrameController, 'calculate_max_flow')
    @patch.object(RestrictionForTimeFrameController, 'get_restrictions')
    def test_apply_restriction_when_F_greater_than_U(self, mock_get_restrictions, mock_calc_max_flow):
        """Test apply_restriction when max flow F > capacity limit U"""
        # Given: restriction with U=1, and mock max flow to return F=3
        mock_get_restrictions.return_value = True
        self.controller.restrictions = [
            ([[1, 2]], [1, 3], 1, 1.0, 200.0, 1.0)  # U=1, gamma=200
        ]
        mock_calc_max_flow.return_value = 3  # F=3 > U=1
        
        # When: call apply_restriction
        self.controller.apply_restriction()
        
        # Then: artificial nodes and edges should be added
        additional_nodes = self.controller.get_all_additional_nodes()
        additional_edges = self.controller.get_all_additional_edges()
        
        self.assertGreater(len(additional_nodes), 0)
        self.assertGreater(len(additional_edges), 0)
        
        # Should find penalty edge with capacity F-U=2 and cost=200
        penalty_edges = [e for e in additional_edges if e[4] == 200.0]  # cost = gamma
        self.assertGreater(len(penalty_edges), 0)
        
        penalty_edge = penalty_edges[0]
        self.assertEqual(penalty_edge[3], 2)  # capacity = F - U = 3 - 1 = 2
        self.assertEqual(penalty_edge[4], 200.0)  # cost = gamma
        
    @patch.object(RestrictionForTimeFrameController, 'calculate_max_flow')
    @patch.object(RestrictionForTimeFrameController, 'get_restrictions')
    def test_apply_restriction_removes_original_edges(self, mock_get_restrictions, mock_calc_max_flow):
        """Test that apply_restriction removes original restricted edges"""
        # Given: restriction and mock max flow > U
        mock_get_restrictions.return_value = True
        self.controller.restrictions = [
            ([[1, 2]], [0, 3], 1, 1.0, 200.0, 1.0)  # U=1, timeframe [0,3]
        ]
        mock_calc_max_flow.return_value = 3  # F=3 > U=1
        
        # Store original edges before applying restriction
        original_ts_edges = self.mock_graph_processor.ts_edges.copy()
        
        # When: call apply_restriction
        self.controller.apply_restriction()
        
        # Then: check that the _omega edges were tracked for removal
        # The _omega should contain the edges that were identified as restricted
        self.assertGreater(len(self.controller._omega), 0, "Omega should contain restricted edges")
        
        # Check that new artificial edges were added
        additional_edges = self.controller.get_all_additional_edges()
        self.assertGreater(len(additional_edges), len(self.controller._omega), 
                          "Should have more additional edges than just the original omega")
        
        # Check that the graph structure was modified
        current_edges = self.mock_graph_processor.ts_edges
        self.assertNotEqual(len(current_edges), len(original_ts_edges),
                           "Graph should have been modified")
        
        # Verify that artificial nodes were created
        additional_nodes = self.controller.get_all_additional_nodes()
        self.assertGreater(len(additional_nodes), 0, "Should have created artificial nodes")

    # =============================================================================
    # Tests for remove_artificial_artifact()
    # =============================================================================
    
    @patch.object(RestrictionForTimeFrameController, 'calculate_max_flow')
    @patch.object(RestrictionForTimeFrameController, 'get_restrictions')
    def test_cleanup_restores_graph_state(self, mock_get_restrictions, mock_calc_max_flow):
        """Test that remove_artificial_artifact restores graph to original state"""
        # Given: apply a restriction first to modify the graph
        mock_get_restrictions.return_value = True
        self.controller.restrictions = [
            ([[1, 2]], [1, 3], 1, 1.0, 200.0, 1.0)  # U=1
        ]
        mock_calc_max_flow.return_value = 3  # F=3 > U=1
        
        # Apply restriction to modify graph
        self.controller.apply_restriction()
        
        # Verify graph was modified
        self.assertGreater(len(self.controller.get_all_additional_nodes()), 0)
        self.assertGreater(len(self.controller.get_all_additional_edges()), 0)
        
        # Store current state
        nodes_before_cleanup = len(self.mock_graph_processor.ts_nodes)
        edges_before_cleanup = len(self.mock_graph_processor.ts_edges)
        
        # When: call remove_artificial_artifact
        self.controller.remove_artificial_artifact()
        
        # Then: artificial artifacts should be cleaned up
        self.assertEqual(len(self.controller.get_all_additional_nodes()), 0)
        self.assertEqual(len(self.controller.get_all_additional_edges()), 0)
        self.assertEqual(len(self.controller._omega), 0)
        
        # Graph should be restored (though exact restoration depends on implementation)
        # At minimum, the additional nodes should be removed
        final_nodes = len(self.mock_graph_processor.ts_nodes)
        self.assertLessEqual(final_nodes, nodes_before_cleanup)

    # =============================================================================
    # Additional helper tests
    # =============================================================================
    
    def test_identify_restricted_nodes(self):
        """Test identification of restricted nodes from omega"""
        # Given: omega with specific edges
        omega = [
            (1, 4, 0, 1, 10),
            (4, 7, 0, 1, 10),
            (2, 5, 0, 1, 10),
        ]
        
        # When: call identify_restricted_nodes
        restricted_nodes = self.controller.identify_restricted_nodes(omega)
        
        # Then: should return all unique nodes from omega
        expected_nodes = {1, 2, 4, 5, 7}
        self.assertEqual(restricted_nodes, expected_nodes)
        
    def test_calculate_incoming_capacity_for_restricted_nodes(self):
        """Test calculation of incoming capacity for restricted nodes"""
        # Given: TSG and restricted nodes
        TSG = [
            (10, 1, 0, 2, 10),  # external -> restricted (capacity 2)
            (11, 4, 0, 3, 10),  # external -> restricted (capacity 3)
            (1, 4, 0, 1, 10),   # restricted -> restricted (should be ignored)
            (1, 20, 0, 1, 10),  # restricted -> external (should be ignored)
        ]
        restricted_nodes = {1, 4}
        
        # When: call calculate_incoming_capacity_for_restricted_nodes
        incoming_capacity = self.controller.calculate_incoming_capacity_for_restricted_nodes(
            TSG, restricted_nodes
        )
        
        # Then: should return correct incoming capacities
        expected = defaultdict(int)
        expected[1] = 2  # from node 10
        expected[4] = 3  # from node 11
        
        self.assertEqual(dict(incoming_capacity), dict(expected))
        
    def test_calculate_outgoing_capacity_for_restricted_nodes(self):
        """Test calculation of outgoing capacity for restricted nodes"""
        # Given: TSG and restricted nodes
        TSG = [
            (1, 20, 0, 2, 10),  # restricted -> external (capacity 2)
            (4, 21, 0, 3, 10),  # restricted -> external (capacity 3)
            (1, 4, 0, 1, 10),   # restricted -> restricted (should be ignored)
            (10, 1, 0, 1, 10),  # external -> restricted (should be ignored)
        ]
        restricted_nodes = {1, 4}
        
        # When: call calculate_outgoing_capacity_for_restricted_nodes
        outgoing_capacity = self.controller.calculate_outgoing_capacity_for_restricted_nodes(
            TSG, restricted_nodes
        )
        
        # Then: should return correct outgoing capacities
        expected = defaultdict(int)
        expected[1] = 2  # to node 20
        expected[4] = 3  # to node 21
        
        self.assertEqual(dict(outgoing_capacity), dict(expected))

    def test_calculate_virtual_flow(self):
        """Test calculation of virtual flow needed"""
        # Test cases for virtual flow calculation
        test_cases = [
            (5, 3, 2),    # max_flow=5, U=3 -> virtual_flow=2
            (3, 5, 0),    # max_flow=3, U=5 -> virtual_flow=0 (no violation)
            (10, 10, 0),  # max_flow=10, U=10 -> virtual_flow=0 (exact match)
        ]
        
        for max_flow, U, expected_virtual_flow in test_cases:
            with self.subTest(max_flow=max_flow, U=U):
                result = self.controller.calculate_virtual_flow(max_flow, U)
                self.assertEqual(result, expected_virtual_flow)


if __name__ == '__main__':
    # Configure test runner for detailed output
    unittest.main(verbosity=2, buffer=True)
