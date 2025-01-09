import numpy as np
import pandas as pd
import math

class PathGenerator:
    @staticmethod
    def generate_cube_path(size_mm, points_per_side, measurements_per_pos=1):
        """Generate a cubic measurement path"""
        half_length = size_mm / 2
        
        # Generate points
        xs = []
        ys = []
        zs = []
        for x in np.linspace(-half_length, half_length, points_per_side):
            for y in np.linspace(-half_length, half_length, points_per_side):
                for z in np.linspace(-half_length, half_length, points_per_side):
                    for _ in range(measurements_per_pos):
                        xs.append(x)
                        ys.append(y)
                        zs.append(z)

        # Create points DataFrame
        df = pd.DataFrame({"x": xs, "y": ys, "z": zs})
        
        # Add center points
        df_center = pd.DataFrame({
            "x": np.zeros(measurements_per_pos),
            "y": np.zeros(measurements_per_pos),
            "z": np.zeros(measurements_per_pos),
        })
        
        # Combine and calculate movements
        df_full = pd.concat([df_center, df, df_center])
        
        df_diff = pd.DataFrame({
            "dx": [0] + list(np.diff(df_full["x"])),
            "dy": [0] + list(np.diff(df_full["y"])),
            "dz": [0] + list(np.diff(df_full["z"])),
            "x": df_full["x"].values,
            "y": df_full["y"].values,
            "z": df_full["z"].values
        })
        
        # Add delays and indices
        df_diff["delay"] = 1
        df_diff.loc[(np.abs(df_diff["dx"]) > 10) |
                   (np.abs(df_diff["dy"]) > 10) |
                   (np.abs(df_diff["dz"]) > 10), "delay"] = 3
        df_diff.loc[(np.abs(df_diff["dx"]) == 0) &
                   (np.abs(df_diff["dy"]) == 0) &
                   (np.abs(df_diff["dz"]) == 0), "delay"] = 0
        df_diff["index"] = np.arange(len(df_diff))
        
        return df_diff

    @staticmethod
    def generate_sphere_path(radius, num_points_theta, num_points_phi, measurements_per_pos=1):
        """Generate a spherical measurement path"""
        # Generate spherical coordinates
        thetas = np.linspace(0, 360, num_points_theta + 1)[:-1]
        phis = np.linspace(0, 180, num_points_phi + 1)[:-1]
        
        xs = []
        ys = []
        zs = []
        for theta in thetas:
            for phi in phis:
                theta_rad = theta * math.pi/180
                phi_rad = phi * math.pi/180
                
                z = math.cos(phi_rad) * radius
                x = math.cos(theta_rad) * math.sin(phi_rad) * radius
                y = math.sin(theta_rad) * math.sin(phi_rad) * radius
                
                for _ in range(measurements_per_pos):
                    xs.append(x)
                    ys.append(y)
                    zs.append(z)
        
        # Create points DataFrame
        df = pd.DataFrame({"x": xs, "y": ys, "z": zs})
        
        # Add center points
        df_center = pd.DataFrame({
            "x": [0] * measurements_per_pos,
            "y": [0] * measurements_per_pos,
            "z": [0] * measurements_per_pos,
        })
        
        # Combine and calculate movements
        df_full = pd.concat([df_center, df, df_center])
        
        df_diff = pd.DataFrame({
            "dx": [0] + list(np.diff(df_full["x"])),
            "dy": [0] + list(np.diff(df_full["y"])),
            "dz": [0] + list(np.diff(df_full["z"])),
            "x": df_full["x"].values,
            "y": df_full["y"].values,
            "z": df_full["z"].values
        })
        
        # Add delays and indices
        df_diff["delay"] = 1
        df_diff.loc[(np.abs(df_diff["dx"]) > 10) |
                   (np.abs(df_diff["dy"]) > 10) |
                   (np.abs(df_diff["dz"]) > 10), "delay"] = 3
        df_diff.loc[(np.abs(df_diff["dx"]) == 0) &
                   (np.abs(df_diff["dy"]) == 0) &
                   (np.abs(df_diff["dz"]) == 0), "delay"] = 0
        df_diff["index"] = np.arange(len(df_diff))
        
        return df_diff

    @staticmethod
    def get_preview_points(df):
        """Convert path dataframe to points for visualization"""
        return np.array([df['x'].values, df['y'].values, df['z'].values]).T