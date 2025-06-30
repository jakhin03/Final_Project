#!/usr/bin/env python3
"""
Practical Example: Using Gamma Evaluation Features

This script shows exactly how to activate and use the gamma evaluation
features built into RestrictionForTimeFrameController.
"""

import os
import sys

def show_activation_example():
    """Show how to properly activate gamma evaluation"""
    
    print("🚀 HOW TO ACTIVATE GAMMA EVALUATION")
    print("=" * 45)
    
    print("""
# Step 1: Create controller (this you probably already have)
from controller.RestrictionForTimeFrameController import RestrictionForTimeFrameController

controller = RestrictionForTimeFrameController(your_graph_processor)

# Step 2: IMPORTANT - Enable gamma control (this is what you're missing!)
controller.enable_gamma_control()
# ✅ This initializes the gamma_integrator

# Step 3: Set up restrictions (creates escape edges with gamma costs)
controller.get_restrictions()  # Interactive input
# OR
controller.set_restrictions(your_restrictions_data)  # Programmatic

# Step 4: Apply restrictions (this creates escape edges in the graph)
controller.apply_restriction()

# Step 5: Run your simulation (this generates TSG.txt with escape edges)
# ... your main simulation code ...

# Step 6: IMPORTANT - Analyze violations (this detects actual violations)
violations = controller.analyze_current_violations("TSG.txt")
# ✅ This is where you'll see the gamma effects

# Step 7: Get summary of results
summary = controller.get_violation_summary()
print(f"Found {summary['violations_count']} violations")
print(f"Total penalty cost: {summary['total_penalty_cost']}")
""")

def show_why_no_changes():
    """Explain why you might not see changes"""
    
    print("\n❓ WHY YOU DON'T SEE CHANGES")
    print("=" * 35)
    
    print("\n1. MOST LIKELY CAUSE: Methods Not Called")
    print("-" * 45)
    print("The gamma evaluation features are PASSIVE - they don't activate automatically.")
    print("You need to explicitly call:")
    print("  • controller.enable_gamma_control()")
    print("  • controller.analyze_current_violations()")
    print("  • controller.get_violation_summary()")
    
    print("\n2. ESCAPE EDGES CREATED BUT NOT ANALYZED")
    print("-" * 45)
    print("apply_restriction() creates escape edges, but you need to:")
    print("  • Run simulation to generate TSG file")
    print("  • Call analyze_current_violations() to detect flow through escape edges")
    
    print("\n3. NO VIOLATIONS OCCURRING")
    print("-" * 30)
    print("If gamma is very high (200+), violations become too expensive:")
    print("  • AGVs find alternative paths")
    print("  • No flow through escape edges")
    print("  • analyze_current_violations() returns empty list")
    
    print("\n4. LOOKING AT WRONG OUTPUT")
    print("-" * 30)
    print("Gamma effects are in violation analysis, not main simulation output:")
    print("  • Check: controller.last_violations")
    print("  • Check: controller.get_violation_summary()")
    print("  • Check: TSG file for high-cost escape edges")

def show_escape_edge_detection():
    """Explain how escape edges work"""
    
    print("\n🎯 HOW ESCAPE EDGES WORK")
    print("=" * 30)
    
    print("\n1. ESCAPE EDGE CREATION (in apply_restriction)")
    print("-" * 50)
    print("""
When you have a restriction with capacity U=2, but flow demand is 5:
• virtual_flow_needed = max(0, 5 - 2) = 3
• Creates escape edge: (artificial_source, artificial_sink, 0, 3, gamma)
• This allows 3 units of "violation flow" with penalty = 3 × gamma
""")
    
    print("\n2. ESCAPE EDGE USAGE (during simulation)")
    print("-" * 45)
    print("""
If gamma is LOW (e.g., 1):
• Penalty for using escape edge = 3 × 1 = 3
• If regular path costs more than 3, AGV uses escape edge
• Result: violation occurs, flow through escape edge > 0

If gamma is HIGH (e.g., 1000):
• Penalty for using escape edge = 3 × 1000 = 3000
• AGV will find alternative path instead
• Result: no violation, flow through escape edge = 0
""")
    
    print("\n3. VIOLATION DETECTION (in analyze_current_violations)")
    print("-" * 55)
    print("""
analyze_current_violations() looks at TSG file:
• Finds edges with very high costs (escape edges)
• Checks flow value through these edges
• If flow > 0: violation detected
• Calculates penalty = flow × gamma
""")

def show_debugging_checklist():
    """Provide debugging checklist"""
    
    print("\n🔧 DEBUGGING CHECKLIST")
    print("=" * 25)
    
    checklist = [
        ("gamma_integrator initialized?", "controller.gamma_integrator should not be None"),
        ("restrictions applied?", "controller._all_additional_edges should contain escape edges"),
        ("TSG file generated?", "TSG.txt should exist and contain high-cost edges"),
        ("violations analyzed?", "controller.last_violations should be populated"),
        ("escape edges detected?", "controller.last_escape_edges should be populated"),
        ("violation summary checked?", "controller.get_violation_summary() should show results")
    ]
    
    for i, (check, detail) in enumerate(checklist, 1):
        print(f"\n{i}. ✅ {check}")
        print(f"   → {detail}")

def show_practical_debugging():
    """Show practical debugging code"""
    
    print("\n🐛 PRACTICAL DEBUGGING CODE")
    print("=" * 32)
    
    print("""
# Debug code to add to your simulation:

# After creating controller
print(f"Gamma integrator: {controller.gamma_integrator}")

# After enabling gamma control
controller.enable_gamma_control()
print(f"Gamma integrator enabled: {controller.gamma_integrator is not None}")

# After applying restrictions
print(f"Additional edges created: {len(controller._all_additional_edges)}")
print(f"Escape edges in restrictions: {[e for e in controller._all_additional_edges if e[4] > 100]}")

# After running simulation
if os.path.exists("TSG.txt"):
    with open("TSG.txt", "r") as f:
        lines = f.readlines()
    high_cost_edges = [line for line in lines if line.startswith("a") and len(line.split()) > 5 and int(line.split()[5]) > 100]
    print(f"High-cost edges in TSG: {len(high_cost_edges)}")

# After analyzing violations
violations = controller.analyze_current_violations()
print(f"Violations detected: {len(violations)}")
print(f"Escape edges found: {len(controller.last_escape_edges)}")

# Get detailed summary
summary = controller.get_violation_summary()
for key, value in summary.items():
    print(f"{key}: {value}")
""")

def main():
    """Main demonstration"""
    show_activation_example()
    show_why_no_changes()
    show_escape_edge_detection()
    show_debugging_checklist()
    show_practical_debugging()
    
    print("\n" + "=" * 70)
    print("🎯 SUMMARY: The gamma evaluation is there, but needs explicit activation!")
    print("   Call: controller.enable_gamma_control()")
    print("   Call: controller.analyze_current_violations()")
    print("   Check: controller.get_violation_summary()")
    print("=" * 70)

if __name__ == "__main__":
    main()
