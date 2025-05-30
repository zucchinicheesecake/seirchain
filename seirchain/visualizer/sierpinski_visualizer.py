import os
import time
import math # For math.log2 (though not strictly used in current iteration, good for fractal logic)

# Import config for visualizer settings
from seirchain.config import config as global_config

class SierpinskiVisualizer:
    def __init__(self, max_display_depth=5, char_filled='▓', char_empty=' ', char_mining='█', char_genesis='◊'):
        self.max_display_depth = max_display_depth # How many fractal levels to display
        self.char_filled = char_filled
        self.char_empty = char_empty
        self.char_mining = char_mining
        self.char_genesis = char_genesis
        self.animation_frame = 0 # Used for dynamic visual effects

    def _generate_sierpinski_grid_pattern(self, current_level):
        """
        Generates a 2D array representing a Sierpinski triangle pattern
        up to a specific fractal level. This array indicates where 'points'
        of the Sierpinski fractal exist (value 1) or not (value 0).
        """
        if current_level == 0:
            return [[1]] # Base case: a single point for the apex
        
        prev_grid = self._generate_sierpinski_grid_pattern(current_level - 1)
        prev_rows = len(prev_grid)
        prev_cols = len(prev_grid[0])
        
        # Calculate new grid dimensions based on the Sierpinski construction
        new_rows = prev_rows * 2
        new_cols = prev_cols * 2 + 1 

        new_grid = [[0 for _ in range(new_cols)] for _ in range(new_rows)]

        # Recursively place the three smaller Sierpinski triangles
        # Top triangle: Centered at the top half
        for r in range(prev_rows):
            for c in range(prev_cols):
                if prev_grid[r][c] == 1:
                    new_grid[r][c + prev_cols // 2 + (prev_cols % 2)] = 1 

        # Bottom-left triangle
        for r in range(prev_rows):
            for c in range(prev_cols):
                if prev_grid[r][c] == 1:
                    new_grid[r + prev_rows][c] = 1 
        
        # Bottom-right triangle
        for r in range(prev_rows):
            for c in range(prev_cols):
                if prev_grid[r][c] == 1:
                    new_grid[r + prev_rows][c + prev_cols + (prev_cols % 2)] = 1 

        return new_grid


    def render_frame(self, ledger_proxy, miner_stats_proxy):
        """
        Renders a single frame of the Sierpinski Triad Matrix ASCII visualization,
        incorporating live ledger and mining data.
        """
        # Get live data from shared proxy objects
        current_triads_dict = ledger_proxy.triads 
        current_max_ledger_depth = ledger_proxy.max_current_depth
        total_triads_count = ledger_proxy.get_total_triads()
        mining_stats = miner_stats_proxy.get_mining_stats()

        # Determine the effective fractal depth to display.
        # This grows with the ledger depth, up to a maximum defined in config.
        effective_display_depth = min(current_max_ledger_depth + 1, self.max_display_depth)
        
        # Generate the underlying Sierpinski pattern grid (where triads *can* be located)
        sierpinski_pattern_grid = self._generate_sierpinski_grid_pattern(effective_display_depth)
        
        grid_rows = len(sierpinski_pattern_grid)
        grid_cols = len(sierpinski_pattern_grid[0])
        
        # Initialize the display grid with empty characters
        display_grid = [[self.char_empty for _ in range(grid_cols)] for _ in range(grid_rows)]

        # Populate the display grid based on the Sierpinski pattern and ledger data
        # This is a simplified mapping. A more advanced visualizer would map specific triad hashes
        # to specific X,Y coordinates in the fractal.
        
        # Fill the base pattern with 'filled' characters where a theoretical triad exists
        for r in range(grid_rows):
            for c in range(grid_cols):
                if sierpinski_pattern_grid[r][c] == 1:
                    display_grid[r][c] = self.char_filled # Default to a generic 'filled' char

        # Apply specific characters based on actual triad states and animation
        # Genesis triad: Always at the apex
        if total_triads_count > 0: # Ensure genesis exists before trying to place
            display_grid[0][grid_cols // 2] = self.char_genesis 
            
        # Highlight recent mining activity or "mining" areas
        # This is a simple animation placeholder. You can make this much more sophisticated.
        if mining_stats.get("hashrate") != "0 H/s" and total_triads_count > 0:
            # Create a "mining wave" that moves down the triangle
            # This is a simple visual effect, not tied to specific triad hashes yet.
            
            # The 'wave' position changes with animation_frame, wraps around the displayable rows
            wave_row = self.animation_frame % grid_rows 
            
            # Highlight cells in the wave_row that are part of the Sierpinski pattern
            for c in range(grid_cols):
                if display_grid[wave_row][c] == self.char_filled:
                    display_grid[wave_row][c] = self.char_mining
                elif display_grid[wave_row][c] == self.char_genesis and wave_row != 0:
                    # Don't overwrite genesis character unless it's the genesis row
                    display_grid[wave_row][c] = self.char_mining 

        # Clear terminal for animation (cross-platform)
        os.system('cls' if os.name == 'nt' else 'clear')

        # Construct the final output string
        output_lines = []
        # Header
        output_lines.append("╔═══════════════════════════════════════════════╗")
        output_lines.append("║            SEIRCHAIN TRIAD MATRIX             ║")
        output_lines.append("╠═══════════════════════════════════════════════╣")

        # Sierpinski grid, centered in the output
        for row in display_grid:
            output_lines.append("".join(row).center(50)) # Adjust padding if needed for your terminal size

        # Footer with real-time stats
        output_lines.append("╠═══════════════════════════════════════════════╣")
        output_lines.append(f"║ Current Ledger Depth: {current_max_ledger_depth:<25}║")
        output_lines.append(f"║ Total Triads: {total_triads_count:<31}║")
        output_lines.append(f"║ Mining Hashrate: {mining_stats.get('hashrate', 'N/A'):<28}║")
        output_lines.append(f"║ Last Nonce: {mining_stats.get('last_nonce', 'N/A'):<31}║")
        output_lines.append(f"║ Mining Target: {mining_stats.get('mining_target', 'N/A')[:20]:<28}║")
        output_lines.append(f"║ Triads Mined (Session): {mining_stats.get('triads_mined_session', 0):<20}║")

        output_lines.append("╚═══════════════════════════════════════════════╝")

        print("\n".join(output_lines))


    def animate(self, ledger_proxy, miner_stats_proxy):
        """
        Main animation loop.
        ledger_proxy: A proxy object that reads live data from the shared ledger dict.
        miner_stats_proxy: A proxy object that reads live data from the shared miner stats dict.
        """
        self.running = True
        try:
            while self.running:
                self.render_frame(ledger_proxy, miner_stats_proxy)
                time.sleep(global_config.VISUALIZER_ANIMATION_INTERVAL) # Use config for interval
                self.animation_frame += 1

        except KeyboardInterrupt:
            self.running = False
            print("\nVisualizer stopped.")
        except Exception as e:
            print(f"\nAn error occurred in the visualizer: {e}")
            self.running = False

