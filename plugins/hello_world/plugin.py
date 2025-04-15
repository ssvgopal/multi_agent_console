"""
Hello World - A simple example plugin for MultiAgentConsole

Author: Sai Sunkara
Version: 1.0.0
"""

from multi_agent_console.plugin.base import Plugin


class HelloWorldPlugin(Plugin):
    """Hello World plugin implementation."""
    
    @property
    def id(self) -> str:
        """Get the plugin ID."""
        return "hello_world"
    
    @property
    def name(self) -> str:
        """Get the plugin name."""
        return "Hello World"
    
    @property
    def version(self) -> str:
        """Get the plugin version."""
        return "1.0.0"
    
    @property
    def description(self) -> str:
        """Get the plugin description."""
        return "A simple example plugin for MultiAgentConsole"
    
    @property
    def author(self) -> str:
        """Get the plugin author."""
        return "Sai Sunkara"
    
    def initialize(self, context):
        """Initialize the plugin."""
        print(f"Hello World plugin initialized with context: {context}")
        return True
    
    def shutdown(self):
        """Shutdown the plugin."""
        print("Hello World plugin shutdown")
        return True
    
    def get_capabilities(self):
        """Get the plugin capabilities."""
        return ["greeting"]
    
    def handle_event(self, event_type, event_data):
        """Handle an event."""
        if event_type == "greeting":
            name = event_data.get("name", "World")
            return {"message": f"Hello, {name}!"}
        return None
    
    def get_ui_components(self):
        """Get UI components provided by the plugin."""
        return {
            "sidebar": {
                "title": "Hello World",
                "icon": "👋",
                "content": """
                <div class="p-4">
                    <h3 class="text-lg font-medium mb-2">Hello World Plugin</h3>
                    <p class="text-gray-600 mb-4">This is a simple example plugin.</p>
                    <div class="mb-4">
                        <label class="block text-sm font-medium mb-1">Your Name</label>
                        <input type="text" id="hello-name" class="w-full border rounded px-3 py-2" placeholder="Enter your name">
                    </div>
                    <button id="hello-greet-btn" class="bg-blue-600 text-white px-4 py-2 rounded">
                        Greet Me
                    </button>
                    <div id="hello-result" class="mt-4 p-3 bg-gray-100 rounded hidden"></div>
                </div>
                <script>
                    document.getElementById('hello-greet-btn').addEventListener('click', function() {
                        const name = document.getElementById('hello-name').value || 'World';
                        fetch('/api/plugin/hello_world/greet', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ name: name })
                        })
                        .then(response => response.json())
                        .then(data => {
                            const resultEl = document.getElementById('hello-result');
                            resultEl.textContent = data.message;
                            resultEl.classList.remove('hidden');
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            alert('Error: ' + error.message);
                        });
                    });
                </script>
                """
            }
        }
