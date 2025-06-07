#!/usr/bin/env python3
import pygame
import sys
import random
import os
import math
import time
from enum import Enum

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Get screen info for fullscreen
screen_info = pygame.display.Info()
SCREEN_WIDTH = screen_info.current_w
SCREEN_HEIGHT = screen_info.current_h

# Constants
GRID_SIZE = 4

# Calculate proper dimensions based on screen size
TITLE_HEIGHT = int(SCREEN_HEIGHT * 0.1)  # 10% of screen height for title
STATUS_HEIGHT = int(SCREEN_HEIGHT * 0.2)  # 20% of screen height for status/controls

# Calculate side panel widths (20% of screen width each)
SIDE_PANEL_WIDTH = int(SCREEN_WIDTH * 0.2)

# Calculate grid size to fit in remaining space
AVAILABLE_WIDTH = SCREEN_WIDTH - (2 * SIDE_PANEL_WIDTH)
AVAILABLE_HEIGHT = SCREEN_HEIGHT - TITLE_HEIGHT - STATUS_HEIGHT
CELL_SIZE = min(AVAILABLE_WIDTH // GRID_SIZE, AVAILABLE_HEIGHT // GRID_SIZE)

# Center the grid horizontally and vertically in the available space
GRID_WIDTH = CELL_SIZE * GRID_SIZE
GRID_HEIGHT = CELL_SIZE * GRID_SIZE
GRID_OFFSET_X = SIDE_PANEL_WIDTH + (AVAILABLE_WIDTH - GRID_WIDTH) // 2
GRID_OFFSET_Y = TITLE_HEIGHT + (AVAILABLE_HEIGHT - GRID_HEIGHT) // 2

# Colors
BG_COLOR = (20, 20, 30)
GRID_COLOR = (80, 80, 100)
TEXT_COLOR = (255, 255, 255)
GOLD_COLOR = (255, 215, 0)
WUMPUS_COLOR = (255, 50, 50)
PIT_COLOR = (100, 100, 100)
PLAYER_COLOR = (50, 255, 100)
BREEZE_COLOR = (100, 200, 255)
STENCH_COLOR = (180, 50, 180)
START_COLOR = (50, 150, 50)

# Game elements
class Element(Enum):
    EMPTY = 0
    PLAYER = 1
    WUMPUS = 2
    PIT = 3
    GOLD = 4
    BREEZE = 5
    STENCH = 6

class WumpusWorld:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.RESIZABLE)
        pygame.display.set_caption("Wumpus World")
        
        # Adjust font size based on screen dimensions
        title_font_size = max(36, min(72, int(SCREEN_HEIGHT * 0.05)))
        ui_font_size = max(18, min(36, int(SCREEN_HEIGHT * 0.025)))
        
        self.title_font = pygame.font.SysFont(None, title_font_size)
        self.font = pygame.font.SysFont(None, ui_font_size)
        
        # Environmental animation variables
        self.env_time = 0
        self.last_time = time.time()
        self.dust_particles = []
        self.light_flickers = []
        self.water_drops = []
        self.bat_positions = []
        
        # Initialize environmental elements
        self.initialize_environment()
        
        # Load images
        self.load_images()
        
        # Create sounds directory if it doesn't exist
        os.makedirs('sounds', exist_ok=True)
        
        # Create placeholder sound files if they don't exist
        self.create_placeholder_sounds()
        
        # Load sound effects
        self.sounds = {
            'move': pygame.mixer.Sound('sounds/move.wav'),
            'gold': pygame.mixer.Sound('sounds/gold.wav'),
            'pit': pygame.mixer.Sound('sounds/pit.wav'),
            'wumpus': pygame.mixer.Sound('sounds/wumpus.wav'),
            'win': pygame.mixer.Sound('sounds/win.wav'),
            'breeze': pygame.mixer.Sound('sounds/breeze.wav'),
            'stench': pygame.mixer.Sound('sounds/stench.wav')
        }
        
        # Set volume
        for sound in self.sounds.values():
            sound.set_volume(0.7)
            
        # Game statistics
        self.stats = {
            'moves': 0,
            'pits_nearby': 0,
            'wumpus_nearby': 0,
            'cells_visited': 0
        }
        
        # Game hints
        self.hints = [
            "Breezes indicate nearby pits",
            "Stenches indicate the Wumpus",
            "Avoid the Wumpus and pits",
            "Find the gold and return home",
            "Use arrow keys to move"
        ]
        
        self.reset_game()
    
    def load_images(self):
        """Load game images or use placeholders"""
        self.images = {}
        
        # Create images directory if it doesn't exist
        os.makedirs('images', exist_ok=True)
        
        # Check if images exist, if not create custom backgrounds
        image_files = {
            'background': 'images/background.png',
            'left_panel': 'images/left_panel.png',
            'right_panel': 'images/right_panel.png',
            'player': 'images/player.png',
            'wumpus': 'images/wumpus.png',
            'gold': 'images/gold.png',
            'pit': 'images/pit.png'
        }
        
        # Load or create placeholder images
        for name, path in image_files.items():
            if os.path.exists(path):
                self.images[name] = pygame.image.load(path)
            else:
                # Create placeholder colored surface
                if name == 'background':
                    self.images[name] = self.create_background_image()
                elif name == 'left_panel':
                    self.images[name] = self.create_left_panel_image()
                elif name == 'right_panel':
                    self.images[name] = self.create_right_panel_image()
                elif name == 'player':
                    self.images[name] = self.create_player_image()
                elif name == 'wumpus':
                    self.images[name] = self.create_wumpus_image()
                elif name == 'gold':
                    self.images[name] = self.create_gold_image()
                elif name == 'pit':
                    self.images[name] = self.create_pit_image()
                else:
                    self.images[name] = pygame.Surface((CELL_SIZE, CELL_SIZE))
                    self.images[name].fill((100, 100, 100))
        
        # Scale images to fit the screen
        self.images['background'] = pygame.transform.scale(self.images['background'], (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.images['left_panel'] = pygame.transform.scale(self.images['left_panel'], (SIDE_PANEL_WIDTH, SCREEN_HEIGHT))
        self.images['right_panel'] = pygame.transform.scale(self.images['right_panel'], (SIDE_PANEL_WIDTH, SCREEN_HEIGHT))
        
        # Scale game element images to fit cells
        for name in ['player', 'wumpus', 'gold', 'pit']:
            if name in self.images:
                self.images[name] = pygame.transform.scale(self.images[name], (CELL_SIZE - 20, CELL_SIZE - 20))
    
    def create_placeholder_sounds(self):
        """Create placeholder sound files if they don't exist"""
        sound_files = {
            'sounds/move.wav': [440, 0.1],    # A4, short
            'sounds/gold.wav': [880, 0.5],    # A5, medium
            'sounds/pit.wav': [220, 0.5],     # A3, medium
            'sounds/wumpus.wav': [110, 0.7],  # A2, long
            'sounds/win.wav': [660, 1.0],     # E5, long
            'sounds/breeze.wav': [587, 0.3],  # D5, short
            'sounds/stench.wav': [330, 0.3]   # E4, short
        }
        
        for filename, (freq, duration) in sound_files.items():
            if not os.path.exists(filename):
                self.generate_tone(filename, freq, duration)
    
    def generate_tone(self, filename, frequency, duration):
        """Generate a simple tone and save it as a WAV file"""
        import math
        sample_rate = 44100
        amplitude = 4096
        num_samples = int(duration * sample_rate)
        
        # Generate a simple sine wave
        buf = bytearray()
        for i in range(num_samples):
            sample = int(amplitude * math.sin(2 * 3.14159 * frequency * i / sample_rate))
            # Simple fade in/out to avoid clicks
            if i < sample_rate * 0.1:
                sample = int(sample * i / (sample_rate * 0.1))
            elif i > num_samples - sample_rate * 0.1:
                sample = int(sample * (num_samples - i) / (sample_rate * 0.1))
            
            # Convert to 16-bit signed PCM
            buf.extend([(sample >> 8) & 0xFF, sample & 0xFF])
        
        # Create a simple WAV file
        with open(filename, 'wb') as f:
            # Write WAV header
            f.write(b'RIFF')
            f.write((36 + len(buf)).to_bytes(4, 'little'))
            f.write(b'WAVE')
            f.write(b'fmt ')
            f.write((16).to_bytes(4, 'little'))
            f.write((1).to_bytes(2, 'little'))  # PCM format
            f.write((1).to_bytes(2, 'little'))  # Mono
            f.write((sample_rate).to_bytes(4, 'little'))
            f.write((sample_rate * 2).to_bytes(4, 'little'))
            f.write((2).to_bytes(2, 'little'))
            f.write((16).to_bytes(2, 'little'))
            f.write(b'data')
            f.write((len(buf)).to_bytes(4, 'little'))
            f.write(buf)
    
    def reset_game(self):
        # Initialize grid with empty cells
        self.grid = [[[] for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.player_pos = [GRID_SIZE-1, 0]  # Bottom-left corner
        self.has_gold = False
        self.game_over = False
        self.win = False
        self.message = "Find the gold and return to start!"
        self.visited = [[False for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.visited[self.player_pos[0]][self.player_pos[1]] = True
        
        # Reset statistics
        self.stats = {
            'moves': 0,
            'pits_nearby': 0,
            'wumpus_nearby': 0,
            'cells_visited': 1  # Starting cell
        }
        
        # Place player
        self.grid[self.player_pos[0]][self.player_pos[1]].append(Element.PLAYER)
        
        # Place Wumpus (not in player's position)
        while True:
            wx, wy = random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)
            if not (wx == self.player_pos[0] and wy == self.player_pos[1]):
                self.grid[wx][wy].append(Element.WUMPUS)
                # Add stench in adjacent cells
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    nx, ny = wx + dx, wy + dy
                    if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                        self.grid[nx][ny].append(Element.STENCH)
                break
        
        # Place pits (not in player's position or Wumpus position)
        pit_count = random.randint(1, 3)
        for _ in range(pit_count):
            while True:
                px, py = random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)
                if not (px == self.player_pos[0] and py == self.player_pos[1]) and Element.WUMPUS not in self.grid[px][py]:
                    self.grid[px][py].append(Element.PIT)
                    # Add breeze in adjacent cells
                    for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                        nx, ny = px + dx, py + dy
                        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                            self.grid[nx][ny].append(Element.BREEZE)
                    break
        
        # Place gold (not in player's position, Wumpus position, or pit)
        # Always place gold in a specific cell (top-right corner) if it's safe
        gx, gy = 0, GRID_SIZE-1  # Top-right corner
        
        # If the preferred position isn't safe, find another position
        if (gx == self.player_pos[0] and gy == self.player_pos[1]) or \
           Element.WUMPUS in self.grid[gx][gy] or \
           Element.PIT in self.grid[gx][gy]:
            while True:
                gx, gy = random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)
                if not (gx == self.player_pos[0] and gy == self.player_pos[1]) and \
                   Element.WUMPUS not in self.grid[gx][gy] and \
                   Element.PIT not in self.grid[gx][gy]:
                    break
        
        self.grid[gx][gy].append(Element.GOLD)
    
    def move_player(self, dx, dy):
        if self.game_over:
            return
        
        # Calculate new position
        new_x = self.player_pos[0] + dx
        new_y = self.player_pos[1] + dy
        
        # Check if the move is valid
        if 0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE:
            # Play move sound
            self.sounds['move'].play()
            
            # Update statistics
            self.stats['moves'] += 1
            
            # Remove player from current position
            self.grid[self.player_pos[0]][self.player_pos[1]].remove(Element.PLAYER)
            
            # Update player position
            self.player_pos = [new_x, new_y]
            
            # Mark as visited if not already
            if not self.visited[new_x][new_y]:
                self.visited[new_x][new_y] = True
                self.stats['cells_visited'] += 1
            
            # Add player to new position
            self.grid[self.player_pos[0]][self.player_pos[1]].append(Element.PLAYER)
            
            # Check for game events
            self.check_events()
    
    def check_events(self):
        current_cell = self.grid[self.player_pos[0]][self.player_pos[1]]
        
        # Check if player found gold
        if Element.GOLD in current_cell:
            current_cell.remove(Element.GOLD)
            self.has_gold = True
            self.message = "You found the gold! Return to start."
            self.sounds['gold'].play()
        
        # Check if player fell into a pit
        if Element.PIT in current_cell:
            self.game_over = True
            self.message = "You fell into a pit! Game Over."
            self.sounds['pit'].play()
        
        # Check if player encountered the Wumpus
        if Element.WUMPUS in current_cell:
            self.game_over = True
            self.message = "The Wumpus got you! Game Over."
            self.sounds['wumpus'].play()
        
        # Check if player returned to start with gold
        if self.has_gold and self.player_pos == [GRID_SIZE-1, 0]:
            self.game_over = True
            self.win = True
            self.message = "You won! You got the gold and returned safely."
            self.sounds['win'].play()
        
        # Update status messages based on percepts
        if not self.game_over:
            percepts = []
            
            # Reset percept counters
            self.stats['pits_nearby'] = 0
            self.stats['wumpus_nearby'] = 0
            
            if Element.BREEZE in current_cell:
                percepts.append("You feel a breeze")
                self.sounds['breeze'].play()
                self.stats['pits_nearby'] += 1
            
            if Element.STENCH in current_cell:
                percepts.append("You smell a stench")
                self.sounds['stench'].play()
                self.stats['wumpus_nearby'] += 1
            
            if percepts:
                self.message = " & ".join(percepts)
            elif not self.has_gold:
                self.message = "Find the gold!"
            else:
                self.message = "Return to start with the gold!"
    
    def handle_resize(self, new_width, new_height):
        global SCREEN_WIDTH, SCREEN_HEIGHT, TITLE_HEIGHT, STATUS_HEIGHT
        global SIDE_PANEL_WIDTH, AVAILABLE_WIDTH, AVAILABLE_HEIGHT
        global CELL_SIZE, GRID_WIDTH, GRID_HEIGHT
        global GRID_OFFSET_X, GRID_OFFSET_Y
        
        # Update dimensions
        SCREEN_WIDTH = new_width
        SCREEN_HEIGHT = new_height
        
        # Recalculate layout
        TITLE_HEIGHT = int(SCREEN_HEIGHT * 0.1)
        STATUS_HEIGHT = int(SCREEN_HEIGHT * 0.2)
        SIDE_PANEL_WIDTH = int(SCREEN_WIDTH * 0.2)
        
        AVAILABLE_WIDTH = SCREEN_WIDTH - (2 * SIDE_PANEL_WIDTH)
        AVAILABLE_HEIGHT = SCREEN_HEIGHT - TITLE_HEIGHT - STATUS_HEIGHT
        CELL_SIZE = min(AVAILABLE_WIDTH // GRID_SIZE, AVAILABLE_HEIGHT // GRID_SIZE)
        
        GRID_WIDTH = CELL_SIZE * GRID_SIZE
        GRID_HEIGHT = CELL_SIZE * GRID_SIZE
        GRID_OFFSET_X = SIDE_PANEL_WIDTH + (AVAILABLE_WIDTH - GRID_WIDTH) // 2
        GRID_OFFSET_Y = TITLE_HEIGHT + (AVAILABLE_HEIGHT - GRID_HEIGHT) // 2
        
        # Update font sizes
        title_font_size = max(36, min(72, int(SCREEN_HEIGHT * 0.05)))
        ui_font_size = max(18, min(36, int(SCREEN_HEIGHT * 0.025)))
        self.title_font = pygame.font.SysFont(None, title_font_size)
        self.font = pygame.font.SysFont(None, ui_font_size)
        
        # Reload and rescale images
        self.load_images()
    
    def draw_title_area(self):
        # Draw title background with border
        title_bg_rect = pygame.Rect(0, 0, SCREEN_WIDTH, TITLE_HEIGHT)
        pygame.draw.rect(self.screen, (30, 30, 45), title_bg_rect)
        pygame.draw.line(self.screen, GRID_COLOR, (0, TITLE_HEIGHT), (SCREEN_WIDTH, TITLE_HEIGHT), 3)
        
        # Draw title text
        title = self.title_font.render("WUMPUS WORLD", True, TEXT_COLOR)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 
                                TITLE_HEIGHT // 2 - title.get_height() // 2))
    
    def draw_status_area(self):
        # Draw status bar background with border
        status_rect = pygame.Rect(0, SCREEN_HEIGHT - STATUS_HEIGHT, SCREEN_WIDTH, STATUS_HEIGHT)
        pygame.draw.rect(self.screen, (30, 30, 45), status_rect)
        pygame.draw.line(self.screen, GRID_COLOR, (0, SCREEN_HEIGHT - STATUS_HEIGHT), 
                        (SCREEN_WIDTH, SCREEN_HEIGHT - STATUS_HEIGHT), 3)
        
        # Game status message (centered at top of status area)
        status_text = self.font.render(self.message, True, TEXT_COLOR)
        self.screen.blit(status_text, (SCREEN_WIDTH // 2 - status_text.get_width() // 2, 
                                      SCREEN_HEIGHT - STATUS_HEIGHT + STATUS_HEIGHT // 4 - status_text.get_height() // 2))
        
        # Controls (centered at bottom of status area)
        controls = [
            "UP: Move Up",
            "DOWN: Move Down",
            "LEFT: Move Left",
            "RIGHT: Move Right",
            "R: Restart",
            "ESC: Quit"
        ]
        
        # Calculate if we should use horizontal or vertical layout based on screen width
        horizontal_width = sum(self.font.size(c)[0] for c in controls) + 20 * (len(controls) - 1)
        
        if horizontal_width < SCREEN_WIDTH * 0.9:
            # Horizontal layout
            control_text = " | ".join(controls)
            text_surface = self.font.render(control_text, True, TEXT_COLOR)
            self.screen.blit(text_surface, (SCREEN_WIDTH // 2 - text_surface.get_width() // 2,
                                          SCREEN_HEIGHT - STATUS_HEIGHT // 3 - text_surface.get_height() // 2))
        else:
            # Vertical layout - split into two rows
            row1 = " | ".join(controls[:3])
            row2 = " | ".join(controls[3:])
            
            text1 = self.font.render(row1, True, TEXT_COLOR)
            text2 = self.font.render(row2, True, TEXT_COLOR)
            
            # Position the two rows
            y_offset = STATUS_HEIGHT // 2
            self.screen.blit(text1, (SCREEN_WIDTH // 2 - text1.get_width() // 2,
                                   SCREEN_HEIGHT - STATUS_HEIGHT + y_offset - text1.get_height()))
            self.screen.blit(text2, (SCREEN_WIDTH // 2 - text2.get_width() // 2,
                                   SCREEN_HEIGHT - STATUS_HEIGHT + y_offset + 5))
    
    def draw_left_panel(self):
        # Draw left panel background
        self.screen.blit(self.images['left_panel'], (0, 0))
        
        # Draw panel title with background
        title_bg = pygame.Rect(0, TITLE_HEIGHT - 10, SIDE_PANEL_WIDTH, 50)
        pygame.draw.rect(self.screen, (50, 40, 70), title_bg)
        pygame.draw.rect(self.screen, (100, 80, 140), title_bg, 2)
        
        panel_title = self.font.render("HINTS", True, (220, 220, 255))
        self.screen.blit(panel_title, (SIDE_PANEL_WIDTH // 2 - panel_title.get_width() // 2, TITLE_HEIGHT + 10))
        
        # Draw hints with improved formatting
        hint_y_start = TITLE_HEIGHT + 70
        hint_spacing = 60
        
        for i, hint in enumerate(self.hints):
            # Draw hint background
            hint_bg = pygame.Rect(10, hint_y_start + i * hint_spacing - 5, SIDE_PANEL_WIDTH - 20, 50)
            pygame.draw.rect(self.screen, (40, 30, 60), hint_bg)
            pygame.draw.rect(self.screen, (80, 60, 120), hint_bg, 2)
            
            # Draw hint number
            number_text = self.font.render(f"{i+1}.", True, (180, 180, 220))
            self.screen.blit(number_text, (20, hint_y_start + i * hint_spacing))
            
            # Draw hint text with word wrapping
            words = hint.split()
            line = ""
            y_offset = 0
            x_offset = 45  # Indent after the number
            
            for word in words:
                test_line = line + word + " "
                test_width = self.font.size(test_line)[0]
                
                if test_width < SIDE_PANEL_WIDTH - 60:
                    line = test_line
                else:
                    hint_text = self.font.render(line, True, TEXT_COLOR)
                    self.screen.blit(hint_text, (20 + x_offset, hint_y_start + i * hint_spacing + y_offset))
                    line = word + " "
                    y_offset += 25
                    x_offset = 0  # No indent for wrapped lines
            
            # Draw the last line
            if line:
                hint_text = self.font.render(line, True, TEXT_COLOR)
                self.screen.blit(hint_text, (20 + x_offset, hint_y_start + i * hint_spacing + y_offset))
    
    def draw_right_panel(self):
        # Draw right panel background
        self.screen.blit(self.images['right_panel'], (SCREEN_WIDTH - SIDE_PANEL_WIDTH, 0))
        
        # Draw panel title with background
        title_bg = pygame.Rect(SCREEN_WIDTH - SIDE_PANEL_WIDTH, TITLE_HEIGHT - 10, SIDE_PANEL_WIDTH, 50)
        pygame.draw.rect(self.screen, (50, 40, 70), title_bg)
        pygame.draw.rect(self.screen, (100, 80, 140), title_bg, 2)
        
        panel_title = self.font.render("STATS", True, (220, 220, 255))
        self.screen.blit(panel_title, (SCREEN_WIDTH - SIDE_PANEL_WIDTH // 2 - panel_title.get_width() // 2, TITLE_HEIGHT + 10))
        
        # Draw statistics with improved formatting
        stats_to_display = [
            ("Moves", f"{self.stats['moves']}"),
            ("Cells Visited", f"{self.stats['cells_visited']}/{GRID_SIZE*GRID_SIZE}"),
            ("Pits Nearby", f"{self.stats['pits_nearby']}"),
            ("Wumpus Nearby", f"{self.stats['wumpus_nearby']}"),
            ("Gold Found", "Yes" if self.has_gold else "No")
        ]
        
        stat_y_start = TITLE_HEIGHT + 70
        stat_spacing = 60
        
        for i, (label, value) in enumerate(stats_to_display):
            # Draw stat background
            stat_bg = pygame.Rect(SCREEN_WIDTH - SIDE_PANEL_WIDTH + 10, stat_y_start + i * stat_spacing - 5, 
                                SIDE_PANEL_WIDTH - 20, 50)
            pygame.draw.rect(self.screen, (40, 30, 60), stat_bg)
            pygame.draw.rect(self.screen, (80, 60, 120), stat_bg, 2)
            
            # Draw label
            label_text = self.font.render(label + ":", True, (180, 180, 220))
            self.screen.blit(label_text, (SCREEN_WIDTH - SIDE_PANEL_WIDTH + 20, stat_y_start + i * stat_spacing))
            
            # Draw value with appropriate color based on content
            value_color = TEXT_COLOR
            if label == "Pits Nearby" and int(value) > 0:
                value_color = (100, 200, 255)  # Blue for breeze/pits
            elif label == "Wumpus Nearby" and int(value) > 0:
                value_color = (255, 100, 255)  # Purple for stench/wumpus
            elif label == "Gold Found" and value == "Yes":
                value_color = (255, 215, 0)    # Gold color
                
            value_text = self.font.render(value, True, value_color)
            value_x = SCREEN_WIDTH - SIDE_PANEL_WIDTH + SIDE_PANEL_WIDTH - 20 - value_text.get_width()
            self.screen.blit(value_text, (value_x, stat_y_start + i * stat_spacing))
            
            # Add visual indicators for certain stats
            if label == "Pits Nearby" and int(value) > 0:
                pygame.draw.circle(self.screen, (100, 200, 255), 
                                (SCREEN_WIDTH - SIDE_PANEL_WIDTH + 30, stat_y_start + i * stat_spacing + 30), 10)
            elif label == "Wumpus Nearby" and int(value) > 0:
                pygame.draw.circle(self.screen, (255, 100, 255), 
                                (SCREEN_WIDTH - SIDE_PANEL_WIDTH + 30, stat_y_start + i * stat_spacing + 30), 10)
        # This section is no longer needed as we're using the new format above
        # for i, stat in enumerate(stats_to_display):
        #     stat_text = self.font.render(stat, True, TEXT_COLOR)
        #     y_pos = TITLE_HEIGHT + 50 + i * 40
        #     self.screen.blit(stat_text, (SCREEN_WIDTH - SIDE_PANEL_WIDTH + 10, y_pos))
    
    def draw_grid(self):
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                # Calculate screen position
                screen_x = GRID_OFFSET_X + y * CELL_SIZE
                screen_y = GRID_OFFSET_Y + x * CELL_SIZE
                
                # Draw cell background
                cell_rect = pygame.Rect(screen_x, screen_y, CELL_SIZE, CELL_SIZE)
                
                # Highlight starting position
                if x == GRID_SIZE-1 and y == 0:
                    pygame.draw.rect(self.screen, START_COLOR, cell_rect, 0)
                
                # Draw cell border
                pygame.draw.rect(self.screen, GRID_COLOR, cell_rect, 3)
                
                # Only draw contents of visited cells
                if x < len(self.visited) and y < len(self.visited[0]) and self.visited[x][y]:
                    # Draw cell contents
                    cell_contents = self.grid[x][y]
                    
                    # Draw percepts (breeze, stench)
                    if Element.BREEZE in cell_contents:
                        # Enhanced breeze visualization
                        breeze_color = BREEZE_COLOR
                        for i in range(3):
                            offset = 5 * math.sin(pygame.time.get_ticks() * 0.003 + i * 2)
                            radius = CELL_SIZE // 15 + offset
                            pygame.draw.circle(self.screen, breeze_color, 
                                             (screen_x + 20, screen_y + 20), radius, 2)
                    
                    if Element.STENCH in cell_contents:
                        # Enhanced stench visualization with custom icon
                        stench_color = STENCH_COLOR
                        # Draw wavy lines to represent smell
                        for i in range(3):
                            start_x = screen_x + 20
                            start_y = screen_y + 50
                            points = []
                            for j in range(5):
                                x_offset = j * 5
                                y_offset = math.sin(pygame.time.get_ticks() * 0.005 + i + j) * 3
                                points.append((start_x + x_offset, start_y + y_offset + i * 5))
                            
                            if len(points) > 1:
                                pygame.draw.lines(self.screen, stench_color, False, points, 2)
                    
                    # Draw main elements using images when available
                    if Element.WUMPUS in cell_contents:
                        # Create a subtle pulsing effect for the Wumpus
                        pulse = math.sin(pygame.time.get_ticks() * 0.004) * 0.1 + 1.0
                        
                        # Calculate the pulsing size
                        wumpus_img = self.images['wumpus']
                        orig_size = wumpus_img.get_size()
                        new_size = (int(orig_size[0] * pulse), int(orig_size[1] * pulse))
                        
                        # Scale the image with the pulse effect
                        scaled_wumpus = pygame.transform.scale(wumpus_img, new_size)
                        
                        # Center the wumpus in the cell
                        wumpus_x = screen_x + (CELL_SIZE - new_size[0]) // 2
                        wumpus_y = screen_y + (CELL_SIZE - new_size[1]) // 2
                        
                        # Add a red glow behind the Wumpus
                        glow_radius = int(CELL_SIZE // 2.5)
                        glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                        
                        for x_pos in range(glow_radius * 2):
                            for y_pos in range(glow_radius * 2):
                                distance = math.sqrt((x_pos - glow_radius) ** 2 + (y_pos - glow_radius) ** 2)
                                if distance < glow_radius:
                                    alpha = max(0, 255 - int(255 * distance / glow_radius))
                                    glow_surface.set_at((x_pos, y_pos), (255, 0, 0, alpha // 4))
                        
                        # Draw the glow
                        self.screen.blit(glow_surface, 
                                        (screen_x + CELL_SIZE // 2 - glow_radius, 
                                         screen_y + CELL_SIZE // 2 - glow_radius))
                        
                        # Draw the Wumpus
                        self.screen.blit(scaled_wumpus, (wumpus_x, wumpus_y))
                    
                    if Element.PIT in cell_contents:
                        # Create a swirling pit effect
                        pit_center_x = screen_x + CELL_SIZE // 2
                        pit_center_y = screen_y + CELL_SIZE // 2
                        pit_radius = CELL_SIZE // 2 - 5
                        
                        # Draw concentric circles with decreasing radius and darker colors
                        for i in range(5):
                            # Calculate radius with a swirl effect
                            time_offset = pygame.time.get_ticks() * 0.001
                            radius_offset = math.sin(time_offset + i) * 2
                            current_radius = int(pit_radius - i * 5 + radius_offset)
                            
                            if current_radius > 0:
                                # Darker colors for deeper circles
                                darkness = 50 - i * 10
                                color = (darkness, darkness, darkness)
                                pygame.draw.circle(self.screen, color, (pit_center_x, pit_center_y), current_radius)
                        
                        # Draw swirling effect
                        time = pygame.time.get_ticks() * 0.002
                        for i in range(4):
                            angle_offset = time + i * math.pi / 2
                            start_angle = angle_offset
                            end_angle = angle_offset + math.pi
                            
                            # Calculate arc points
                            arc_points = []
                            for j in range(20):
                                angle = start_angle + (end_angle - start_angle) * j / 19
                                radius = pit_radius - 10 - i * 5
                                x = int(pit_center_x + math.cos(angle) * radius)
                                y = int(pit_center_y + math.sin(angle) * radius)
                                arc_points.append((x, y))
                            
                            # Draw the arc
                            if len(arc_points) > 1:
                                pygame.draw.lines(self.screen, (20, 20, 20), False, arc_points, 2)
                        
                        # Add the pit image on top for texture
                        pit_img = self.images['pit']
                        pit_rect = pit_img.get_rect(center=(pit_center_x, pit_center_y))
                        self.screen.blit(pit_img, pit_rect)
                    
                    if Element.GOLD in cell_contents:
                        # Draw a subtle glow effect behind the gold
                        glow_radius = CELL_SIZE // 3 + 5 + int(math.sin(pygame.time.get_ticks() * 0.005) * 3)
                        glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                        
                        # Create radial gradient for glow
                        for x in range(glow_radius * 2):
                            for y in range(glow_radius * 2):
                                distance = math.sqrt((x - glow_radius) ** 2 + (y - glow_radius) ** 2)
                                if distance < glow_radius:
                                    alpha = max(0, 255 - int(255 * distance / glow_radius))
                                    glow_surface.set_at((x, y), (255, 215, 0, alpha // 3))
                        
                        # Draw the glow
                        self.screen.blit(glow_surface, 
                                        (screen_x + CELL_SIZE // 2 - glow_radius, 
                                         screen_y + CELL_SIZE // 2 - glow_radius))
                        
                        # Draw the gold icon centered in the cell
                        gold_img = self.images['gold']
                        gold_rect = gold_img.get_rect(center=(screen_x + CELL_SIZE // 2, screen_y + CELL_SIZE // 2))
                        self.screen.blit(gold_img, gold_rect)
                    
                    if Element.PLAYER in cell_contents:
                        # Draw highlight around player
                        player_center_x = screen_x + CELL_SIZE // 2
                        player_center_y = screen_y + CELL_SIZE // 2
                        
                        # Create pulsing highlight effect
                        highlight_radius = int(CELL_SIZE // 2 - 5 + int(math.sin(pygame.time.get_ticks() * 0.004) * 3))
                        highlight_color = (100, 255, 150, 100)  # Semi-transparent green
                        
                        # Draw the highlight
                        highlight_surface = pygame.Surface((highlight_radius * 2, highlight_radius * 2), pygame.SRCALPHA)
                        pygame.draw.circle(highlight_surface, highlight_color, 
                                          (highlight_radius, highlight_radius), highlight_radius)
                        
                        # Apply a blur effect by scaling down and up
                        small_surface = pygame.transform.scale(highlight_surface, 
                                                             (highlight_radius, highlight_radius))
                        blurred_surface = pygame.transform.scale(small_surface, 
                                                               (highlight_radius * 2, highlight_radius * 2))
                        
                        # Draw the highlight
                        self.screen.blit(blurred_surface, 
                                        (player_center_x - highlight_radius, 
                                         player_center_y - highlight_radius))
                        
                        # Draw player centered in the cell
                        player_img = self.images['player']
                        player_rect = player_img.get_rect(center=(player_center_x, player_center_y))
                        self.screen.blit(player_img, player_rect)
                        
                        # Show player with gold with enhanced effect
                        if self.has_gold:
                            # Draw gold orbiting around player
                            orbit_angle = pygame.time.get_ticks() * 0.003
                            orbit_radius = CELL_SIZE // 3
                            gold_x = player_center_x + math.cos(orbit_angle) * orbit_radius
                            gold_y = player_center_y + math.sin(orbit_angle) * orbit_radius
                            
                            # Draw small gold circle
                            mini_gold_radius = CELL_SIZE // 8
                            pygame.draw.circle(self.screen, GOLD_COLOR, (int(gold_x), int(gold_y)), mini_gold_radius)
                            
                            # Add sparkle effect
                            sparkle_time = pygame.time.get_ticks() * 0.01
                            for i in range(4):
                                sparkle_angle = sparkle_time + i * math.pi / 2
                                sparkle_x = gold_x + math.cos(sparkle_angle) * (mini_gold_radius + 2)
                                sparkle_y = gold_y + math.sin(sparkle_angle) * (mini_gold_radius + 2)
                                pygame.draw.line(self.screen, (255, 255, 200), 
                                               (int(sparkle_x - 2), int(sparkle_y - 2)), 
                                               (int(sparkle_x + 2), int(sparkle_y + 2)), 1)
                                pygame.draw.line(self.screen, (255, 255, 200), 
                                               (int(sparkle_x - 2), int(sparkle_y + 2)), 
                                               (int(sparkle_x + 2), int(sparkle_y - 2)), 1)
    
    def draw_game_over(self):
        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            if self.win:
                game_over_text = self.title_font.render("YOU WON!", True, (50, 255, 50))
            else:
                game_over_text = self.title_font.render("GAME OVER", True, (255, 50, 50))
            
            restart_text = self.font.render("Press R to restart", True, TEXT_COLOR)
            
            self.screen.blit(game_over_text, 
                            (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, 
                             SCREEN_HEIGHT // 2 - game_over_text.get_height()))
            
            self.screen.blit(restart_text, 
                            (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, 
                             SCREEN_HEIGHT // 2 + restart_text.get_height()))
    
    def draw(self):
        # Draw background
        self.screen.blit(self.images['background'], (0, 0))
        
        # Update and draw environmental animations
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time
        
        self.update_environment(dt)
        self.draw_environment()
        
        # Draw side panels
        self.draw_left_panel()
        self.draw_right_panel()
        
        # Draw the three main sections
        self.draw_title_area()
        self.draw_grid()
        self.draw_status_area()
        
        # Draw game over overlay if needed
        self.draw_game_over()
        
        pygame.display.flip()

def main():
    game = WumpusWorld()
    clock = pygame.time.Clock()
    
    # For smooth animations
    target_fps = 60
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.VIDEORESIZE:
                game.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                game.handle_resize(event.w, event.h)
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                
                if event.key == pygame.K_r:
                    game.reset_game()
                
                if not game.game_over:
                    if event.key == pygame.K_UP:
                        game.move_player(-1, 0)
                    elif event.key == pygame.K_DOWN:
                        game.move_player(1, 0)
                    elif event.key == pygame.K_LEFT:
                        game.move_player(0, -1)
                    elif event.key == pygame.K_RIGHT:
                        game.move_player(0, 1)
        
        game.draw()
        clock.tick(target_fps)  # Higher FPS for smoother animations

if __name__ == "__main__":
    main()
            y = random.randint(0, SCREEN_HEIGHT)
            radius = random.randint(5, 50)
            color_value = random.randint(30, 60)
            color = (color_value, color_value//2, color_value)
            pygame.draw.circle(bg_surface, color, (x, y), radius)
        
        # Add some "stalactites" at the top
        for i in range(0, SCREEN_WIDTH, 40):
            height = random.randint(50, 150)
            width = random.randint(20, 40)
            points = [
                (i, 0),
                (i + width//2, height),
                (i + width, 0)
            ]
            pygame.draw.polygon(bg_surface, (40, 30, 50), points)
        
        # Add some "stalagmites" at the bottom
        for i in range(0, SCREEN_WIDTH, 60):
            height = random.randint(50, 150)
            width = random.randint(20, 40)
            points = [
                (i, SCREEN_HEIGHT),
                (i + width//2, SCREEN_HEIGHT - height),
                (i + width, SCREEN_HEIGHT)
            ]
            pygame.draw.polygon(bg_surface, (40, 30, 50), points)
        
        # Save the background image
        pygame.image.save(bg_surface, 'images/background.png')
    
    def create_panel_images(self):
        """Create custom panel images"""
        # Left panel - darker with hint styling
        left_panel = pygame.Surface((SIDE_PANEL_WIDTH, SCREEN_HEIGHT))
        left_panel.fill((15, 10, 25))
        
        # Add some decorative elements
        for i in range(0, SCREEN_HEIGHT, 40):
            pygame.draw.line(left_panel, (40, 30, 60), (10, i), (SIDE_PANEL_WIDTH-10, i), 2)
        
        # Add a title area
        pygame.draw.rect(left_panel, (30, 20, 50), (10, 10, SIDE_PANEL_WIDTH-20, 60))
        pygame.draw.rect(left_panel, (50, 40, 70), (10, 10, SIDE_PANEL_WIDTH-20, 60), 2)
        
        # Save the left panel image
        pygame.image.save(left_panel, 'images/left_panel.png')
        
        # Right panel - slightly lighter with stat styling
        right_panel = pygame.Surface((SIDE_PANEL_WIDTH, SCREEN_HEIGHT))
        right_panel.fill((25, 15, 35))
        
        # Add some decorative elements
        for i in range(0, SCREEN_HEIGHT, 60):
            pygame.draw.rect(right_panel, (40, 30, 60), (10, i, SIDE_PANEL_WIDTH-20, 50), 1)
        
        # Add a title area
        pygame.draw.rect(right_panel, (35, 25, 55), (10, 10, SIDE_PANEL_WIDTH-20, 60))
        pygame.draw.rect(right_panel, (55, 45, 75), (10, 10, SIDE_PANEL_WIDTH-20, 60), 2)
        
        # Save the right panel image
        pygame.image.save(right_panel, 'images/right_panel.png')
    
    def create_character_images(self):
        """Create custom character images"""
        # Player image - green explorer
        player_size = 64
        player = pygame.Surface((player_size, player_size), pygame.SRCALPHA)
        
        # Body
        pygame.draw.circle(player, (50, 200, 50), (player_size//2, player_size//2), player_size//3)
        # Head
        pygame.draw.circle(player, (220, 180, 150), (player_size//2, player_size//3), player_size//5)
        # Eyes
        pygame.draw.circle(player, (0, 0, 0), (player_size//2 - 5, player_size//3 - 2), 3)
        pygame.draw.circle(player, (0, 0, 0), (player_size//2 + 5, player_size//3 - 2), 3)
        # Helmet
        pygame.draw.arc(player, (100, 100, 100), (player_size//4, player_size//6, player_size//2, player_size//3), 0, 3.14, 3)
        
        # Save the player image
        pygame.image.save(player, 'images/player.png')
        
        # Wumpus image - red monster
        wumpus_size = 64
        wumpus = pygame.Surface((wumpus_size, wumpus_size), pygame.SRCALPHA)
        
        # Body
        pygame.draw.circle(wumpus, (200, 50, 50), (wumpus_size//2, wumpus_size//2), wumpus_size//3)
        # Eyes
        pygame.draw.circle(wumpus, (255, 255, 0), (wumpus_size//2 - 8, wumpus_size//3), 6)
        pygame.draw.circle(wumpus, (255, 255, 0), (wumpus_size//2 + 8, wumpus_size//3), 6)
        pygame.draw.circle(wumpus, (0, 0, 0), (wumpus_size//2 - 8, wumpus_size//3), 3)
        pygame.draw.circle(wumpus, (0, 0, 0), (wumpus_size//2 + 8, wumpus_size//3), 3)
        # Teeth
        for i in range(-2, 3):
            pygame.draw.rect(wumpus, (255, 255, 255), (wumpus_size//2 + i*5, wumpus_size//2, 4, 8))
        
        # Save the wumpus image
        pygame.image.save(wumpus, 'images/wumpus.png')
        
        # Gold image - yellow treasure
        gold_size = 64
        gold = pygame.Surface((gold_size, gold_size), pygame.SRCALPHA)
        
        # Gold pile
        pygame.draw.circle(gold, (255, 215, 0), (gold_size//2, gold_size//2), gold_size//3)
        pygame.draw.circle(gold, (255, 235, 100), (gold_size//2 - 5, gold_size//2 - 5), gold_size//6)
        
        # Sparkles
        for _ in range(5):
            x = random.randint(gold_size//4, 3*gold_size//4)
            y = random.randint(gold_size//4, 3*gold_size//4)
            size = random.randint(3, 6)
            pygame.draw.circle(gold, (255, 255, 255), (x, y), size)
        
        # Save the gold image
        pygame.image.save(gold, 'images/gold.png')
        
        # Pit image - dark hole
        pit_size = 64
        pit = pygame.Surface((pit_size, pit_size), pygame.SRCALPHA)
        
        # Dark circle for pit
        pygame.draw.circle(pit, (20, 20, 20), (pit_size//2, pit_size//2), pit_size//3)
        # Add depth with concentric circles
        pygame.draw.circle(pit, (40, 40, 40), (pit_size//2, pit_size//2), pit_size//3, 3)
        pygame.draw.circle(pit, (60, 60, 60), (pit_size//2, pit_size//2), pit_size//4, 2)
        pygame.draw.circle(pit, (80, 80, 80), (pit_size//2, pit_size//2), pit_size//6, 1)
        
        # Save the pit image
        pygame.image.save(pit, 'images/pit.png')
    def create_background_image(self):
        """Create a custom background image with a cave-like pattern"""
        # Create the background surface
        bg_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # Fill with dark base color
        bg_surface.fill((20, 15, 30))
        
        # Add some random cave-like patterns
        for _ in range(500):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            radius = random.randint(5, 50)
            color_value = random.randint(30, 60)
            color = (color_value, color_value//2, color_value)
            pygame.draw.circle(bg_surface, color, (x, y), radius)
        
        # Add some "stalactites" at the top
        for i in range(0, SCREEN_WIDTH, 40):
            height = random.randint(50, 150)
            width = random.randint(20, 40)
            points = [
                (i, 0),
                (i + width//2, height),
                (i + width, 0)
            ]
            pygame.draw.polygon(bg_surface, (40, 30, 50), points)
        
        # Add some "stalagmites" at the bottom
        for i in range(0, SCREEN_WIDTH, 60):
            height = random.randint(50, 150)
            width = random.randint(20, 40)
            points = [
                (i, SCREEN_HEIGHT),
                (i + width//2, SCREEN_HEIGHT - height),
                (i + width, SCREEN_HEIGHT)
            ]
            pygame.draw.polygon(bg_surface, (40, 30, 50), points)
        
        # Save the background image
        pygame.image.save(bg_surface, 'images/background.png')
        return bg_surface
    
    def create_left_panel_image(self):
        """Create custom left panel image"""
        # Left panel - darker with hint styling
        left_panel = pygame.Surface((SIDE_PANEL_WIDTH, SCREEN_HEIGHT))
        left_panel.fill((15, 10, 25))
        
        # Add some decorative elements
        for i in range(0, SCREEN_HEIGHT, 40):
            pygame.draw.line(left_panel, (40, 30, 60), (10, i), (SIDE_PANEL_WIDTH-10, i), 2)
        
        # Add a title area
        pygame.draw.rect(left_panel, (30, 20, 50), (10, 10, SIDE_PANEL_WIDTH-20, 60))
        pygame.draw.rect(left_panel, (50, 40, 70), (10, 10, SIDE_PANEL_WIDTH-20, 60), 2)
        
        # Save the left panel image
        pygame.image.save(left_panel, 'images/left_panel.png')
        return left_panel
    
    def create_right_panel_image(self):
        """Create custom right panel image"""
        # Right panel - slightly lighter with stat styling
        right_panel = pygame.Surface((SIDE_PANEL_WIDTH, SCREEN_HEIGHT))
        right_panel.fill((25, 15, 35))
        
        # Add some decorative elements
        for i in range(0, SCREEN_HEIGHT, 60):
            pygame.draw.rect(right_panel, (40, 30, 60), (10, i, SIDE_PANEL_WIDTH-20, 50), 1)
        
        # Add a title area
        pygame.draw.rect(right_panel, (35, 25, 55), (10, 10, SIDE_PANEL_WIDTH-20, 60))
        pygame.draw.rect(right_panel, (55, 45, 75), (10, 10, SIDE_PANEL_WIDTH-20, 60), 2)
        
        # Save the right panel image
        pygame.image.save(right_panel, 'images/right_panel.png')
        return right_panel
    
    def create_player_image(self):
        """Create custom player image"""
        # Player image - green explorer
        player_size = 64
        player = pygame.Surface((player_size, player_size), pygame.SRCALPHA)
        
        # Body
        pygame.draw.circle(player, (50, 200, 50), (player_size//2, player_size//2), player_size//3)
        # Head
        pygame.draw.circle(player, (220, 180, 150), (player_size//2, player_size//3), player_size//5)
        # Eyes
        pygame.draw.circle(player, (0, 0, 0), (player_size//2 - 5, player_size//3 - 2), 3)
        pygame.draw.circle(player, (0, 0, 0), (player_size//2 + 5, player_size//3 - 2), 3)
        # Helmet
        pygame.draw.arc(player, (100, 100, 100), (player_size//4, player_size//6, player_size//2, player_size//3), 0, 3.14, 3)
        
        # Save the player image
        pygame.image.save(player, 'images/player.png')
        return player
    
    def create_wumpus_image(self):
        """Create custom wumpus image"""
        # Wumpus image - red monster
        wumpus_size = 64
        wumpus = pygame.Surface((wumpus_size, wumpus_size), pygame.SRCALPHA)
        
        # Body
        pygame.draw.circle(wumpus, (200, 50, 50), (wumpus_size//2, wumpus_size//2), wumpus_size//3)
        # Eyes
        pygame.draw.circle(wumpus, (255, 255, 0), (wumpus_size//2 - 8, wumpus_size//3), 6)
        pygame.draw.circle(wumpus, (255, 255, 0), (wumpus_size//2 + 8, wumpus_size//3), 6)
        pygame.draw.circle(wumpus, (0, 0, 0), (wumpus_size//2 - 8, wumpus_size//3), 3)
        pygame.draw.circle(wumpus, (0, 0, 0), (wumpus_size//2 + 8, wumpus_size//3), 3)
        # Teeth
        for i in range(-2, 3):
            pygame.draw.rect(wumpus, (255, 255, 255), (wumpus_size//2 + i*5, wumpus_size//2, 4, 8))
        
        # Save the wumpus image
        pygame.image.save(wumpus, 'images/wumpus.png')
        return wumpus
    
    def create_gold_image(self):
        """Create custom gold image"""
        # Gold image - yellow treasure
        gold_size = 64
        gold = pygame.Surface((gold_size, gold_size), pygame.SRCALPHA)
        
        # Gold pile
        pygame.draw.circle(gold, (255, 215, 0), (gold_size//2, gold_size//2), gold_size//3)
        pygame.draw.circle(gold, (255, 235, 100), (gold_size//2 - 5, gold_size//2 - 5), gold_size//6)
        
        # Sparkles
        for _ in range(5):
            x = random.randint(gold_size//4, 3*gold_size//4)
            y = random.randint(gold_size//4, 3*gold_size//4)
            size = random.randint(3, 6)
            pygame.draw.circle(gold, (255, 255, 255), (x, y), size)
        
        # Save the gold image
        pygame.image.save(gold, 'images/gold.png')
        return gold
    
    def create_pit_image(self):
        """Create custom pit image"""
        # Pit image - dark hole
        pit_size = 64
        pit = pygame.Surface((pit_size, pit_size), pygame.SRCALPHA)
        
        # Dark circle for pit
        pygame.draw.circle(pit, (20, 20, 20), (pit_size//2, pit_size//2), pit_size//3)
        # Add depth with concentric circles
        pygame.draw.circle(pit, (40, 40, 40), (pit_size//2, pit_size//2), pit_size//3, 3)
        pygame.draw.circle(pit, (60, 60, 60), (pit_size//2, pit_size//2), pit_size//4, 2)
        pygame.draw.circle(pit, (80, 80, 80), (pit_size//2, pit_size//2), pit_size//6, 1)
        
        # Save the pit image
        pygame.image.save(pit, 'images/pit.png')
        return pit
    def initialize_environment(self):
        """Initialize environmental animation elements"""
        # Create dust particles
        for _ in range(20):
            self.dust_particles.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'size': random.uniform(1, 3),
                'speed': random.uniform(0.2, 1.0),
                'angle': random.uniform(0, 2 * math.pi),
                'alpha': random.randint(50, 150)
            })
        
        # Create light flickers (torches on the walls)
        for _ in range(8):
            self.light_flickers.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'radius': random.randint(30, 80),
                'intensity': random.uniform(0.5, 1.0),
                'phase': random.uniform(0, 2 * math.pi)
            })
        
        # Create water drops
        for _ in range(15):
            self.water_drops.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT // 3),  # Only in top third
                'speed': random.uniform(1, 3),
                'size': random.uniform(1, 3),
                'active': False,
                'timer': random.uniform(1, 10)  # Random start time
            })
        
        # Create bats
        for _ in range(3):
            self.bat_positions.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT // 4),  # Only near the top
                'speed': random.uniform(0.5, 2.0),
                'direction': random.choice([-1, 1]),
                'size': random.randint(5, 10),
                'flap_speed': random.uniform(0.1, 0.3),
                'flap_state': 0
            })
    def update_environment(self, dt):
        """Update environmental animations"""
        self.env_time += dt
        
        # Update dust particles
        for particle in self.dust_particles:
            # Move particles slowly
            particle['x'] += math.cos(particle['angle']) * particle['speed'] * dt
            particle['y'] += math.sin(particle['angle']) * particle['speed'] * dt
            
            # Wrap around screen edges
            if particle['x'] < 0:
                particle['x'] = SCREEN_WIDTH
            elif particle['x'] > SCREEN_WIDTH:
                particle['x'] = 0
            if particle['y'] < 0:
                particle['y'] = SCREEN_HEIGHT
            elif particle['y'] > SCREEN_HEIGHT:
                particle['y'] = 0
                
            # Occasionally change direction
            if random.random() < 0.01:
                particle['angle'] = random.uniform(0, 2 * math.pi)
        
        # Update light flickers
        for light in self.light_flickers:
            # Flicker intensity based on sine wave with random phase
            light['intensity'] = 0.5 + 0.5 * math.sin(self.env_time * 2 + light['phase'])
        
        # Update water drops
        for drop in self.water_drops:
            if drop['active']:
                # Move active drops down
                drop['y'] += drop['speed'] * dt * 60
                
                # Reset if reached bottom
                if drop['y'] > SCREEN_HEIGHT:
                    drop['active'] = False
                    drop['timer'] = random.uniform(1, 5)
                    drop['y'] = random.randint(0, SCREEN_HEIGHT // 3)
                    drop['x'] = random.randint(0, SCREEN_WIDTH)
            else:
                # Count down timer for inactive drops
                drop['timer'] -= dt
                if drop['timer'] <= 0:
                    drop['active'] = True
        
        # Update bats
        for bat in self.bat_positions:
            # Move bats horizontally
            bat['x'] += bat['speed'] * bat['direction'] * dt * 30
            
            # Change direction if at screen edge
            if bat['x'] < 0 or bat['x'] > SCREEN_WIDTH:
                bat['direction'] *= -1
            
            # Update flapping animation
            bat['flap_state'] = (bat['flap_state'] + bat['flap_speed'] * dt * 60) % 2
            
            # Occasionally change vertical position
            if random.random() < 0.01:
                bat['y'] += random.uniform(-10, 10)
                bat['y'] = max(0, min(SCREEN_HEIGHT // 3, bat['y']))
    
    def draw_environment(self):
        """Draw environmental animations"""
        # Draw light flickers (under everything else)
        for light in self.light_flickers:
            # Create a surface for the light with alpha
            light_surface = pygame.Surface((light['radius'] * 2, light['radius'] * 2), pygame.SRCALPHA)
            
            # Calculate color based on intensity (yellow-orange glow)
            intensity = int(255 * light['intensity'])
            color = (intensity, intensity // 2, intensity // 4, 100)
            
            # Draw the light as a radial gradient
            pygame.draw.circle(light_surface, color, (light['radius'], light['radius']), light['radius'])
            
            # Blit the light onto the screen
            self.screen.blit(light_surface, (light['x'] - light['radius'], light['y'] - light['radius']), special_flags=pygame.BLEND_ADD)
        
        # Draw water drops
        for drop in self.water_drops:
            if drop['active']:
                # Draw the drop as a small blue ellipse
                pygame.draw.ellipse(self.screen, (100, 150, 255, 200), 
                                   (drop['x'], drop['y'], drop['size'], drop['size'] * 2))
                
                # Draw splash if near bottom
                if drop['y'] > SCREEN_HEIGHT - 20 and drop['y'] < SCREEN_HEIGHT - 10:
                    pygame.draw.circle(self.screen, (100, 150, 255, 100),
                                     (drop['x'], SCREEN_HEIGHT - 5), drop['size'] * 2)
        
        # Draw bats
        for bat in self.bat_positions:
            # Draw the bat body
            pygame.draw.circle(self.screen, (40, 40, 40), (int(bat['x']), int(bat['y'])), bat['size'])
            
            # Draw the wings based on flap state
            wing_extension = 10 + 5 * math.sin(bat['flap_state'] * math.pi)
            
            # Left wing
            pygame.draw.polygon(self.screen, (40, 40, 40), [
                (bat['x'], bat['y']),
                (bat['x'] - wing_extension, bat['y'] - wing_extension // 2),
                (bat['x'] - wing_extension, bat['y'] + wing_extension // 2)
            ])
            
            # Right wing
            pygame.draw.polygon(self.screen, (40, 40, 40), [
                (bat['x'], bat['y']),
                (bat['x'] + wing_extension, bat['y'] - wing_extension // 2),
                (bat['x'] + wing_extension, bat['y'] + wing_extension // 2)
            ])
        
        # Draw dust particles (on top of everything)
        for particle in self.dust_particles:
            # Draw the particle as a small semi-transparent circle
            pygame.draw.circle(self.screen, (200, 200, 200, particle['alpha']),
                             (int(particle['x']), int(particle['y'])), particle['size'])
