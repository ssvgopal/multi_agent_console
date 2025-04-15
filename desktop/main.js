const { app, BrowserWindow, Menu, Tray, dialog, ipcMain, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const Store = require('electron-store');
const fetch = require('node-fetch');
const fs = require('fs');

// Initialize settings store
const store = new Store({
  name: 'settings',
  defaults: {
    serverPort: 8007,
    startServerOnLaunch: true,
    minimizeToTray: true,
    syncEnabled: true,
    syncInterval: 30, // minutes
    theme: 'system', // 'light', 'dark', 'system'
    fontSize: 'medium', // 'small', 'medium', 'large'
    notifications: true,
    autoUpdate: true,
    offlineMode: false,
    developerMode: false
  }
});

// Global references
let mainWindow;
let tray;
let serverProcess;
let serverRunning = false;
let serverPort = store.get('serverPort');
let syncInterval;

// Create the main window
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'icons', process.platform === 'win32' ? 'icon.ico' : 'icon.png')
  });

  // Load the app
  if (serverRunning) {
    mainWindow.loadURL(`http://localhost:${serverPort}`);
  } else {
    mainWindow.loadFile(path.join(__dirname, 'offline.html'));
  }

  // Open DevTools in developer mode
  if (store.get('developerMode')) {
    mainWindow.webContents.openDevTools();
  }

  // Handle window close
  mainWindow.on('close', (event) => {
    if (store.get('minimizeToTray') && !app.isQuitting) {
      event.preventDefault();
      mainWindow.hide();
      return false;
    }
    return true;
  });

  // Create application menu
  createMenu();
}

// Create the application menu
function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Settings',
          click: () => openSettings()
        },
        { type: 'separator' },
        {
          label: 'Exit',
          click: () => {
            app.isQuitting = true;
            app.quit();
          }
        }
      ]
    },
    {
      label: 'Server',
      submenu: [
        {
          label: 'Start Server',
          click: () => startServer(),
          enabled: !serverRunning
        },
        {
          label: 'Stop Server',
          click: () => stopServer(),
          enabled: serverRunning
        },
        {
          label: 'Restart Server',
          click: () => {
            stopServer();
            setTimeout(() => startServer(), 1000);
          }
        }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'Documentation',
          click: () => shell.openExternal('https://github.com/ssvgopal/multi_agent_console')
        },
        {
          label: 'Report Issue',
          click: () => shell.openExternal('https://github.com/ssvgopal/multi_agent_console/issues')
        },
        { type: 'separator' },
        {
          label: 'About',
          click: () => showAboutDialog()
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// Create the tray icon
function createTray() {
  tray = new Tray(path.join(__dirname, 'icons', process.platform === 'win32' ? 'icon.ico' : 'icon.png'));
  
  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Open MultiAgentConsole',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
        } else {
          createWindow();
        }
      }
    },
    {
      label: serverRunning ? 'Stop Server' : 'Start Server',
      click: () => serverRunning ? stopServer() : startServer()
    },
    { type: 'separator' },
    {
      label: 'Settings',
      click: () => openSettings()
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        app.isQuitting = true;
        app.quit();
      }
    }
  ]);

  tray.setToolTip('MultiAgentConsole');
  tray.setContextMenu(contextMenu);

  tray.on('click', () => {
    if (mainWindow) {
      if (mainWindow.isVisible()) {
        mainWindow.hide();
      } else {
        mainWindow.show();
      }
    } else {
      createWindow();
    }
  });
}

// Start the server
function startServer() {
  if (serverRunning) return;

  const pythonExecutable = process.platform === 'win32' ? 'python' : 'python3';
  const args = ['-m', 'multi_agent_console', '--web', '--port', serverPort.toString()];
  
  // Add offline mode if enabled
  if (store.get('offlineMode')) {
    args.push('--offline');
  }

  try {
    serverProcess = spawn(pythonExecutable, args, {
      detached: false,
      stdio: 'pipe'
    });

    serverProcess.stdout.on('data', (data) => {
      console.log(`Server stdout: ${data}`);
      
      // Check if server is running
      if (data.toString().includes('Web interface started at')) {
        serverRunning = true;
        updateTrayAndMenu();
        
        // Reload main window if it exists
        if (mainWindow) {
          mainWindow.loadURL(`http://localhost:${serverPort}`);
        }
      }
    });

    serverProcess.stderr.on('data', (data) => {
      console.error(`Server stderr: ${data}`);
    });

    serverProcess.on('close', (code) => {
      console.log(`Server process exited with code ${code}`);
      serverRunning = false;
      updateTrayAndMenu();
    });

    // Check if server is running after a delay
    setTimeout(() => {
      checkServerStatus();
    }, 3000);
  } catch (error) {
    console.error('Failed to start server:', error);
    dialog.showErrorBox('Server Error', `Failed to start server: ${error.message}`);
  }
}

