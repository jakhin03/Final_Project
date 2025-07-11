from model.Node import Node

class ArtificialNode(Node):
    def __init__(self, id, label=None, temporary=False):
        super().__init__(id, label)
        self.temporary = temporary  # Indicates whether the node is temporary

    def __repr__(self):
        return f"ArtificialNode(id={self.id}, label='{self.label}', temporary={self.temporary})"
    
    def create_edge(self, node, M, d, e, debug=False):
        """Create edge from artificial node to any other node type."""
        if debug:
            import pdb
            pdb.set_trace()
        from controller.NodeGenerator import RestrictionNode
        from controller.NodeGenerator import TimeWindowNode
        from controller.EdgeGenerator import RestrictionEdge
        from controller.EdgeGenerator import TimeWindowEdge
        from model.Edge import ArtificialEdge
        
        if isinstance(node, int):
            import pdb
            pdb.set_trace()
        
        # For artificial nodes, we always create ArtificialEdge regardless of destination
        return ArtificialEdge(self, node, e[2], e[3], e[4])
    
from controller.EdgeGenerator import RestrictionEdge
import pdb

class RestrictionNode(Node):
    def __init__(self, ID, restrictions):
        super().__init__(ID)
        self.restrictions = restrictions  # Restrictions associated with the node
        
    def create_edge(self, node, M, d, e):
        #pdb.set_trace()
        # Always returns a RestrictionEdge regardless of other node types or conditions.
        return RestrictionEdge(self, node, e, "Restriction")

    def __repr__(self):
        return f"RestrictionNode(ID={self.id}, restrictions={self.restrictions})"

class TimeoutNode(Node):
    def __init__(self, id, label=None, temporary=False):
        super().__init__(id, label)
        self.temporary = temporary  # Indicates whether the node is temporary

    def __repr__(self):
        return f"TimeoutNode(id={self.id}, label='{self.label}', temporary={self.temporary})"

class TimeWindowNode(Node):
    def __init__(self, ID, time_window):
        super().__init__(ID)
        self.time_window = time_window  # Time window in which the node can be accessed
        self.earliness = float('-inf')
        self.tardiness = float('inf')

    def set_time_window(self, earliness, tardiness):
        self.earliness = earliness
        self.tardiness = tardiness
        
    def calculate(self, reaching_time):
        if reaching_time >= self.earliness and reaching_time <= self.tardiness:
            return 0
        if reaching_time < self.earliness:
            return (-1)*(self.earliness - reaching_time)
        #if reaching_time > self.tardiness:
        return (reaching_time - self.tardiness)
        
    def create_edge(self, node, M, d, e):
        # Does nothing and returns None, effectively preventing the creation of any edge.
        return None
    
    def getEventForReaching(self, event):
        from controller.EventGenerator import ReachingTargetEvent
        if self.id == event.agv.target_node.id:
            #pdb.set_trace()
            print(f"Target {event.agv.target_node.id}")
            return ReachingTargetEvent(
                event.end_time, event.end_time, event.agv, event.graph, self.id
            )
        return None
    
    def __repr__(self):
        return f"TimeWindowNode(ID={self.id}, time_window={self.time_window})"
