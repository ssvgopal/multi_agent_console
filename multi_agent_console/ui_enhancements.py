"""
UI Enhancements for MultiAgentConsole.

This module provides enhanced UI capabilities:
- Themes and color scheme customization
- Split-pane views for multitasking
- Keyboard shortcuts for power users
- Rich text formatting with syntax highlighting
- Progress indicators for long-running operations
- Auto-completion for commands and inputs
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from pathlib import Path

try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, guess_lexer
    from pygments.formatters import TerminalFormatter
    SYNTAX_HIGHLIGHT_AVAILABLE = True
except ImportError:
    SYNTAX_HIGHLIGHT_AVAILABLE = False


class ThemeManager:
    """Manages themes and color schemes for the UI."""
    
    # Default themes
    DEFAULT_THEMES = {
        "default": {
            "background": "#121212",
            "foreground": "#FFFFFF",
            "primary": "#4CAF50",
            "secondary": "#2196F3",
            "accent": "#FF9800",
            "success": "#4CAF50",
            "warning": "#FFC107",
            "error": "#F44336",
            "surface": "#1E1E1E",
            "text": "#FFFFFF"
        },
        "light": {
            "background": "#F5F5F5",
            "foreground": "#000000",
            "primary": "#4CAF50",
            "secondary": "#2196F3",
            "accent": "#FF9800",
            "success": "#4CAF50",
            "warning": "#FFC107",
            "error": "#F44336",
            "surface": "#FFFFFF",
            "text": "#000000"
        },
        "dark_blue": {
            "background": "#0D1117",
            "foreground": "#C9D1D9",
            "primary": "#58A6FF",
            "secondary": "#1F6FEB",
            "accent": "#F0883E",
            "success": "#3FB950",
            "warning": "#D29922",
            "error": "#F85149",
            "surface": "#161B22",
            "text": "#C9D1D9"
        },
        "solarized": {
            "background": "#002B36",
            "foreground": "#839496",
            "primary": "#268BD2",
            "secondary": "#2AA198",
            "accent": "#CB4B16",
            "success": "#859900",
            "warning": "#B58900",
            "error": "#DC322F",
            "surface": "#073642",
            "text": "#839496"
        },
        "nord": {
            "background": "#2E3440",
            "foreground": "#D8DEE9",
            "primary": "#88C0D0",
            "secondary": "#81A1C1",
            "accent": "#EBCB8B",
            "success": "#A3BE8C",
            "warning": "#EBCB8B",
            "error": "#BF616A",
            "surface": "#3B4252",
            "text": "#E5E9F0"
        }
    }
    
    def __init__(self, themes_path: str = "data/themes.json"):
        """Initialize the theme manager.
        
        Args:
            themes_path: Path to the themes configuration file
        """
        self.themes_path = themes_path
        self.themes = {}
        self.current_theme = "default"
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(themes_path), exist_ok=True)
        
        # Load themes
        self.load_themes()
        
        logging.info("Theme Manager initialized")
    
    def load_themes(self) -> None:
        """Load themes from the configuration file."""
        # Start with default themes
        self.themes = self.DEFAULT_THEMES.copy()
        
        if os.path.exists(self.themes_path):
            try:
                with open(self.themes_path, 'r') as f:
                    custom_themes = json.load(f)
                
                # Merge custom themes with default themes
                self.themes.update(custom_themes)
                
                logging.info(f"Loaded themes from {self.themes_path}")
            except json.JSONDecodeError:
                logging.error(f"Error parsing themes file: {self.themes_path}")
        else:
            # Create default themes file
            self.save_themes()
    
    def save_themes(self) -> None:
        """Save themes to the configuration file."""
        # Only save custom themes (not default ones)
        custom_themes = {}
        for theme_name, theme in self.themes.items():
            if theme_name not in self.DEFAULT_THEMES:
                custom_themes[theme_name] = theme
        
        with open(self.themes_path, 'w') as f:
            json.dump(custom_themes, f, indent=2)
        
        logging.info(f"Saved themes to {self.themes_path}")
    
    def get_theme(self, theme_name: Optional[str] = None) -> Dict[str, str]:
        """Get a theme by name.
        
        Args:
            theme_name: Name of the theme (default: current theme)
            
        Returns:
            Theme colors as a dictionary
        """
        theme_name = theme_name or self.current_theme
        return self.themes.get(theme_name, self.themes["default"])
    
    def set_current_theme(self, theme_name: str) -> bool:
        """Set the current theme.
        
        Args:
            theme_name: Name of the theme
            
        Returns:
            True if the theme was set, False otherwise
        """
        if theme_name in self.themes:
            self.current_theme = theme_name
            return True
        return False
    
    def create_theme(self, theme_name: str, colors: Dict[str, str]) -> bool:
        """Create a new theme.
        
        Args:
            theme_name: Name of the theme
            colors: Theme colors as a dictionary
            
        Returns:
            True if the theme was created, False otherwise
        """
        if theme_name in self.themes:
            return False
        
        # Validate colors
        required_colors = set(self.themes["default"].keys())
        if not required_colors.issubset(set(colors.keys())):
            return False
        
        self.themes[theme_name] = colors
        self.save_themes()
        return True
    
    def update_theme(self, theme_name: str, colors: Dict[str, str]) -> bool:
        """Update an existing theme.
        
        Args:
            theme_name: Name of the theme
            colors: Theme colors as a dictionary
            
        Returns:
            True if the theme was updated, False otherwise
        """
        if theme_name not in self.themes:
            return False
        
        # Update colors
        self.themes[theme_name].update(colors)
        self.save_themes()
        return True
    
    def delete_theme(self, theme_name: str) -> bool:
        """Delete a theme.
        
        Args:
            theme_name: Name of the theme
            
        Returns:
            True if the theme was deleted, False otherwise
        """
        if theme_name not in self.themes or theme_name in self.DEFAULT_THEMES:
            return False
        
        del self.themes[theme_name]
        
        # If the current theme was deleted, switch to default
        if self.current_theme == theme_name:
            self.current_theme = "default"
        
        self.save_themes()
        return True
    
    def list_themes(self) -> List[str]:
        """List all available themes.
        
        Returns:
            List of theme names
        """
        return list(self.themes.keys())
    
    def get_theme_css(self, theme_name: Optional[str] = None) -> str:
        """Get the CSS for a theme.
        
        Args:
            theme_name: Name of the theme (default: current theme)
            
        Returns:
            Theme CSS as a string
        """
        theme = self.get_theme(theme_name)
        
        css = """
        $background: {background};
        $foreground: {foreground};
        $primary: {primary};
        $secondary: {secondary};
        $accent: {accent};
        $success: {success};
        $warning: {warning};
        $error: {error};
        $surface: {surface};
        $text: {text};
        """.format(**theme)
        
        return css


class SyntaxHighlighter:
    """Provides syntax highlighting for code."""
    
    def __init__(self):
        """Initialize the syntax highlighter."""
        self.available = SYNTAX_HIGHLIGHT_AVAILABLE
        
        if not self.available:
            logging.warning("Pygments is not installed. Syntax highlighting will not be available.")
    
    def highlight_code(self, code: str, language: Optional[str] = None) -> str:
        """Highlight code with syntax highlighting.
        
        Args:
            code: Code to highlight
            language: Programming language (default: auto-detect)
            
        Returns:
            Highlighted code as a string
        """
        if not self.available:
            return code
        
        try:
            if language:
                lexer = get_lexer_by_name(language)
            else:
                lexer = guess_lexer(code)
            
            formatter = TerminalFormatter()
            return highlight(code, lexer, formatter)
        except Exception as e:
            logging.error(f"Error highlighting code: {e}")
            return code
    
    def get_supported_languages(self) -> List[str]:
        """Get a list of supported programming languages.
        
        Returns:
            List of supported languages
        """
        if not self.available:
            return []
        
        from pygments.lexers import get_all_lexers
        return sorted([lexer[0] for lexer in get_all_lexers()])


class ProgressIndicator:
    """Provides progress indicators for long-running operations."""
    
    def __init__(self):
        """Initialize the progress indicator."""
        self.spinners = {
            "dots": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
            "line": ["-", "\\", "|", "/"],
            "braille": ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"],
            "pulse": ["█", "▓", "▒", "░"],
            "points": ["∙∙∙", "●∙∙", "∙●∙", "∙∙●"],
            "arc": ["◜", "◠", "◝", "◞", "◡", "◟"],
            "arrows": ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"],
            "bars": ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█", "▇", "▆", "▅", "▄", "▃", "▁"],
            "clock": ["🕛", "🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚"]
        }
        
        self.progress_bars = {
            "ascii": ["[", "#", " ", "]"],
            "unicode": ["▕", "█", "░", "▏"],
            "blocks": ["▕", "█", "▒", "▏"],
            "dots": ["▕", "●", "○", "▏"],
            "arrows": ["▕", "→", "·", "▏"]
        }
    
    def get_spinner_frames(self, style: str = "dots") -> List[str]:
        """Get spinner animation frames.
        
        Args:
            style: Spinner style
            
        Returns:
            List of spinner frames
        """
        return self.spinners.get(style, self.spinners["dots"])
    
    def get_progress_bar(self, style: str = "unicode", width: int = 20, progress: float = 0.0) -> str:
        """Get a progress bar.
        
        Args:
            style: Progress bar style
            width: Width of the progress bar
            progress: Progress value (0.0 to 1.0)
            
        Returns:
            Progress bar as a string
        """
        progress = max(0.0, min(1.0, progress))
        bar_chars = self.progress_bars.get(style, self.progress_bars["unicode"])
        
        filled_width = int(width * progress)
        empty_width = width - filled_width
        
        bar = bar_chars[0] + bar_chars[1] * filled_width + bar_chars[2] * empty_width + bar_chars[3]
        percentage = f" {int(progress * 100)}%"
        
        return bar + percentage


class AutoCompleter:
    """Provides auto-completion for commands and inputs."""
    
    def __init__(self):
        """Initialize the auto-completer."""
        self.commands = set()
        self.history = []
        self.max_history = 100
    
    def add_command(self, command: str) -> None:
        """Add a command to the auto-completion list.
        
        Args:
            command: Command to add
        """
        self.commands.add(command)
    
    def add_commands(self, commands: List[str]) -> None:
        """Add multiple commands to the auto-completion list.
        
        Args:
            commands: Commands to add
        """
        self.commands.update(commands)
    
    def remove_command(self, command: str) -> None:
        """Remove a command from the auto-completion list.
        
        Args:
            command: Command to remove
        """
        if command in self.commands:
            self.commands.remove(command)
    
    def clear_commands(self) -> None:
        """Clear all commands from the auto-completion list."""
        self.commands.clear()
    
    def add_to_history(self, input_text: str) -> None:
        """Add input to the history.
        
        Args:
            input_text: Input text to add
        """
        if input_text and (not self.history or input_text != self.history[-1]):
            self.history.append(input_text)
            if len(self.history) > self.max_history:
                self.history.pop(0)
    
    def clear_history(self) -> None:
        """Clear the input history."""
        self.history.clear()
    
    def get_completions(self, prefix: str) -> List[str]:
        """Get auto-completion suggestions for a prefix.
        
        Args:
            prefix: Input prefix
            
        Returns:
            List of completion suggestions
        """
        return [cmd for cmd in self.commands if cmd.startswith(prefix)]
    
    def get_history_completions(self, prefix: str) -> List[str]:
        """Get auto-completion suggestions from history.
        
        Args:
            prefix: Input prefix
            
        Returns:
            List of completion suggestions from history
        """
        return [item for item in reversed(self.history) if item.startswith(prefix)]


class UIEnhancementManager:
    """Manages UI enhancements for MultiAgentConsole."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the UI enhancement manager.
        
        Args:
            data_dir: Directory for UI data
        """
        self.data_dir = data_dir
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize components
        self.theme_manager = ThemeManager(os.path.join(data_dir, "themes.json"))
        self.syntax_highlighter = SyntaxHighlighter()
        self.progress_indicator = ProgressIndicator()
        self.auto_completer = AutoCompleter()
        
        # Initialize default commands
        self._initialize_default_commands()
        
        logging.info("UI Enhancement Manager initialized")
    
    def _initialize_default_commands(self) -> None:
        """Initialize default commands for auto-completion."""
        default_commands = [
            "help", "exit", "clear", "theme", "set", "set_api_key",
            "git_status", "git_log", "git_diff",
            "connect_sqlite", "execute_query", "list_tables",
            "http_request", "weather_api", "news_api",
            "image_info", "ocr_image", "text_to_speech"
        ]
        
        self.auto_completer.add_commands(default_commands)
    
    def get_theme_css(self) -> str:
        """Get the CSS for the current theme.
        
        Returns:
            Theme CSS as a string
        """
        return self.theme_manager.get_theme_css()
    
    def set_theme(self, theme_name: str) -> bool:
        """Set the current theme.
        
        Args:
            theme_name: Name of the theme
            
        Returns:
            True if the theme was set, False otherwise
        """
        return self.theme_manager.set_current_theme(theme_name)
    
    def highlight_code(self, code: str, language: Optional[str] = None) -> str:
        """Highlight code with syntax highlighting.
        
        Args:
            code: Code to highlight
            language: Programming language (default: auto-detect)
            
        Returns:
            Highlighted code as a string
        """
        return self.syntax_highlighter.highlight_code(code, language)
    
    def get_progress_bar(self, width: int = 20, progress: float = 0.0, style: str = "unicode") -> str:
        """Get a progress bar.
        
        Args:
            width: Width of the progress bar
            progress: Progress value (0.0 to 1.0)
            style: Progress bar style
            
        Returns:
            Progress bar as a string
        """
        return self.progress_indicator.get_progress_bar(style, width, progress)
    
    def get_spinner_frames(self, style: str = "dots") -> List[str]:
        """Get spinner animation frames.
        
        Args:
            style: Spinner style
            
        Returns:
            List of spinner frames
        """
        return self.progress_indicator.get_spinner_frames(style)
    
    def get_completions(self, prefix: str) -> List[str]:
        """Get auto-completion suggestions.
        
        Args:
            prefix: Input prefix
            
        Returns:
            List of completion suggestions
        """
        return self.auto_completer.get_completions(prefix)
    
    def add_to_history(self, input_text: str) -> None:
        """Add input to the history.
        
        Args:
            input_text: Input text to add
        """
        self.auto_completer.add_to_history(input_text)
    
    def get_history_completions(self, prefix: str) -> List[str]:
        """Get auto-completion suggestions from history.
        
        Args:
            prefix: Input prefix
            
        Returns:
            List of completion suggestions from history
        """
        return self.auto_completer.get_history_completions(prefix)
    
    def add_command(self, command: str) -> None:
        """Add a command to the auto-completion list.
        
        Args:
            command: Command to add
        """
        self.auto_completer.add_command(command)
    
    def get_enhanced_css(self) -> str:
        """Get enhanced CSS for the UI.
        
        Returns:
            Enhanced CSS as a string
        """
        theme_css = self.theme_manager.get_theme_css()
        
        enhanced_css = f"""
        {theme_css}
        
        /* Enhanced UI Styles */
        
        /* Split Pane */
        #split-container {{
            width: 100%;
            height: 100%;
        }}
        
        #left-pane {{
            width: 30%;
            height: 100%;
            border-right: solid $primary;
        }}
        
        #right-pane {{
            width: 70%;
            height: 100%;
        }}
        
        /* Tabs */
        #tabs {{
            height: auto;
            background: $surface;
        }}
        
        .tab {{
            padding: 1 2;
            background: $surface;
            color: $text;
        }}
        
        .tab.active {{
            background: $primary 30%;
            color: $text;
            text-style: bold;
        }}
        
        /* Code Blocks */
        .code-block {{
            background: $surface;
            color: $text;
            border: wide $primary;
            padding: 1;
            margin: 1;
        }}
        
        /* Progress Bar */
        .progress-bar {{
            width: 100%;
            height: 1;
            margin: 1 0;
        }}
        
        /* Auto-complete */
        .completion-popup {{
            background: $surface;
            border: solid $primary;
            padding: 1;
            margin: 0;
        }}
        
        .completion-item {{
            padding: 0 1;
        }}
        
        .completion-item.selected {{
            background: $primary 30%;
        }}
        """
        
        return enhanced_css