// Stop the server
function stopServer() {
  if (!serverRunning || !serverProcess) return;

  try {
    if (process.platform === 'win32') {
      spawn('taskkill', ['/pid', serverProcess.pid, '/f', '/t']);
    } else {
      process.kill(-serverProcess.pid, 'SIGTERM');
    }
    
    serverRunning = false;
    updateTrayAndMenu();
    
    // Load offline page if main window exists
    if (mainWindow) {
      mainWindow.loadFile(path.join(__dirname, 'offline.html'));
    }
  } catch (error) {
    console.error('Failed to stop server:', error);
    dialog.showErrorBox('Server Error', `Failed to stop server: ${error.message}`);
  }
}

// Check if server is running
function checkServerStatus() {
  fetch(`http://localhost:${serverPort}/api/status`, { timeout: 2000 })
    .then(response => {
      if (response.ok) {
        serverRunning = true;
      } else {
        serverRunning = false;
      }
    })
    .catch(() => {
      serverRunning = false;
    })
    .finally(() => {
      updateTrayAndMenu();
    });
}

// Update tray and menu to reflect server status
function updateTrayAndMenu() {
  if (tray) {
    const contextMenu = Menu.buildFromTemplate([
      {
        label: 'Open MultiAgentConsole',
        click: () => {
          if (mainWindow) {
            mainWindow.show();
          } else {
            createWindow();
          }
        }
      },
      {
        label: serverRunning ? 'Stop Server' : 'Start Server',
        click: () => serverRunning ? stopServer() : startServer()
      },
      { type: 'separator' },
      {
        label: 'Settings',
        click: () => openSettings()
      },
      { type: 'separator' },
      {
        label: 'Quit',
        click: () => {
          app.isQuitting = true;
          app.quit();
        }
      }
    ]);
    tray.setContextMenu(contextMenu);
  }

  createMenu();
}

// Open settings window
function openSettings() {
  const settingsWindow = new BrowserWindow({
    width: 600,
    height: 700,
    parent: mainWindow,
    modal: true,
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  settingsWindow.loadFile(path.join(__dirname, 'settings.html'));
  settingsWindow.once('ready-to-show', () => {
    settingsWindow.show();
  });
}

// Show about dialog
function showAboutDialog() {
  dialog.showMessageBox(mainWindow, {
    title: 'About MultiAgentConsole',
    message: 'MultiAgentConsole',
    detail: `Version: ${app.getVersion()}\nAuthor: Sai Sunkara\nLicense: MIT\n\nA powerful multi-agent console for AI interactions.`,
    buttons: ['OK'],
    icon: path.join(__dirname, 'icons', process.platform === 'win32' ? 'icon.ico' : 'icon.png')
  });
}

// Setup cloud sync
function setupCloudSync() {
  if (store.get('syncEnabled')) {
    const intervalMinutes = store.get('syncInterval');
    
    // Clear existing interval if any
    if (syncInterval) {
      clearInterval(syncInterval);
    }
    
    // Set up new interval
    syncInterval = setInterval(() => {
      syncWithCloud();
    }, intervalMinutes * 60 * 1000);
    
    // Initial sync
    syncWithCloud();
  } else if (syncInterval) {
    clearInterval(syncInterval);
    syncInterval = null;
  }
}

// Sync with cloud
function syncWithCloud() {
  console.log('Syncing with cloud...');
  // TODO: Implement actual cloud sync
}

// App ready event
app.whenReady().then(() => {
  createWindow();
  createTray();
  
  // Start server if enabled
  if (store.get('startServerOnLaunch')) {
    startServer();
  }
  
  // Setup cloud sync
  setupCloudSync();
  
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// App will quit event
app.on('will-quit', () => {
  // Stop server before quitting
  if (serverRunning) {
    stopServer();
  }
  
  // Clear sync interval
  if (syncInterval) {
    clearInterval(syncInterval);
  }
});

// IPC handlers for settings
ipcMain.handle('get-settings', () => {
  return store.store;
});

ipcMain.handle('save-settings', (event, settings) => {
  store.store = settings;
  
  // Update server port if changed
  if (settings.serverPort !== serverPort) {
    serverPort = settings.serverPort;
    if (serverRunning) {
      dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: 'Server Restart Required',
        message: 'The server port has been changed. The server needs to be restarted for this change to take effect.',
        buttons: ['Restart Now', 'Later'],
      }).then(result => {
        if (result.response === 0) {
          stopServer();
          setTimeout(() => startServer(), 1000);
        }
      });
    }
  }
  
  // Update sync settings if changed
  setupCloudSync();
  
  return true;
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
  dialog.showErrorBox('Error', `An unexpected error occurred: ${error.message}`);
});
