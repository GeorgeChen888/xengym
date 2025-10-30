#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Force Comparison Visualization Tool
Visualizes and compares force_xyz[2] (Z-force) between real and simulated data
for different objects and trajectories.
"""

import numpy as np
import pickle
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, RadioButtons
from typing import Dict, List, Tuple, Optional
import sys

try:
    from scipy.interpolate import UnivariateSpline
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("⚠️ scipy not available, polynomial fitting will be used instead")


class ForceDataVisualizer:
    def __init__(self, real_data_path: str, sim_data_path: str):
        """
        Initialize the force comparison visualizer
        
        Parameters:
        - real_data_path: Path to real_data.pkl
        - sim_data_path: Path to sim_data.pkl
        """
        self.real_data = self.load_data(real_data_path)
        self.sim_data = self.load_data(sim_data_path)
        
        # Get common objects and trajectories
        self.objects = sorted(list(set(self.real_data.keys()) & set(self.sim_data.keys())))
        
        if not self.objects:
            raise ValueError("No common objects found between real and sim data")
        
        self.current_object = self.objects[0]
        self.current_trajectory = None
        self.trajectories = {}
        
        # Build trajectory dictionary
        for obj in self.objects:
            real_trajs = set(self.real_data[obj].keys())
            sim_trajs = set(self.sim_data[obj].keys())
            common_trajs = sorted(list(real_trajs & sim_trajs))
            self.trajectories[obj] = common_trajs
        
        self.current_trajectory = self.trajectories[self.current_object][0] if self.trajectories[self.current_object] else None
        
        # Setup the plot
        self.setup_plot()
        
    def load_data(self, file_path: str) -> Dict:
        """Load pickle data file"""
        with open(file_path, 'rb') as f:
            return pickle.load(f)
    
    def extract_force_z(self, data: Dict, obj: str, traj: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract force_xyz[2] values and step numbers for a given object and trajectory
        
        Returns:
        - steps: array of step indices
        - forces: array of Z-force values
        """
        traj_data = data[obj][traj]
        steps = []
        forces = []
        
        for step_key in sorted(traj_data.keys()):
            step_data = traj_data[step_key]
            if 'force_xyz' in step_data:
                force_z = step_data['force_xyz'][2]
                # Extract step number from key like "step_000", "step_001", etc.
                step_num = int(step_key.split('_')[-1])
                steps.append(step_num)
                forces.append(float(force_z))
        
        return np.array(steps), np.array(forces)
    
    def fit_curve(self, x: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Fit a smooth curve through the data points
        
        Returns:
        - x_dense: dense x values for smooth plotting
        - y_fitted: fitted y values
        """
        if len(x) < 2:
            return x, y
        
        x_dense = np.linspace(x.min(), x.max(), 200)
        
        if SCIPY_AVAILABLE and len(x) >= 4:
            try:
                # Use spline fitting
                k = min(3, len(x) - 1)  # Spline degree
                s = len(x) * 0.1  # Smoothing factor
                spline = UnivariateSpline(x, y, k=k, s=s)
                y_fitted = spline(x_dense)
                return x_dense, y_fitted
            except:
                pass
        
        # Fallback to polynomial fitting
        try:
            degree = min(3, len(x) - 1)
            poly = np.polyfit(x, y, degree)
            y_fitted = np.polyval(poly, x_dense)
            return x_dense, y_fitted
        except:
            return x, y
    
    def setup_plot(self):
        """Setup the matplotlib figure and widgets"""
        self.fig = plt.figure(figsize=(14, 8))
        self.fig.canvas.manager.set_window_title('Force Z Comparison: Real vs Simulation')
        
        # Main plot area (larger, no bottom stats area)
        self.ax_main = plt.subplot2grid((3, 4), (0, 1), colspan=3, rowspan=3)
        
        # Object selection area (left column, top)
        self.ax_object = plt.subplot2grid((3, 4), (0, 0), rowspan=1)
        self.ax_object.set_title('Select Object', fontsize=10, fontweight='bold')
        
        # Trajectory selection area (left column, bottom)
        self.ax_trajectory = plt.subplot2grid((3, 4), (1, 0), rowspan=2)
        self.ax_trajectory.set_title('Select Trajectory', fontsize=10, fontweight='bold')
        
        # Create radio buttons for object selection
        self.radio_object = RadioButtons(self.ax_object, self.objects)
        self.radio_object.on_clicked(self.on_object_change)
        
        # Create radio buttons for trajectory selection
        self.update_trajectory_buttons()
        
        # Plot initial data
        self.update_plot()
        
        plt.tight_layout()
    
    def update_trajectory_buttons(self):
        """Update trajectory radio buttons based on current object"""
        self.ax_trajectory.clear()
        self.ax_trajectory.set_title('Select Trajectory', fontsize=10, fontweight='bold')
        
        trajs = self.trajectories[self.current_object]
        if trajs:
            self.radio_trajectory = RadioButtons(self.ax_trajectory, trajs)
            self.radio_trajectory.on_clicked(self.on_trajectory_change)
            if self.current_trajectory not in trajs:
                self.current_trajectory = trajs[0]
        else:
            self.ax_trajectory.text(0.5, 0.5, 'No trajectories', 
                                   ha='center', va='center', transform=self.ax_trajectory.transAxes)
            self.current_trajectory = None
    
    def on_object_change(self, label):
        """Callback when object selection changes"""
        self.current_object = label
        self.update_trajectory_buttons()
        self.update_plot()
        plt.draw()
    
    def on_trajectory_change(self, label):
        """Callback when trajectory selection changes"""
        self.current_trajectory = label
        self.update_plot()
        plt.draw()
    
    def update_plot(self):
        """Update the main plot with current selection"""
        self.ax_main.clear()
        
        if self.current_trajectory is None:
            self.ax_main.text(0.5, 0.5, 'No trajectory selected', 
                            ha='center', va='center', transform=self.ax_main.transAxes,
                            fontsize=14)
            return
        
        try:
            # Extract force data
            real_steps, real_forces = self.extract_force_z(
                self.real_data, self.current_object, self.current_trajectory
            )
            sim_steps, sim_forces = self.extract_force_z(
                self.sim_data, self.current_object, self.current_trajectory
            )
            
            if len(real_steps) == 0 and len(sim_steps) == 0:
                self.ax_main.text(0.5, 0.5, 'No force data available', 
                                ha='center', va='center', transform=self.ax_main.transAxes,
                                fontsize=14)
                return
            
            # Plot real data
            if len(real_steps) > 0:
                self.ax_main.scatter(real_steps, real_forces, 
                                   c='blue', s=80, alpha=0.6, 
                                   edgecolors='darkblue', linewidth=1.5,
                                   label='Real Data Points', zorder=3)
                
                # Fit and plot curve
                if len(real_steps) >= 2:
                    x_fit, y_fit = self.fit_curve(real_steps, real_forces)
                    self.ax_main.plot(x_fit, y_fit, 'b-', 
                                    linewidth=2.5, alpha=0.7,
                                    label='Real Fitted Curve')
            
            # Plot sim data
            if len(sim_steps) > 0:
                self.ax_main.scatter(sim_steps, sim_forces, 
                                   c='red', s=80, alpha=0.6, marker='s',
                                   edgecolors='darkred', linewidth=1.5,
                                   label='Sim Data Points', zorder=3)
                
                # Fit and plot curve
                if len(sim_steps) >= 2:
                    x_fit, y_fit = self.fit_curve(sim_steps, sim_forces)
                    self.ax_main.plot(x_fit, y_fit, 'r--', 
                                    linewidth=2.5, alpha=0.7,
                                    label='Sim Fitted Curve')
            
            # Formatting
            self.ax_main.set_xlabel('Step Number', fontsize=12, fontweight='bold')
            self.ax_main.set_ylabel('Z-Force (N)', fontsize=12, fontweight='bold')
            self.ax_main.set_title(
                f'Force Comparison: {self.current_object} - {self.current_trajectory}',
                fontsize=14, fontweight='bold', pad=15
            )
            self.ax_main.legend(loc='best', fontsize=10, framealpha=0.9)
            self.ax_main.grid(True, alpha=0.3, linestyle='--')
        
        except Exception as e:
            self.ax_main.text(0.5, 0.5, f'Error loading data:\n{str(e)}', 
                            ha='center', va='center', transform=self.ax_main.transAxes,
                            fontsize=12, color='red')
    
    def show(self):
        """Display the interactive plot"""
        plt.show()


def main():
    """Main function"""
    print("🎯 Force Comparison Visualization Tool")
    print("=" * 60)
    
    # Get script directory
    script_dir = Path(__file__).parent
    
    # Default paths
    real_data_path = script_dir / "real_data.pkl"
    sim_data_path = script_dir / "sim_data.pkl"
    
    # Check if files exist
    if not real_data_path.exists():
        print(f"❌ Error: real_data.pkl not found at {real_data_path}")
        print(f"   Please ensure the file exists in: {script_dir}")
        sys.exit(1)
    
    if not sim_data_path.exists():
        print(f"❌ Error: sim_data.pkl not found at {sim_data_path}")
        print(f"   Please ensure the file exists in: {script_dir}")
        sys.exit(1)
    
    print(f"✓ Loading real data from: {real_data_path}")
    print(f"✓ Loading sim data from: {sim_data_path}")
    
    try:
        visualizer = ForceDataVisualizer(str(real_data_path), str(sim_data_path))
        
        print(f"\n📊 Visualization ready!")
        print(f"   Objects available: {', '.join(visualizer.objects)}")
        print(f"   Total trajectories: {sum(len(v) for v in visualizer.trajectories.values())}")
        print(f"\n💡 Instructions:")
        print(f"   - Use left panel radio buttons to switch between objects")
        print(f"   - Use left bottom panel to select trajectories")
        print(f"   - Blue: Real data | Red: Simulation data")
        print(f"\n🖥️  Opening visualization window...")
        
        visualizer.show()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()