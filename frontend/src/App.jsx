import React, { useState, useEffect, useRef, useMemo } from 'react';
import './index.css';

// --- Icons ---
const FileIcon = () => (
    <svg width="14" height="16" viewBox="0 0 14 16" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M0 1C0 0.447715 0.447715 0 1 0H9L14 5V15C14 15.5523 13.5523 16 13 16H1C0.447715 16 0 15.5523 0 15V1Z" fill="#A1A1A6" />
        <path d="M9 0L14 5H9V0Z" fill="#D1D1D6" />
    </svg>
);

const FolderIcon = () => (
    <svg width="16" height="13" viewBox="0 0 16 13" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M0 2C0 1.44772 0.447715 1 1 1H6L8 3H15C15.5523 3 16 3.44772 16 4V12C16 12.5523 15.5523 13 15 13H1C0.447715 13 0 12.5523 0 12V2Z" fill="#EBC347" />
    </svg>
);

const NewTestIcon = () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
        <polyline points="14 2 14 8 20 8"></polyline>
        <line x1="12" y1="18" x2="12" y2="12"></line>
        <line x1="9" y1="15" x2="15" y2="15"></line>
    </svg>
);

const NewFolderIcon = () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
        <line x1="12" y1="17" x2="12" y2="11"></line>
        <line x1="9" y1="14" x2="15" y2="14"></line>
    </svg>
);

const EditIcon = () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
    </svg>
);

const DeleteIcon = () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="3 6 5 6 21 6" />
        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
        <line x1="10" y1="11" x2="10" y2="17" />
        <line x1="14" y1="11" x2="14" y2="17" />
    </svg>
);

const CopyIcon = () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
    </svg>
);

const PlayIcon = () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="5 3 19 12 5 21 5 3"></polygon>
    </svg>
);

// Default base URL logic: If on Vercel, point to Render. If local, point to local port 8000.
const DEFAULT_API_URL = window.location.hostname.includes('vercel.app')
    ? 'https://rattl-runner-lr6p.onrender.com'
    : `${window.location.protocol}//${window.location.hostname === 'localhost' ? 'localhost' : window.location.hostname}:8000`;

function App() {
    const resizingTargetRef = useRef(null);

    useEffect(() => {
        const handleMouseMove = (e) => {
            if (!resizingTargetRef.current) return;
            e.preventDefault();

            if (resizingTargetRef.current === 'sidebar') {
                let w = e.clientX;
                if (w < 150) w = 150;
                if (w > 800) w = 800;
                document.documentElement.style.setProperty('--sidebar-width', `${w}px`);
            } else if (resizingTargetRef.current === 'terminal') {
                let h = window.innerHeight - e.clientY;
                if (h < 50) h = 50;
                if (h > 600) h = 600;
                document.documentElement.style.setProperty('--terminal-height', `${h}px`);
            } else if (resizingTargetRef.current === 'device') {
                let w = window.innerWidth - e.clientX;
                if (w < 300) w = 300;
                if (w > 900) w = 900;
                document.documentElement.style.setProperty('--device-pane-width', `${w}px`);
            }
        };

        const handleMouseUp = () => {
            if (resizingTargetRef.current) {
                resizingTargetRef.current = null;
                document.body.style.cursor = 'default';
                document.querySelectorAll('.sidebar-resizer, .terminal-resizer, .device-resizer').forEach(el => el.classList.remove('active'));
            }
        };

        window.addEventListener('mousemove', handleMouseMove);
        window.addEventListener('mouseup', handleMouseUp);
        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
        };
    }, []);

    const startSidebarResize = (e) => {
        e.preventDefault();
        resizingTargetRef.current = 'sidebar';
        document.body.style.cursor = 'col-resize';
        e.target.classList.add('active');
    };

    const startTerminalResize = (e) => {
        e.preventDefault();
        resizingTargetRef.current = 'terminal';
        document.body.style.cursor = 'row-resize';
        e.target.classList.add('active');
    };

    const startDeviceResize = (e) => {
        e.preventDefault();
        resizingTargetRef.current = 'device';
        document.body.style.cursor = 'col-resize';
        e.target.classList.add('active');
    };

    // --- State ---
    const [files, setFiles] = useState([]);
    const [currentFile, setCurrentFile] = useState(null);
    const [editorContent, setEditorContent] = useState('');
    const [logs, setLogs] = useState([{ type: 'info', text: 'Ratl Studio Terminal Ready' }]);
    const [deviceConnected, setDeviceConnected] = useState(false);
    const [isRunning, setIsRunning] = useState(false);
    const [refreshKey, setRefreshKey] = useState(0);
    const [packages, setPackages] = useState([]);
    const [expandedFolders, setExpandedFolders] = useState(new Set());
    const [lineStatuses, setLineStatuses] = useState({}); // line# -> 'pass' | 'fail' | 'running'
    const [hierarchy, setHierarchy] = useState(null);
    const [elements, setElements] = useState([]);
    const [selectedElement, setSelectedElement] = useState(null);
    const [deviceInfo, setDeviceInfo] = useState({ width: 1080, height: 2280, model: '' });
    const [showInspector, setShowInspector] = useState(true);
    const [popupPosition, setPopupPosition] = useState(null); // { x, y } for floating popup
    const [selectedLocatorIndex, setSelectedLocatorIndex] = useState(0); // Which locator (ID, Text, etc) is active
    const [isFetchingHierarchy, setIsFetchingHierarchy] = useState(false);
    const [hierarchyRefreshKey, setHierarchyRefreshKey] = useState(0);
    const [interactMode, setInteractMode] = useState(false); // New: Auto-Insert & Run mode
    const [errorLine, setErrorLine] = useState(null); // Track YAML error line number
    const [terminalInput, setTerminalInput] = useState('');
    const [activeTerminalTab, setActiveTerminalTab] = useState('OUTPUT');
    const [isGeneratingAI, setIsGeneratingAI] = useState(false);
    const [terminalCwd, setTerminalCwd] = useState('backend');
    const [apiBaseUrl, setApiBaseUrl] = useState(localStorage.getItem('ratl_api_url') || import.meta.env.VITE_API_URL || DEFAULT_API_URL);
    const [isEditingUrl, setIsEditingUrl] = useState(false);
    const [showSettings, setShowSettings] = useState(false);
    const [apiKey, setApiKey] = useState(localStorage.getItem('openai_api_key') || '');
    const [aiPrompt, setAiPrompt] = useState('');
    const [agentIntelligence, setAgentIntelligence] = useState(null);
    const [activeTab, setActiveTab] = useState('inspector');
    const [selectedRunId, setSelectedRunId] = useState(null);
    const [showReportModal, setShowReportModal] = useState(false);
    const [currentReport, setCurrentReport] = useState(null);
    const [showPackageDropdown, setShowPackageDropdown] = useState(false);

    const fetchIntelligence = async () => {
        try {
            const res = await fetch(`${apiBaseUrl}/api/intelligence/stats`);
            const data = await res.json();
            setAgentIntelligence(data);
        } catch (e) { console.error(e); }
    };

    // Custom Modal States
    const [fileToDelete, setFileToDelete] = useState(null);
    const [fileToRename, setFileToRename] = useState(null);
    const [renameValue, setRenameValue] = useState('');

    // New Folder State
    const [showNewFolderModal, setShowNewFolderModal] = useState(false);
    const [newFolderName, setNewFolderName] = useState('');

    const [urlInput, setUrlInput] = useState(apiBaseUrl);
    const terminalInputRef = useRef(null);

    // Modal State
    const [showModal, setShowModal] = useState(false);
    const [modalData, setModalData] = useState({
        name: '',
        appId: 'com.hamleys_webapp',
        type: 'Mobile Test',
        tags: ''
    });

    const terminalEndRef = useRef(null);
    const lineNumbersRef = useRef(null);

    // For Line Numbers
    const countLines = (text) => text.split('\n').length;
    const [lineCount, setLineCount] = useState(1);

    // --- Sorting Helper ---
    const getSortedFiles = (rawFiles) => {
        if (!rawFiles || !Array.isArray(rawFiles)) return [];
        try {
            const root = { children: {} };

            rawFiles.forEach(f => {
                const parts = f.path.split('/');
                let current = root;
                parts.forEach((part, i) => {
                    if (!current.children[part]) {
                        current.children[part] = {
                            name: part,
                            path: parts.slice(0, i + 1).join('/'),
                            type: 'folder', // Default to folder
                            children: {}
                        };
                    }
                    // If we are at the last part, update type if it's a file from rawFiles
                    if (i === parts.length - 1) {
                        if (f.path === current.children[part].path) {
                            current.children[part].raw = f;
                            if (part.endsWith('.yaml') || part.endsWith('.yml')) {
                                current.children[part].type = 'file';
                            }
                        }
                    }
                    current = current.children[part];
                });
            });

            const result = [];
            const process = (node) => {
                if (!node || !node.children) return;

                const children = Object.values(node.children);
                children.sort((a, b) => {
                    const aIsFolder = a.type === 'folder';
                    const bIsFolder = b.type === 'folder';
                    if (aIsFolder && !bIsFolder) return -1;
                    if (!aIsFolder && bIsFolder) return 1;
                    return a.name.localeCompare(b.name);
                });

                children.forEach(child => {
                    // Add the item itself to the flat list
                    if (child.type === 'file' && child.raw) {
                        result.push(child.raw);
                    } else if (child.type === 'folder') {
                        result.push({ name: child.name, path: child.path, type: 'folder' });
                        // Recursively process children
                        process(child);
                    }
                });
            };
            process(root);
            return result;
        } catch (e) {
            console.error("Sorting error:", e);
            return rawFiles || [];
        }
    };

    const sortedFiles = useMemo(() => getSortedFiles(files), [files]);

    // --- Effects ---
    useEffect(() => {
        fetchFiles();
        checkDevice();
        fetchPackages();
        fetchDeviceInfo();

        // 1. Show startup logs in terminal on mount to match ./start.sh experience
        const startupLogs = [
            { text: `kalyanibadgujar@rattl-runner rattl-runner % ./start.sh`, delay: 100 },
            { text: '🚀 Starting Ratl Runner...', delay: 200 },
            { text: '🐍 Starting Backend (Port 8000)...', delay: 500 },
            { text: 'INFO:     Started server process [92237]', delay: 800 },
            { text: 'INFO:     Application startup complete.', delay: 1200 },
            { text: '⚛️ Starting Frontend...', delay: 1500 },
            { text: '✅ Both services reported running.', delay: 1800 },
            { text: 'Press Ctrl+C to stop.', delay: 2000 }
        ];

        startupLogs.forEach(log => {
            setTimeout(() => addLog('info-cmd', log.text), log.delay);
        });

        // 2. Real ADB Check on start
        setTimeout(() => {
            addLog('info', '🔍 Searching for USB devices...');
            executeCommand('adb devices');
        }, 2200);
    }, []);

    // Polling for device status - Restarts when URL changes
    useEffect(() => {
        // Run immediately on URL change or mount
        checkDevice();
        const statusInterval = setInterval(checkDevice, 2000);
        return () => clearInterval(statusInterval);
    }, [apiBaseUrl]);

    // 2. Automaticaly "Start" when device is connected
    useEffect(() => {
        if (deviceConnected && logs.length > 5) {
            addLog('success', '🔌 Device connected! Initializing session...');
            executeCommand('adb shell getprop ro.product.model');
        }
    }, [deviceConnected]);

    // Sequential polling handler: Only fetch next frame after current one is loaded
    const onScreenLoad = () => {
        if (deviceConnected) {
            // Sequential polling: trigger one update after the other
            // but with a small throttle cap if needed
            setRefreshKey(prev => prev + 1);
        }
    };

    // Only fetch hierarchy if inspector is ON and device is connected
    useEffect(() => {
        if (deviceConnected && showInspector && !isFetchingHierarchy) {
            fetchHierarchy();
        }
    }, [hierarchyRefreshKey, deviceConnected, showInspector]);

    useEffect(() => {
        setSelectedLocatorIndex(0);
    }, [selectedElement]);

    // Update hierarchy refresh key at a slower pace
    useEffect(() => {
        if (showInspector && deviceConnected) {
            const interval = setInterval(() => {
                setHierarchyRefreshKey(prev => prev + 1);
            }, 2000); // Fetch hierarchy every 2 seconds
            return () => clearInterval(interval);
        }
    }, [showInspector, deviceConnected]);

    useEffect(() => {
        setLineCount(countLines(editorContent));
    }, [editorContent]);

    useEffect(() => {
        const handleKeyDown = (e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault();
                setShowModal(true);
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, []);

    useEffect(() => {
        if (terminalEndRef.current) {
            const terminalContainer = terminalEndRef.current.parentElement;
            const isNearBottom = terminalContainer.scrollHeight - terminalContainer.scrollTop - terminalContainer.clientHeight < 100;
            if (isNearBottom) {
                terminalContainer.scrollTop = terminalContainer.scrollHeight;
            }
        }
    }, [logs]);

    // --- API Calls ---
    const fetchFiles = async () => {
        try {
            const res = await fetch(`${apiBaseUrl}/files`);
            const data = await res.json();
            setFiles(data.files || []);
        } catch (e) {
            console.error(e);
        }
    };

    const fetchDeviceInfo = async () => {
        try {
            const res = await fetch(`${apiBaseUrl}/device_info`);
            const data = await res.json();
            if (data.size) {
                const match = data.size.match(/(\d+)x(\d+)/);
                if (match) {
                    setDeviceInfo({
                        width: parseInt(match[1]),
                        height: parseInt(match[2]),
                        model: data.model || 'Unknown Device'
                    });
                }
            }
        } catch (e) {
            console.error('Fetch device info error:', e);
        }
    };

    const fetchHierarchy = async () => {
        if (!showInspector || isFetchingHierarchy) return;
        setIsFetchingHierarchy(true);
        try {
            const res = await fetch(`${apiBaseUrl}/hierarchy`);
            const data = await res.json();
            if (data.output) {
                const parsed = JSON.parse(data.output);
                setHierarchy(parsed);
                const flattened = [];
                flattenHierarchy(parsed, flattened);
                setElements(flattened);
            }
        } catch (e) {
            console.error('Fetch hierarchy error:', e);
        } finally {
            setIsFetchingHierarchy(false);
        }
    };

    const flattenHierarchy = (node, acc) => {
        if (!node) return;
        if (node.bounds) {
            acc.push(node);
        }
        if (node.children) {
            node.children.forEach(child => flattenHierarchy(child, acc));
        }
    };

    const checkDevice = async () => {
        try {
            const res = await fetch(`${apiBaseUrl}/devices`);
            const data = await res.json();

            const output = data.output || '';
            const connected = output.split('\n').some(line => {
                const parts = line.trim().split(/\s+/);
                return parts.length >= 2 && parts[1] === 'device';
            });

            if (connected && !deviceConnected) {
                // Device connected - silently update state
                fetchDeviceInfo();
                fetchPackages();
            } else if (!connected && deviceConnected) {
                addLog('error', '⚠️ Device disconnected. Waiting for connection...');
            }

            setDeviceConnected(connected);
        } catch (e) {
            if (deviceConnected) addLog('error', '📡 Server connection lost.');
            setDeviceConnected(false);
        }
    };

    const fetchPackages = async () => {
        try {
            const res = await fetch(`${apiBaseUrl}/packages`);
            if (!res.ok) throw new Error('Failed to fetch packages');
            const data = await res.json();
            const pkgs = data.packages || [];
            setPackages(pkgs);
        } catch (e) {
            console.error('Fetch packages error:', e);
        }
    };

    const loadFile = async (file) => {
        try {
            const res = await fetch(`${apiBaseUrl}/file?path=${encodeURIComponent(file.path)}`);
            const data = await res.json();
            setCurrentFile(file);
            setEditorContent(data.content);
            setLineStatuses({});
            addLog('info', `Loaded ${file.name}`);
        } catch (e) {
            alert('Error loading file');
        }
    };

    const saveFile = async () => {
        if (!currentFile) return;
        try {
            await fetch(`${apiBaseUrl}/file`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: currentFile.path, content: editorContent })
            });
            addLog('success', `Saved ${currentFile.name}`);
        } catch (e) {
            addLog('error', `Failed to save ${currentFile.name}`);
        }
    };

    const addLog = (type, text) => {
        const time = new Date().toLocaleTimeString([], { hour12: false });
        setLogs(prev => [...prev, { type, text, time }]);
    };

    const updateBaseUrl = (newUrl) => {
        let formatted = newUrl.trim();

        // 1. Smart Extraction: If they pasted a command like 'lt --port 8000', find the URL inside it
        const urlMatch = formatted.match(/https?:\/\/[a-z0-9-.]+(?:\.[a-z]{2,})[^\s]*/i);
        if (urlMatch) {
            formatted = urlMatch[0];
        }

        // 2. Validation: If it still looks like a command, reject it
        if (formatted.includes('ssh ') || formatted.includes('lt ') || formatted.includes('npm ')) {
            addLog('error', '❌ Invalid URL: You pasted the COMMAND. Please run the script on your Mac and paste the LINK it gives you.');
            alert('Wait! You pasted the command, not the URL. \n\n1. Run the bridge script (copy the command from the left).\n2. Copy the https:// link it gives you.\n3. Paste THAT link here.');
            return;
        }

        if (formatted && !formatted.startsWith('http')) formatted = 'http://' + formatted;
        if (formatted.endsWith('/')) formatted = formatted.slice(0, -1);

        setApiBaseUrl(formatted);
        localStorage.setItem('ratl_api_url', formatted);
        setIsEditingUrl(false);
        addLog('info', `📡 Switching backend to: ${formatted}`);

        // Reset connection check
        setDeviceConnected(false);
    };

    const focusTerminal = () => {
        if (terminalInputRef.current) {
            terminalInputRef.current.focus();
        }
    };

    const clearLogs = () => {
        setLogs([{ type: 'info', text: 'Terminal Cleared', time: new Date().toLocaleTimeString([], { hour12: false }) }]);
    };

    // Helper to format path (tildify)
    const formatTerminalPath = (path) => {
        if (!path) return 'loading...';
        // Simple tildify logic if we knew the home dir, but for now let's just show the path
        // or a shortened version of it.
        // If it's the project root, we can just show the folder name if it's too long
        return path;
    };

    const fetchTerminalInfo = async () => {
        try {
            const res = await fetch(`${apiBaseUrl}/terminal`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: '' })
            });
            const data = await res.json();
            if (data.cwd) setTerminalCwd(data.cwd);
        } catch (e) {
            console.error("Failed to fetch terminal info", e);
        }
    };

    useEffect(() => {
        if (activeTerminalTab === 'TERMINAL') {
            fetchTerminalInfo();
            setTimeout(focusTerminal, 50);
        }
    }, [activeTerminalTab]);

    useEffect(() => {
        if (activeTab === 'intelligence') {
            fetchIntelligence();
            const interval = setInterval(fetchIntelligence, 5000);
            return () => clearInterval(interval);
        }
    }, [activeTab]);

    const executeCommand = async (cmd) => {
        if (!cmd) return;

        if (cmd.toLowerCase() === 'clear') {
            setLogs(prev => prev.filter(l => l.type !== 'info-cmd' && !l.text.startsWith('>')));
            return;
        }

        addLog('info-cmd', `> ${cmd}`);

        try {
            const res = await fetch(`${apiBaseUrl}/terminal`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: cmd })
            });

            const contentType = res.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const data = await res.json();
                if (data.output) addLog('info-cmd', data.output);
                if (data.cwd) setTerminalCwd(data.cwd);
                return;
            }

            if (!res.body) throw new Error('No response body');
            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n\n');
                buffer = lines.pop() || '';

                for (const rawLine of lines) {
                    if (!rawLine.startsWith('data: ')) continue;
                    const text = rawLine.replace('data: ', '').trim();

                    if (text.startsWith('[DONE] EXIT_CODE:')) {
                        const code = text.split(': ')[1];
                        if (code !== '0') addLog('error', `Command exited with code ${code}`);
                    } else if (text.startsWith('[CWD]')) {
                        const cwdValue = text.replace('[CWD]', '').trim();
                        setTerminalCwd(cwdValue);
                    } else if (text.startsWith('[ERROR]')) {
                        addLog('error', text.replace('[ERROR]', ''));
                    } else if (text) {
                        addLog('info-cmd', text);
                    }
                }
            }
        } catch (err) {
            console.error('Terminal Execution Error:', err);
            addLog('error', `Terminal Error: ${err.message}. Make sure the backend at ${apiBaseUrl} is online.`);
        }
    };

    const handleTerminalSubmit = async (e) => {
        e.preventDefault();
        const cmd = terminalInput.trim();
        if (!cmd) return;
        setTerminalInput('');
        await executeCommand(cmd);
    };

    // Helper function to get available locators for an element
    const getAvailableLocators = (element) => {
        if (!element || element.isPoint) return [];
        const locators = [];
        const isInput = element.className?.includes('EditText');

        // Capture locators in temporary storage first
        const textLocs = [];
        const idLocs = [];
        const accLocs = [];

        // 1. Text Content
        const textValue = (element.text || element.attributes?.text || '').trim();
        if (textValue) {
            textLocs.push({
                type: 'Text',
                label: 'Visible Text',
                value: textValue,
                reliability: isInput ? 'low' : 'high',
                selector: { text: textValue },
                syntax: `"${textValue}"`
            });
        }

        // 1b. Child Text Content
        let childText = null;

        // Strategy A: Explicit Children Hierarchy (DFS)
        if (element.children && element.children.length > 0) {
            const findTextInChildren = (node) => {
                const t = (node.text || node.attributes?.text || '').trim();
                if (t) return t;
                if (node.children) {
                    for (const child of node.children) {
                        const found = findTextInChildren(child);
                        if (found) return found;
                    }
                }
                return null;
            };
            childText = findTextInChildren(element);
        }
        // Strategy B: Spatial Children (Flat List Fallback)
        else if (elements && elements.length > 0 && element.bounds) {
            const { left: pl, top: pt, right: pr, bottom: pb } = element.bounds;
            // Find elements strictly contained within parent
            const contained = elements.filter(el => {
                if (el === element || !el.bounds) return false;
                const { left: cl, top: ct, right: cr, bottom: cb } = el.bounds;
                return cl >= pl && cr <= pr && ct >= pt && cb <= pb;
            });

            // Sort by area (smallest first - deeper in hierarchy) to get most specific text
            contained.sort((a, b) => {
                const areaA = (a.bounds.right - a.bounds.left) * (a.bounds.bottom - a.bounds.top);
                const areaB = (b.bounds.right - b.bounds.left) * (b.bounds.bottom - b.bounds.top);
                return areaA - areaB;
            });

            const textNode = contained.find(el => (el.text || el.attributes?.text || '').trim());
            if (textNode) {
                childText = (textNode.text || textNode.attributes?.text || '').trim();
            }
        }

        if (childText) {
            textLocs.push({
                type: 'Text',
                label: 'Child Text',
                value: childText,
                reliability: 'medium',
                selector: { text: childText },
                syntax: `"${childText}"`
            });
        }

        // 2. Resource ID
        const idValue = element.resourceId || element['resource-id'] || element.attributes?.['resource-id'];
        if (idValue) {
            idLocs.push({
                type: 'ID',
                label: 'Resource ID',
                value: idValue,
                reliability: 'high',
                selector: { id: idValue },
                syntax: `id: "${idValue}"`
            });
        }

        // 3. Accessibility / Content Description
        const descValue = element.contentDescription || element['content-desc'] || element.attributes?.['content-desc'] || element.hint;
        if (descValue) {
            accLocs.push({
                type: 'Accessibility',
                label: 'Accessibility ID',
                value: descValue,
                reliability: 'high',
                selector: { accessibilityId: descValue },
                syntax: `accessibilityId: "${descValue}"`
            });
        }

        // PRIORITIZATION LOGIC
        if (isInput) {
            // For inputs: ID > Accessibility > Text (Value is mutable)
            locators.push(...idLocs);
            locators.push(...accLocs);
            locators.push(...textLocs);
        } else {
            // For static elements: Text > ID > Accessibility
            locators.push(...textLocs);
            locators.push(...idLocs);
            locators.push(...accLocs);
        }

        // 4. Point (Fallback that is always available)
        if (element.bounds) {
            const { left, top, right, bottom } = element.bounds;
            const centerX = ((left + right) / 2 / deviceInfo.width) * 100;
            const centerY = ((top + bottom) / 2 / deviceInfo.height) * 100;
            locators.push({
                type: 'Point',
                label: 'Coordinates',
                value: `${Math.round(centerX)}%, ${Math.round(centerY)}%`,
                reliability: 'low',
                selector: { point: `${Math.round(centerX)}%,${Math.round(centerY)}%` },
                syntax: `point: "${Math.round(centerX)}%,${Math.round(centerY)}%"`
            });
        }

        return locators;

        // 5. Class Name (Last Resort)
        const classValue = element.className || element.class || element.attributes?.class;
        if (classValue) {
            locators.push({
                type: 'Class',
                label: 'Class Name',
                value: classValue,
                reliability: 'low',
                selector: { class: classValue },
                syntax: `class: "${classValue}"`
            });
        }

        return locators;
    };

    const formatYaml = (action, params) => {
        const indent = '    ';

        // YAML formatting for test automation
        // Standard shorthand for text/id if it's the only param
        if (params.text && Object.keys(params).length === 1) {
            const v = params.text;
            const escapedV = (v.includes(':') || v.includes('"')) ? `"${v.replace(/"/g, '\\"')}"` : `"${v}"`;
            return `- ${action}: ${escapedV}`;
        }
        if (params.id && Object.keys(params).length === 1) {
            return `- ${action}:\n    id: "${params.id}"`;
        }

        let yaml = `- ${action}:\n`;

        const formatValue = (val, level = 1) => {
            const currIndent = indent.repeat(level);
            if (typeof val === 'string') {
                if (val.includes(':') || val.includes('"')) return `${currIndent}"${val.replace(/"/g, '\\"')}"\n`;
                return `${currIndent}${val}\n`;
            }
            if (typeof val === 'object' && val !== null) {
                let s = '';
                for (const [k, v] of Object.entries(val)) {
                    if (typeof v === 'object') {
                        s += `${currIndent}${k}:\n${formatValue(v, level + 1)}`;
                    } else {
                        const escapedV = typeof v === 'string' && (v.includes(':') || v.includes('"')) ? `"${v.replace(/"/g, '\\"')}"` : v;
                        s += `${currIndent}${k}: ${escapedV}\n`;
                    }
                }
                return s;
            }
            return `${currIndent}${val}\n`;
        };

        for (const [k, v] of Object.entries(params)) {
            if (typeof v === 'object') {
                yaml += `${indent}${k}:\n${formatValue(v, 2)}`;
            } else {
                const escapedV = typeof v === 'string' && (v.includes(':') || v.includes('"')) ? `"${v.replace(/"/g, '\\"')}"` : v;
                yaml += `${indent}${k}: ${escapedV}\n`;
            }
        }
        return yaml;
    };

    // Generate automation command with selected locator
    const generateCommand = (locator, commandType) => {
        const commands = {
            tap: `- tapOn:\n    ${locator.syntax}`,
            assert: `- assertVisible:\n    ${locator.syntax}`,
            input: `- tapOn:\n    ${locator.syntax}\n- inputText: "your text here"`,
            swipe: `- swipe:\n    start: ${locator.syntax}\n    direction: UP`
        };

        return commands[commandType] || commands.tap;
    };

    // Copy to clipboard
    const copyToClipboard = (text) => {
        navigator.clipboard.writeText(text).then(() => {
            addLog('success', 'Copied to clipboard');
        }).catch(() => {
            addLog('error', 'Failed to copy to clipboard');
        });
    };

    const getStepLines = (content) => {
        const lines = content.split('\n');
        const stepLines = [];
        let inSteps = false;
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            if (line === '---') {
                inSteps = true;
                continue;
            }
            if (inSteps && line.startsWith('- ')) {
                stepLines.push(i + 1);
            }
        }
        return stepLines;
    };

    const abortControllerRef = useRef(null);

    const stopTest = () => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }
        addLog('error', 'Test Stopped by User');
        setIsRunning(false);
    };

    const runStep = async (step) => {
        try {
            const res = await fetch(`${apiBaseUrl}/run-step`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ step })
            });
            const data = await res.json();
            if (data.status === 'success') {
                addLog('success', `Executed: ${data.log}`);
                // Sequential refresh
                setTimeout(() => {
                    setRefreshKey(Date.now());
                    setHierarchyRefreshKey(prev => prev + 1);
                }, 800);
            } else {
                addLog('error', `Step Failed: ${data.error || 'Unknown error'}`);
            }
        } catch (e) {
            addLog('error', `Execution error: ${e.message}`);
        }
    };

    const runTest = async () => {
        if (!currentFile) return;

        // Auto-save before running
        await saveFile();


        // Validate YAML before running
        try {
            const validateRes = await fetch(`${apiBaseUrl}/validate-yaml`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ yaml_content: editorContent })
            });

            if (!validateRes.ok) {
                throw new Error(`Validation request failed: ${validateRes.status}`);
            }

            const validation = await validateRes.json();


            if (!validation.valid) {
                // Use line number from response (or fallback to regex parsing)
                const errorMsg = validation.error || 'Unknown validation error';
                const errorLineNum = validation.line || (() => {
                    if (!errorMsg) return null;
                    const lineMatch = errorMsg.match(/line (\d+)/i);
                    return lineMatch ? parseInt(lineMatch[1], 10) : null;
                })();

                setErrorLine(errorLineNum);
                addLog('error', `❌ YAML Validation Failed: ${errorMsg}`);
                addLog('info', `💡 Tip: Check for missing dashes (-), colons (:), or improper indentation`);

                if (errorLineNum) {
                    addLog('info', `📍 Error is on line ${errorLineNum} - check the red highlight in the editor`);
                }
                return;
            }

            // Clear error line if validation passes
            setErrorLine(null);
            // Validation passed - silently proceed
        } catch (e) {
            addLog('error', `Validation error: ${e.message}`);
            setErrorLine(null);
            return;
        }



        setIsRunning(true);
        setLineStatuses({});
        addLog('info', `Running ${currentFile.name}...`);

        const stepLines = getStepLines(editorContent);
        abortControllerRef.current = new AbortController();

        try {
            const response = await fetch(`${apiBaseUrl}/run`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    yaml_content: editorContent,
                    apiKey: apiKey, // Pass the stored key
                    filename: currentFile.name // Pass the filename
                }),
                signal: abortControllerRef.current.signal
            });

            // Check for HTTP errors (like YAML validation errors from backend)
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to run test');
            }

            if (!response.body) throw new Error('No response body');
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n\n');
                buffer = lines.pop() || '';

                for (const rawLine of lines) {
                    if (!rawLine.startsWith('data: ')) continue;
                    const text = rawLine.replace('data: ', '').trim();

                    if (text.startsWith('[DONE] EXIT_CODE:')) {
                        const code = text.split(': ')[1];
                        if (code === '0') addLog('success', 'Test Completed Successfully');
                        else addLog('error', `Test Failed (Exit Code: ${code})`);
                        continue;
                    }

                    if (text.startsWith('[ERROR]')) {
                        addLog('error', text.replace('[ERROR]', ''));
                        continue;
                    }

                    // Parse test progress: [1/5] Step name (completed/failed/running)
                    // Improved regex to handle messages with parentheses like "Launch (cleared state)"
                    const match = text.match(/\[(\d+)\/(\d+)\]\s+(.*)\s+\((running|completed|failed)\)$/);
                    if (match) {
                        const stepIdx = parseInt(match[1], 10) - 1;
                        const status = match[4].toLowerCase().trim(); // Group 4 is now the status
                        const stepDetail = match[3];

                        if (status !== 'running' || stepDetail !== 'step') {
                            // Only log if it's not the initial "step (running)" generic message
                            addLog(status === 'failed' ? 'error' : 'info', text);
                        }

                        if (stepLines[stepIdx]) {
                            const lineNum = stepLines[stepIdx];
                            setLineStatuses(prev => ({
                                ...prev,
                                [lineNum]: status === 'completed' ? 'pass' : (status === 'failed' ? 'fail' : 'running')
                            }));
                        }
                    } else {
                        addLog('info', text);
                    }
                }
            }
        } catch (e) {
            if (e.name === 'AbortError') {
                console.log('Fetch aborted');
            } else {
                addLog('error', `Error: ${e.message}`);
            }
        } finally {
            setIsRunning(false);
            abortControllerRef.current = null;
        }
    };

    const createTestFlow = async () => {
        const { name, appId } = modalData;
        if (!name.trim()) {
            addLog('error', 'Test name is required');
            return;
        }
        if (!appId) {
            addLog('error', 'App Id is required');
            return;
        }

        // Sanitize name: remove leading/trailing slashes/dots and handle extension
        let baseName = name.trim().replace(/^[./\\]+/, "");
        if (!baseName) {
            addLog('error', 'Invalid test name');
            return;
        }

        if (baseName.endsWith('.yaml') || baseName.endsWith('.yml')) {
            // keep it
        } else {
            baseName += '.yaml';
        }

        const initialContent = `appId: ${appId}
---
- launchApp:
    clearState: true`;

        try {
            setIsRunning(true);
            addLog('info', `Creating test ${baseName}...`);

            const res = await fetch(`${apiBaseUrl}/files`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: baseName, type: 'file' })
            });

            if (!res.ok) {
                let msg = 'Failed to create file';
                try {
                    const errorData = await res.json();
                    msg = errorData.detail || msg;
                } catch (e) {
                    msg = `Server error: ${res.status} ${res.statusText} `;
                }
                throw new Error(msg);
            }

            const saveRes = await fetch(`${apiBaseUrl}/file`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: baseName, content: initialContent })
            });

            if (!saveRes.ok) {
                let msg = 'Failed to save content';
                try {
                    const errorData = await saveRes.json();
                    msg = errorData.detail || msg;
                } catch (e) {
                    msg = `Server error: ${saveRes.status} ${saveRes.statusText} `;
                }
                throw new Error(msg);
            }

            setShowModal(false);
            setModalData({ ...modalData, name: '' });
            addLog('success', `Created test ${baseName} `);

            if (baseName.includes('/')) {
                const parts = baseName.split('/').slice(0, -1);
                setExpandedFolders(prev => {
                    const next = new Set(prev);
                    let accum = '';
                    parts.forEach(p => { accum = accum ? accum + '/' + p : p; next.add(accum); });
                    return next;
                });
            }

            fetchFiles();
        } catch (e) {
            console.error(e);
            addLog('error', `Error creating test: ${e.message} `);
        } finally {
            setIsRunning(false);
        }
    };

    const runFolder = async (e, folderPath) => {
        e.stopPropagation();
        if (isRunning) return;

        setIsRunning(true);
        setLogs([{ type: 'info', text: `🚀 Starting folder run: ${folderPath}` }]);

        try {
            const response = await fetch(`${apiBaseUrl}/run-folder`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ folder_path: folderPath })
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n\n');

                lines.forEach(line => {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        if (data.includes('[DONE]')) {
                            // Keep running state managed by outer finally, but good to know
                        } else {
                            addLog('info', data);
                        }
                    }
                });
            }
        } catch (error) {
            addLog('error', `Run failed: ${error.message}`);
        } finally {
            setIsRunning(false);
        }
    };

    const duplicateItem = async (e, file) => {
        e.stopPropagation();
        const newName = prompt('Enter name for copy:', file.path.replace(/(\.ya?ml)$/, '_copy$1'));
        if (!newName) return;

        try {
            // Read content
            const readRes = await fetch(`${apiBaseUrl}/file?path=${encodeURIComponent(file.path)}`);
            const readData = await readRes.json();
            const content = readData.content;

            // Create/Save new
            const saveRes = await fetch(`${apiBaseUrl}/file`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: newName, content: content })
            });

            if (!saveRes.ok) throw new Error("Failed to save copy");

            addLog('success', `Duplicated to ${newName}`);

            // Auto expand folder if valid
            if (newName.includes('/')) {
                const parts = newName.split('/').slice(0, -1);
                let accum = '';
                const nextExpanded = new Set(expandedFolders);
                parts.forEach(p => {
                    accum = accum ? accum + '/' + p : p;
                    nextExpanded.add(accum);
                });
                setExpandedFolders(nextExpanded);
            }

            fetchFiles();
        } catch (e) {
            addLog('error', `Error replicating: ${e.message}`);
        }
    };

    const deleteItem = async (e, file) => {
        e.stopPropagation();
        setFileToDelete(file);
    };

    const confirmDelete = async () => {
        if (!fileToDelete) return;
        const file = fileToDelete;
        setFileToDelete(null); // Close modal

        try {
            const res = await fetch(`${apiBaseUrl}/file?path=${encodeURIComponent(file.path)}`, {
                method: 'DELETE',
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || 'Failed to delete');
            }

            if (currentFile?.path === file.path) {
                setCurrentFile(null);
                setEditorContent('');
            }
            addLog('info', `Deleted ${file.name}`);
            fetchFiles();
        } catch (e) {
            addLog('error', `Error deleting file: ${e.message}`);
        }
    };

    const renameItem = async (e, file) => {
        e.stopPropagation();
        setFileToRename(file);
        setRenameValue(file.path); // Use full path to keep folder structure
    };

    const confirmRename = async () => {
        if (!fileToRename || !renameValue || renameValue === fileToRename.name) return;
        const file = fileToRename;
        const newName = renameValue;

        setFileToRename(null); // Close modal

        try {
            const res = await fetch(`${apiBaseUrl}/file`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ old_path: file.path, new_path: newName })
            });
            if (!res.ok) throw new Error('Rename failed');

            addLog('info', `Renamed ${file.name} to ${newName}`);
            if (currentFile?.path === file.path) {
                setCurrentFile({ ...file, path: newName, name: newName });
            }
            fetchFiles();
        } catch (e) {
            addLog('error', `Error renaming: ${e.message}`);
        }
    };

    // --- Interaction ---
    const handleScreenClick = async (e) => {
        if (!currentFile) {
            addLog('info', 'Please select or create a test file first');
            return;
        }

        const img = e.target;
        const rect = img.getBoundingClientRect();
        const xPct = ((e.clientX - rect.left) / rect.width) * 100;
        const yPct = ((e.clientY - rect.top) / rect.height) * 100;

        const x = (xPct / 100) * deviceInfo.width;
        const y = (yPct / 100) * deviceInfo.height;

        let bestMatch = null;
        let minArea = Infinity;

        elements.forEach(el => {
            if (!el.bounds) return;
            const { left, top, right, bottom } = el.bounds;
            if (x >= left && x <= right && y >= top && y <= bottom) {
                const area = (right - left) * (bottom - top);
                const hasText = !!(el.text || el.attributes?.text || el.contentDescription || el['content-desc']);

                // Element prioritization: Smallest element, but prefer those with text/ID
                // Weight elements with text significantly lower to prefer them
                const score = hasText ? area * 0.5 : area;

                if (score < minArea) {
                    minArea = score;
                    bestMatch = el;
                }
            }
        });

        if (interactMode) {
            // "AUTO-INSERT & RUN" Mode (Interactive Studio style)
            let actionParams = null;
            let label = "";

            if (bestMatch) {
                const locs = getAvailableLocators(bestMatch);
                if (locs && locs.length > 0) {
                    // Use the best locator (text, ID, etc.)
                    const locator = locs[0];
                    actionParams = locator.selector;
                    label = `Tap ${locator.value}`;
                } else {
                    // Element found but no good locators - use center point
                    const { left, top, right, bottom } = bestMatch.bounds;
                    const centerX = ((left + right) / 2 / deviceInfo.width) * 100;
                    const centerY = ((top + bottom) / 2 / deviceInfo.height) * 100;
                    actionParams = { point: `${Math.round(centerX)}%,${Math.round(centerY)}%` };
                    label = `Tap element at ${Math.round(centerX)}%, ${Math.round(centerY)}%`;
                }
            } else {
                // No element found - use click coordinates
                actionParams = { point: `${Math.round(xPct)}%,${Math.round(yPct)}%` };
                label = `Tap at ${Math.round(xPct)}%, ${Math.round(yPct)}%`;
            }

            const stepCount = (editorContent.match(/^\s*-\s+/gm) || []).length + 1;
            const yaml = formatYaml('tapOn', actionParams);
            const cmd = `# ${stepCount}. ${label}\n${yaml}`;

            setEditorContent(prev => prev + (prev.endsWith('\n') ? '' : '\n') + cmd + '\n');
            addLog('info', `Inserting & Running: ${label}`);

            // Execute on device
            runStep({ tapOn: actionParams });
            return;
        }

        if (showInspector) {
            if (bestMatch) {
                const { left: l, top: t, right: r, bottom: b } = bestMatch.bounds;
                setPopupPosition({
                    x: ((l + r) / 2 / deviceInfo.width) * 100,
                    y: ((t + b) / 2 / deviceInfo.height) * 100
                });
                setSelectedElement(bestMatch);
                setSelectedLocatorIndex(0);
            } else {
                setSelectedElement({
                    text: `Point (${Math.round(xPct)}%, ${Math.round(yPct)}%)`,
                    isPoint: true,
                    bounds: { left: x, top: y, right: x, bottom: y }
                });
                setPopupPosition({ x: xPct, y: yPct });
            }
            return;
        }

        // When Inspector is OFF: Still show element selection and Inspector panel
        // (Users can choose which action to perform, not just auto-insert Tap On)
        if (bestMatch) {
            const { left: l, top: t, right: r, bottom: b } = bestMatch.bounds;
            setPopupPosition({
                x: ((l + r) / 2 / deviceInfo.width) * 100,
                y: ((t + b) / 2 / deviceInfo.height) * 100
            });
            setSelectedElement(bestMatch);
            setSelectedLocatorIndex(0);
        } else {
            setSelectedElement({
                text: `Point (${Math.round(xPct)}%, ${Math.round(yPct)}%)`,
                isPoint: true,
                bounds: { left: x, top: y, right: x, bottom: y }
            });
            setPopupPosition({ x: xPct, y: yPct });
        }
    };

    const handleAIGenerate = async (e, customInstruction = null) => {
        if (e) e.stopPropagation();
        setIsGeneratingAI(true);
        addLog('info', customInstruction ? 'Generating bulk tests...' : 'Asking AI to generate step...');

        try {
            // 1. Capture Screenshot (Fetch from backend endpoint)
            const snapRes = await fetch(`${apiBaseUrl}/screenshot?t=${Date.now()}`);
            const blob = await snapRes.blob();

            // Convert Blob to Base64
            const reader = new FileReader();
            reader.onloadend = async () => {
                const base64data = reader.result.split(',')[1];

                // 2. Hierarchy
                const hierarchyStr = JSON.stringify(hierarchy || {});

                // 3. Context
                const elementCtx = (selectedElement && selectedElement.isPoint)
                    ? `User clicked point at ${Math.round(popupPosition?.x || 0)}%, ${Math.round(popupPosition?.y || 0)}%`
                    : `User selected element: ${JSON.stringify(selectedElement)}`;

                const fullContext = `${elementCtx}\nAvailable Packages: ${packages.join(', ')}`;

                const payload = {
                    screenshot: base64data,
                    hierarchy: hierarchyStr,
                    context: fullContext,
                    apiKey: apiKey,
                    instruction: customInstruction
                };

                // 4. Call API
                const res = await fetch(`${apiBaseUrl}/api/ai/generate`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const data = await res.json();
                if (data.success) {
                    const stepCount = (editorContent.match(/^\s*-\s+/gm) || []).length + 1;
                    const cmd = `# ${stepCount}. ${customInstruction ? 'Bulk Assertions' : 'AI Step'}\n${data.yaml}`;
                    setEditorContent(prev => prev + (prev.endsWith('\n') ? '' : '\n') + cmd + '\n');
                    addLog('success', 'AI Generated Code successfully!');
                } else {
                    addLog('error', `AI Error: ${data.error}`);
                }
                setIsGeneratingAI(false);
            };
            reader.readAsDataURL(blob);

        } catch (err) {
            addLog('error', `AI Request Failed: ${err.message}`);
            setIsGeneratingAI(false);
        }
    };

    // --- Render ---
    return (
        <div className="app-container">
            <header className="header">
                <div className="header-brand">
                    <img src="/logo.png" alt="Ratl.ai Logo" className="header-logo" />
                    <h2 className="header-title">Ratl Studio</h2>
                </div>
                <div className="header-controls">
                    <button
                        className="btn"
                        style={{ background: 'none', border: 'none', color: '#888' }}
                        onClick={() => setShowSettings(true)}
                        title="Settings"
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
                    </button>

                    <div className="device-status" style={{ position: 'relative' }}>
                        <span className={`status-dot ${deviceConnected ? 'connected' : ''}`} />
                        <span
                            style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
                            onClick={() => { setIsEditingUrl(!isEditingUrl); setUrlInput(apiBaseUrl); }}
                            title="Click to Change Backend URL"
                        >
                            {deviceConnected ? 'CONNECTED' : 'NOT DETECTED'}
                            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                        </span>

                        {isEditingUrl && (
                            <div style={{
                                position: 'absolute', top: '100%', right: 0, marginTop: '8px',
                                background: 'var(--bg-tertiary)', border: '1px solid var(--border)',
                                padding: '12px', borderRadius: '8px', zIndex: 1000,
                                width: '300px', boxShadow: '0 10px 25px rgba(0,0,0,0.5)'
                            }}>
                                <div style={{ fontSize: '10px', marginBottom: '8px', color: 'var(--text-secondary)' }}>BACKEND API URL (PGY.IN / NGROK)</div>
                                <div style={{ display: 'flex', gap: '8px' }}>
                                    <input
                                        type="text"
                                        value={urlInput}
                                        onChange={(e) => setUrlInput(e.target.value)}
                                        placeholder="https://..."
                                        style={{ flex: 1, background: '#000', border: '1px solid var(--border)', color: '#fff', fontSize: '11px', padding: '4px 8px', borderRadius: '4px' }}
                                    />
                                    <button
                                        type="button"
                                        className="btn btn-primary"
                                        style={{ height: '24px', fontSize: '10px' }}
                                        onClick={() => updateBaseUrl(urlInput)}
                                    >Update</button>
                                </div>
                                <div style={{ fontSize: '9px', marginTop: '8px', color: '#ff3b30' }}>
                                    Note: If using HTTPS (Vercel), your backend MUST also use HTTPS (like pgy.in tunnel).
                                </div>
                            </div>
                        )}

                        {!deviceConnected && !isEditingUrl && (
                            <button
                                className="action-btn"
                                style={{ marginLeft: '4px', fontSize: '10px', padding: '2px 6px', width: 'auto' }}
                                onClick={() => {
                                    addLog('info', '🔄 Restarting ADB server...');
                                    executeCommand('adb kill-server && adb start-server && adb devices');
                                }}
                            >
                                FIX...
                            </button>
                        )}
                    </div>
                    <div style={{ display: 'flex', gap: '8px', background: 'rgba(0,0,0,0.2)', padding: '4px', borderRadius: '8px' }}>
                        <button className={`btn ${showInspector ? 'btn-primary' : 'btn-secondary'}`} onClick={() => {
                            setShowInspector(!showInspector);
                            if (!showInspector) setInteractMode(false);
                        }}>
                            {showInspector ? 'Inspector On' : 'Inspector Off'}
                        </button>
                    </div>
                </div>
            </header>

            <div className="main-layout">
                {/* 1. Sidebar */}
                <aside className="sidebar">
                    <div className="sidebar-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span>EXPLORER</span>
                        <button onClick={fetchFiles} className="action-btn" title="Refresh Files">
                            <span style={{ fontSize: '12px' }}>🔄</span>
                        </button>
                    </div>
                    <div className="sidebar-actions-row">
                        <button onClick={() => {
                            setModalData(prev => ({ ...prev, name: '' }));
                            setShowModal(true);
                        }} className="sidebar-action-btn">
                            <NewTestIcon />
                            <span>New Test</span>
                        </button>
                        <button onClick={() => setShowNewFolderModal(true)} className="sidebar-action-btn">
                            <NewFolderIcon />
                            <span>New Folder</span>
                        </button>
                    </div>
                    <ul className="file-list">
                        {sortedFiles.map(file => {
                            const isYaml = file.name.endsWith('.yaml') || file.name.endsWith('.yml');
                            const isFolder = !isYaml;
                            const parts = file.path.split('/');
                            const depth = parts.length - 1;
                            const displayName = parts[parts.length - 1];

                            // Visibility check
                            let visible = true;
                            if (depth > 0) {
                                let currentCheck = '';
                                for (let i = 0; i < parts.length - 1; i++) {
                                    currentCheck = currentCheck ? `${currentCheck}/${parts[i]}` : parts[i];
                                    if (!expandedFolders.has(currentCheck)) {
                                        visible = false;
                                        break;
                                    }
                                }
                            }

                            if (!visible) return null;

                            const isExpanded = expandedFolders.has(file.path);

                            const handleItemClick = (e) => {
                                // Prevent triggering if clicking actions
                                if (e.target.closest('.file-item-actions')) return;

                                if (isFolder) {
                                    const next = new Set(expandedFolders);
                                    if (next.has(file.path)) next.delete(file.path);
                                    else next.add(file.path);
                                    setExpandedFolders(next);
                                } else {
                                    loadFile(file);
                                }
                            };

                            return (
                                <li key={file.path}
                                    className={`file-item ${currentFile?.path === file.path ? 'active' : ''}`}
                                    onClick={handleItemClick}
                                    style={{ paddingLeft: `${depth * 15 + 10}px` }}
                                >
                                    <div className="file-item-main">
                                        <span className="file-item-icon">
                                            {isFolder && (
                                                <span style={{
                                                    display: 'inline-block',
                                                    marginRight: '4px',
                                                    fontSize: '10px',
                                                    transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)',
                                                    transition: 'transform 0.2s',
                                                    color: '#888'
                                                }}>▶</span>
                                            )}
                                            {isFolder ? <FolderIcon /> : <FileIcon />}
                                        </span>
                                        <span className="file-item-name">{displayName}</span>
                                    </div>
                                    <div className="file-item-actions">
                                        {isFolder && (
                                            <button className="action-btn" onClick={(e) => {
                                                e.stopPropagation();
                                                setModalData(prev => ({ ...prev, name: `${file.path}/` }));
                                                setShowModal(true);
                                            }} title="New Test in Folder">
                                                <span style={{ fontSize: '14px', fontWeight: 'bold' }}>+</span>
                                            </button>
                                        )}
                                        {!isFolder && (
                                            <button className="action-btn" onClick={(e) => duplicateItem(e, file)} title="Duplicate">
                                                <CopyIcon />
                                            </button>
                                        )}
                                        <button className="action-btn" onClick={(e) => renameItem(e, file)} title="Rename">
                                            <EditIcon />
                                        </button>
                                        <button className="action-btn delete" onClick={(e) => deleteItem(e, file)} title="Delete">
                                            <DeleteIcon />
                                        </button>
                                    </div>
                                </li>
                            );
                        })}
                        {files.length === 0 && (
                            <div style={{ padding: '2rem 1rem', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.9em' }}>
                                <p>No files yet.</p>
                                <p>Click 📄+ to create a new test flow.</p>
                            </div>
                        )}
                    </ul>
                </aside>
                <div className="sidebar-resizer" onMouseDown={startSidebarResize} />

                {/* 2. Editor & Terminal */}
                <div className="editor-pane">
                    {currentFile ? (
                        <>
                            <div className="editor-tabs">
                                <div className="tab active">
                                    <span>{currentFile.name}</span>
                                    <span style={{ fontSize: '12px', color: '#ccc', cursor: 'pointer' }}>×</span>
                                </div>
                            </div>

                            <div className="editor-toolbar">
                                <div style={{ display: 'flex', gap: '8px' }}>
                                    {currentFile.name.endsWith('.sh') ? (
                                        <button className="btn btn-primary" onClick={() => {
                                            setActiveTerminalTab('TERMINAL');
                                            executeCommand(currentFile.path === '../start.sh' ? './start.sh' : `./${currentFile.name}`);
                                        }}>
                                            🚀 Run Script
                                        </button>
                                    ) : (
                                        <button className="btn btn-primary" onClick={runTest} disabled={isRunning}>
                                            {isRunning ? 'Running...' : '▶ Run Locally'}
                                        </button>
                                    )}
                                    <button
                                        className="btn btn-secondary"
                                        onClick={stopTest}
                                        disabled={!isRunning}
                                        style={{ borderColor: isRunning ? '#ff3b30' : 'var(--border)', color: isRunning ? '#ff3b30' : 'var(--text-secondary)' }}
                                    >
                                        ⏹ Stop
                                    </button>
                                </div>
                            </div>

                            <div className="editor-container">
                                <div className="line-numbers" ref={lineNumbersRef}>
                                    {Array.from({ length: lineCount }, (_, i) => {
                                        const ln = i + 1;
                                        const status = lineStatuses[ln];
                                        const isErrorLine = errorLine === ln;
                                        return (
                                            <div
                                                key={ln}
                                                className="line-number-cell"
                                                style={{
                                                    backgroundColor: isErrorLine ? 'rgba(255, 59, 48, 0.15)' : 'transparent',
                                                    borderLeft: isErrorLine ? '3px solid #ff3b30' : '3px solid transparent',
                                                    transition: 'all 0.2s ease'
                                                }}
                                            >
                                                <span
                                                    className="line-number-text"
                                                    style={{
                                                        minWidth: '32px',
                                                        textAlign: 'right',
                                                        fontWeight: '500',
                                                        color: isErrorLine ? '#ff3b30' : 'inherit'
                                                    }}
                                                >
                                                    {ln}
                                                </span>
                                                <div className="line-status-icon" style={{ width: '24px', display: 'flex', justifyContent: 'center', marginLeft: '8px' }}>
                                                    {isErrorLine && <span style={{ fontSize: '14px' }}>⚠️</span>}
                                                    {!isErrorLine && status === 'pass' && <span className="status-pass">✅</span>}
                                                    {!isErrorLine && status === 'fail' && <span className="status-fail">❌</span>}
                                                    {!isErrorLine && status === 'running' && <span className="status-running">⏳</span>}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                                <textarea
                                    className="editor-textarea"
                                    value={editorContent}
                                    onChange={(e) => {
                                        setEditorContent(e.target.value);
                                        // Clear error highlight when user edits
                                        if (errorLine) setErrorLine(null);
                                    }}
                                    onScroll={(e) => {
                                        if (lineNumbersRef.current) {
                                            lineNumbersRef.current.scrollTop = e.target.scrollTop;
                                        }
                                    }}
                                    onKeyDown={(e) => {
                                        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                                            e.preventDefault();
                                            saveFile();
                                        }
                                    }}
                                    spellCheck="false"
                                />
                            </div>
                        </>
                    ) : (
                        <div className="editor-placeholder">Select a flow to edit</div>
                    )}

                    {/* Terminal (VS Code Style) */}
                    <div className="terminal-resizer" onMouseDown={startTerminalResize} />
                    <div className="terminal-panel">
                        <div className="terminal-header">
                            <div className="terminal-tabs">
                                {['PROBLEMS', 'OUTPUT', 'DEBUG CONSOLE', 'TERMINAL'].map(tab => (
                                    <button
                                        key={tab}
                                        className={`terminal-tab ${activeTerminalTab === tab ? 'active' : ''}`}
                                        onClick={() => setActiveTerminalTab(tab)}
                                    >
                                        {tab}
                                    </button>
                                ))}
                            </div>
                            <div className="terminal-actions">
                                <button className="action-btn" title="Scroll to Top" onClick={() => {
                                    if (terminalEndRef.current?.parentElement) {
                                        terminalEndRef.current.parentElement.scrollTop = 0;
                                    }
                                }}>
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="18 15 12 9 6 15"></polyline></svg>
                                </button>
                                <button className="action-btn" title="Scroll to Bottom" onClick={() => {
                                    if (terminalEndRef.current?.parentElement) {
                                        terminalEndRef.current.parentElement.scrollTop = terminalEndRef.current.parentElement.scrollHeight;
                                    }
                                }}>
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
                                </button>
                                <button className="action-btn" title="Clear Terminal" onClick={clearLogs}>
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"></line></svg>
                                </button>
                            </div>
                        </div>
                        <div className="terminal-content" onClick={activeTerminalTab === 'TERMINAL' ? focusTerminal : undefined}>
                            {activeTerminalTab === 'OUTPUT' && logs.map((log, i) => (
                                <div key={i} className={`terminal-line terminal-${log.type}`}>
                                    <span className="time">[{log.time}]</span>
                                    <span className="terminal-text">{log.text}</span>
                                </div>
                            ))}

                            {activeTerminalTab === 'TERMINAL' && (
                                <>
                                    <div className="terminal-welcome" style={{ color: '#888', marginBottom: '8px', fontSize: '11px' }}>
                                        Interactive Terminal - Execute shell commands directly on the server.
                                    </div>
                                    {logs.filter(l => l.text.startsWith('>') || l.type === 'info-cmd').map((log, i) => (
                                        <div key={i} className={`terminal-line terminal-${log.type}`}>
                                            <span className="terminal-text">{log.text}</span>
                                        </div>
                                    ))}
                                    <div className="terminal-input-row" style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '13px' }}>
                                        <span className="terminal-prompt" style={{ color: '#10b981', fontWeight: 'bold' }}>
                                            kalyanibadgujar@rattl-runner
                                        </span>
                                        <span style={{ color: '#ffffff', margin: '0 8px' }}>
                                            {formatTerminalPath(terminalCwd).split('/').pop() || 'rattl-runner'}
                                        </span>
                                        <span className="terminal-prompt" style={{ color: '#ffffff', marginRight: '8px' }}>%</span>
                                        <form onSubmit={handleTerminalSubmit} style={{ flex: 1 }}>
                                            <input
                                                ref={terminalInputRef}
                                                type="text"
                                                className="terminal-input"
                                                value={terminalInput}
                                                onChange={(e) => setTerminalInput(e.target.value)}
                                                placeholder="Type command and press Enter..."
                                                spellCheck="false"
                                                autoComplete="off"
                                            />
                                        </form>
                                    </div>
                                </>
                            )}

                            {activeTerminalTab === 'PROBLEMS' && (
                                <div style={{ color: '#888', padding: '10px' }}>No problems detected in the current workspace.</div>
                            )}

                            {activeTerminalTab === 'DEBUG CONSOLE' && (
                                <div style={{ color: '#888', padding: '10px' }}>Debug console is ready.</div>
                            )}

                            <div ref={terminalEndRef} />
                        </div>
                    </div>
                </div>

                {/* 3. Device & Inspector */}
                <div className="device-resizer" onMouseDown={startDeviceResize} />
                <aside className={`device-pane ${showInspector ? 'inspector-active' : ''}`}>

                    {!deviceConnected ? (
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', padding: '2rem', color: 'var(--text-secondary)' }}>
                            <div style={{ background: 'rgba(255,255,255,0.02)', padding: '2rem', borderRadius: '24px', border: '1px solid var(--border)', width: '100%', maxWidth: '400px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.5rem', boxShadow: '0 20px 40px rgba(0,0,0,0.3)' }}>
                                <div style={{ position: 'relative' }}>
                                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#666" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                        <rect x="5" y="2" width="14" height="20" rx="2" ry="2"></rect>
                                        <line x1="12" y1="18" x2="12.01" y2="18"></line>
                                    </svg>
                                    <div style={{ position: 'absolute', top: -5, right: -5, background: '#ff3b30', width: '20px', height: '20px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '2px solid var(--bg-secondary)' }}>
                                        <span style={{ color: 'white', fontSize: '12px', fontWeight: 'bold' }}>!</span>
                                    </div>
                                </div>
                                <div style={{ textAlign: 'center' }}>
                                    <h3 style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '0.4rem' }}>No Device Detected</h3>
                                    <p style={{ fontSize: '0.8rem', lineHeight: '1.4' }}>Follow these steps to connect your phone to the cloud studio.</p>
                                </div>

                                <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                    <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                                        <div style={{ width: '24px', height: '24px', borderRadius: '50%', background: 'var(--accent)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 'bold', flexShrink: 0 }}>1</div>
                                        <div>
                                            <div style={{ fontSize: '0.8rem', fontWeight: '600', color: '#fff' }}>Plug in USB</div>
                                            <div style={{ fontSize: '0.7rem' }}>Enable USB Debugging on your phone.</div>
                                        </div>
                                    </div>

                                    <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                                        <div style={{ width: '24px', height: '24px', borderRadius: '50%', background: 'var(--accent)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 'bold', flexShrink: 0 }}>2</div>
                                        <div style={{ flex: 1 }}>
                                            <div style={{ fontSize: '0.8rem', fontWeight: '600', color: '#fff' }}>Start Local Bridge</div>
                                            <div style={{ fontSize: '0.7rem', marginBottom: '6px' }}>Run this in Terminal (Mac/Linux) or Git Bash (Windows):</div>
                                            <code
                                                style={{ display: 'block', padding: '6px 10px', background: '#000', borderRadius: '6px', fontSize: '10px', color: '#10b981', cursor: 'pointer', border: '1px solid #10b98133', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}
                                                onClick={() => {
                                                    const cmd = `curl -sL ${window.location.origin}/install.sh | bash`;
                                                    navigator.clipboard.writeText(cmd);
                                                    addLog('success', 'Copied script command to clipboard!');
                                                }}
                                                title="Click to copy"
                                            >
                                                curl -sL {window.location.host}/install.sh | bash
                                            </code>
                                        </div>
                                    </div>

                                    <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                                        <div style={{ width: '24px', height: '24px', borderRadius: '50%', background: 'var(--accent)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 'bold', flexShrink: 0 }}>3</div>
                                        <div style={{ width: '100%' }}>
                                            <div style={{ fontSize: '0.8rem', fontWeight: '600', color: '#fff' }}>Paste Tunnel URL</div>
                                            <div style={{ fontSize: '0.7rem', marginBottom: '8px' }}>Paste the <b>.trycloudflare.com</b> link from the terminal below:</div>
                                            <div style={{ display: 'flex', gap: '8px', width: '100%' }}>
                                                <input
                                                    type="text"
                                                    value={urlInput}
                                                    onChange={(e) => setUrlInput(e.target.value)}
                                                    placeholder="https://..."
                                                    style={{ flex: 1, background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border)', color: '#fff', fontSize: '12px', padding: '8px', borderRadius: '6px' }}
                                                    onKeyDown={(e) => {
                                                        if (e.key === 'Enter') updateBaseUrl(urlInput);
                                                    }}
                                                />
                                                <button
                                                    type="button"
                                                    className="btn btn-primary"
                                                    onClick={() => updateBaseUrl(urlInput)}
                                                >
                                                    Connect
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                            <div style={{
                                padding: '0.5rem 1rem',
                                background: 'rgba(16, 185, 129, 0.1)',
                                borderBottom: '1px solid rgba(16, 185, 129, 0.2)',
                                color: '#10b981',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '8px'
                            }}>
                                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981' }}></div>
                                <span style={{ fontSize: '10px', fontWeight: 800, letterSpacing: '0.05em' }}>
                                    {deviceInfo.model ? deviceInfo.model.toUpperCase() : 'DEVICE CONNECTED'}
                                </span>
                            </div>

                            <div className="device-content-wrapper" style={{
                                display: 'flex',
                                flexDirection: 'row',
                                justifyContent: 'center',
                                alignItems: 'start',
                                gap: '24px',
                                height: 'calc(100% - 40px)',
                                width: '100%',
                                padding: '20px',
                                overflow: 'hidden'
                            }}>
                                <div className="device-frame" style={{
                                    position: 'relative',
                                    aspectRatio: `${deviceInfo.width} / ${deviceInfo.height}`,
                                    flexShrink: 0
                                }}>
                                    <img
                                        src={`${apiBaseUrl}/screenshot?t=${refreshKey}`}
                                        className="device-screen"
                                        alt="Device Screen"
                                        onClick={handleScreenClick}
                                        onLoad={onScreenLoad}
                                        onError={() => setTimeout(onScreenLoad, 1000)} // Retry on error
                                    />

                                    {showInspector && deviceConnected && (
                                        <div className="inspector-layer">
                                            {/* Crosshair Lines */}
                                            {selectedElement && (
                                                <>
                                                    <div
                                                        className="inspector-crosshair-v"
                                                        style={{ left: `${popupPosition?.x}%` }}
                                                    />
                                                    <div
                                                        className="inspector-crosshair-h"
                                                        style={{ top: `${popupPosition?.y}%` }}
                                                    />
                                                </>
                                            )}

                                            {elements.map((el, i) => {
                                                if (!el.bounds) return null;
                                                const { left: l, top: t, right: r, bottom: b } = el.bounds;
                                                const left = (l / deviceInfo.width) * 100;
                                                const top = (t / deviceInfo.height) * 100;
                                                const width = ((r - l) / deviceInfo.width) * 100;
                                                const height = ((b - t) / deviceInfo.height) * 100;

                                                return (
                                                    <div
                                                        key={i}
                                                        className={`inspector-element ${selectedElement === el ? 'selected' : ''}`}
                                                        style={{
                                                            left: `${left}%`,
                                                            top: `${top}%`,
                                                            width: `${width}%`,
                                                            height: `${height}%`
                                                        }}
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            const centerX = ((l + r) / 2 / deviceInfo.width) * 100;
                                                            const centerY = ((t + b) / 2 / deviceInfo.height) * 100;
                                                            setPopupPosition({ x: centerX, y: centerY });
                                                            setSelectedElement(el);
                                                            setSelectedLocatorIndex(0);
                                                        }}
                                                        title={el.text || el['resource-id'] || el.class}
                                                    />
                                                );
                                            })}
                                        </div>
                                    )}
                                </div>

                                {/* Side Intelligence & Inspector Panel */}
                                <div className="inspector-sidebar-panel" style={{
                                    width: '360px',
                                    height: '100%',
                                    background: 'var(--bg-secondary)',
                                    border: '1px solid var(--border)',
                                    borderRadius: '16px',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    overflow: 'hidden',
                                    boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
                                    backdropFilter: 'blur(10px)',
                                    animation: 'sidebarIn 0.3s cubic-bezier(0.16, 1, 0.3, 1)'
                                }}>
                                    {/* Tab Header */}
                                    <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', background: 'rgba(0,0,0,0.2)' }}>
                                        <button
                                            onClick={() => setActiveTab('inspector')}
                                            style={{
                                                flex: 1, padding: '12px', fontSize: '11px', fontWeight: 700,
                                                color: activeTab === 'inspector' ? 'var(--accent)' : '#666',
                                                borderBottom: activeTab === 'inspector' ? '2px solid var(--accent)' : 'none',
                                                background: 'transparent', border: 'none', cursor: 'pointer', transition: '0.2s'
                                            }}
                                        >
                                            🔍 INSPECTOR
                                        </button>
                                        <button
                                            onClick={() => { setActiveTab('intelligence'); fetchIntelligence(); }}
                                            style={{
                                                flex: 1, padding: '12px', fontSize: '11px', fontWeight: 700,
                                                color: activeTab === 'intelligence' ? '#a78bfa' : '#666',
                                                borderBottom: activeTab === 'intelligence' ? '2px solid #a78bfa' : 'none',
                                                background: 'transparent', border: 'none', cursor: 'pointer', transition: '0.2s'
                                            }}
                                        >
                                            🧠 AGENT BRAIN
                                        </button>
                                    </div>

                                    <div style={{ flex: 1, overflowY: 'auto', padding: '16px' }} className="custom-scrollbar">
                                        {activeTab === 'intelligence' ? (
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                                                {/* 1. Header & Confidence Trend */}
                                                <div style={{
                                                    background: 'linear-gradient(135deg, rgba(167, 139, 250, 0.1) 0%, rgba(139, 92, 246, 0.05) 100%)',
                                                    padding: '24px', borderRadius: '16px', border: '1px solid rgba(167, 139, 250, 0.2)',
                                                    position: 'relative', overflow: 'hidden'
                                                }}>
                                                    <div style={{ position: 'absolute', top: '-20px', right: '-20px', width: '100px', height: '100px', background: 'var(--accent)', filter: 'blur(60px)', opacity: 0.2 }}></div>

                                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                                                        <div>
                                                            <div style={{ fontSize: '10px', color: '#a78bfa', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em' }}>Intelligence Confidence</div>
                                                            <div style={{ fontSize: '36px', fontWeight: 900, color: '#fff', marginTop: '4px' }}>
                                                                {(() => {
                                                                    const runs = agentIntelligence?.runs || [];
                                                                    if (runs.length === 0) return 0;
                                                                    return Math.round(runs[runs.length - 1].confidence_score * 100);
                                                                })()}
                                                                <span style={{ fontSize: '16px', opacity: 0.5, fontWeight: 500 }}>%</span>
                                                            </div>
                                                        </div>
                                                        <div style={{ textAlign: 'right' }}>
                                                            <div style={{ fontSize: '9px', color: '#666', fontWeight: 700 }}>STABILITY</div>
                                                            <div style={{ fontSize: '11px', color: '#10b981', fontWeight: 600 }}>+2.4% vs last run</div>
                                                        </div>
                                                    </div>

                                                    {/* Confidence Sparkline (SVG) */}
                                                    <div style={{ height: '40px', width: '100%', marginBottom: '8px' }}>
                                                        <svg width="100%" height="40" preserveAspectRatio="none">
                                                            <defs>
                                                                <linearGradient id="lineGrad" x1="0" y1="0" x2="0" y2="1">
                                                                    <stop offset="0%" stopColor="#a78bfa" stopOpacity="0.5" />
                                                                    <stop offset="100%" stopColor="#a78bfa" stopOpacity="0" />
                                                                </linearGradient>
                                                            </defs>
                                                            {(() => {
                                                                const runs = agentIntelligence?.runs || [];
                                                                if (runs.length < 2) return null;
                                                                const scores = runs.slice(-10).map(r => r.confidence_score * 40);
                                                                const width = 100 / (scores.length - 1);
                                                                const path = `M 0,${40 - scores[0]} ` + scores.map((s, i) => `L ${i * width}%,${40 - s}`).join(' ');
                                                                const areaPath = path + ` L 100%,40 L 0,40 Z`;
                                                                return (
                                                                    <>
                                                                        <path d={areaPath} fill="url(#lineGrad)" />
                                                                        <path d={path} fill="none" stroke="#a78bfa" strokeWidth="2" strokeLinejoin="round" />
                                                                    </>
                                                                );
                                                            })()}
                                                        </svg>
                                                    </div>
                                                </div>

                                                {/* 2. Core Stats Grid */}
                                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                                                    <div style={{ background: 'rgba(255,255,255,0.02)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border)' }}>
                                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                                                            <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10b981' }}></div>
                                                            <span style={{ fontSize: '9px', color: '#666', fontWeight: 800, textTransform: 'uppercase' }}>Auto-Healed</span>
                                                        </div>
                                                        <div style={{ fontSize: '24px', fontWeight: 900, color: '#fff' }}>{agentIntelligence?.healed_count || 0}</div>
                                                        <div style={{ fontSize: '10px', color: '#444', marginTop: '2px' }}>Events recorded</div>
                                                    </div>
                                                    <div style={{ background: 'rgba(255,255,255,0.02)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border)' }}>
                                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                                                            <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#a78bfa' }}></div>
                                                            <span style={{ fontSize: '9px', color: '#666', fontWeight: 800, textTransform: 'uppercase' }}>Memory Size</span>
                                                        </div>
                                                        <div style={{ fontSize: '24px', fontWeight: 900, color: '#fff' }}>{Object.keys(agentIntelligence?.screens || {}).length}</div>
                                                        <div style={{ fontSize: '10px', color: '#444', marginTop: '2px' }}>Learned screens</div>
                                                    </div>
                                                </div>

                                                {/* 3. Healing Timeline */}
                                                <div>
                                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                                                        <div style={{ fontSize: '10px', fontWeight: 800, color: '#fff', textTransform: 'uppercase', letterSpacing: '0.08em' }}>🧠 Healing Timeline</div>
                                                        <div style={{ fontSize: '9px', color: 'var(--accent)', fontWeight: 700 }}>LIVE</div>
                                                    </div>
                                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                                                        {agentIntelligence?.failures?.filter(f => f.healed).slice(-5).reverse().map((fail, i) => (
                                                            <div key={fail.failure_id} style={{
                                                                padding: '12px', background: 'rgba(16, 185, 129, 0.05)', borderRadius: '8px', borderLeft: '3px solid #10b981',
                                                                position: 'relative'
                                                            }}>
                                                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '4px' }}>
                                                                    <div style={{ fontSize: '11px', fontWeight: 700, color: '#fff' }}>Auto-Heal: {fail.reason}</div>
                                                                    <div style={{ fontSize: '9px', color: '#666' }}>{new Date().toLocaleTimeString()}</div>
                                                                </div>
                                                                <div style={{ fontSize: '11px', color: '#888', fontStyle: 'italic', marginBottom: '4px' }}>"{fail.notes}"</div>
                                                                <div style={{ display: 'flex', gap: '6px' }}>
                                                                    <span style={{ fontSize: '9px', background: 'rgba(255,255,255,0.05)', color: '#aaa', padding: '2px 6px', borderRadius: '4px' }}>Mode: LEARN</span>
                                                                    <span style={{ fontSize: '9px', background: 'rgba(16, 185, 129, 0.1)', color: '#10b981', padding: '2px 6px', borderRadius: '4px' }}>+0.01 Confidence</span>
                                                                </div>
                                                            </div>
                                                        ))}
                                                        {(!agentIntelligence?.failures || agentIntelligence.failures.filter(f => f.healed).length === 0) && (
                                                            <div style={{ padding: '24px', textAlign: 'center', border: '1px dashed var(--border)', borderRadius: '12px', opacity: 0.5 }}>
                                                                <div style={{ fontSize: '11px' }}>No healing events yet. The agent is strictly validating flows.</div>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>

                                                {/* 4. Run History Table */}
                                                <div>
                                                    <div style={{ fontSize: '10px', fontWeight: 800, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '12px' }}>Recent Test Runs</div>
                                                    <div style={{ borderRadius: '12px', border: '1px solid var(--border)', overflow: 'hidden' }}>
                                                        {agentIntelligence?.runs?.slice(-5).reverse().map((run, i) => (
                                                            <div key={run.run_id} style={{
                                                                padding: '12px', borderBottom: i === 4 ? 'none' : '1px solid var(--border)',
                                                                background: 'rgba(255,255,255,0.01)', display: 'flex', justifyContent: 'space-between', alignItems: 'center'
                                                            }}>
                                                                <div>
                                                                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                                                        <div style={{ fontSize: '11px', fontWeight: 700 }}>{run.test_name}</div>
                                                                        <div style={{ fontSize: '9px', background: run.status === 'PASS' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', color: run.status === 'PASS' ? '#10b981' : '#ef4444', padding: '1px 6px', borderRadius: '4px' }}>{run.status}</div>
                                                                    </div>
                                                                    <div style={{ fontSize: '10px', color: '#555' }}>ID: {run.run_id} • {(run.execution_time_ms / 1000).toFixed(1)}s</div>
                                                                </div>
                                                                <div style={{ textAlign: 'right' }}>
                                                                    <div style={{ fontSize: '12px', fontWeight: 700, color: '#fff' }}>{Math.round(run.confidence_score * 100)}%</div>
                                                                    <div style={{ fontSize: '9px', color: '#444' }}>Confidence</div>
                                                                    <button
                                                                        onClick={async () => {
                                                                            try {
                                                                                const res = await fetch(`${apiBaseUrl}/report/${run.run_id}`);
                                                                                const report = await res.json();
                                                                                setCurrentReport(report);
                                                                                setShowReportModal(true);
                                                                            } catch (err) {
                                                                                console.error('Failed to fetch report:', err);
                                                                            }
                                                                        }}
                                                                        style={{ marginTop: '8px', fontSize: '9px', background: 'rgba(167, 139, 250, 0.1)', color: '#a78bfa', border: '1px solid rgba(167, 139, 250, 0.2)', padding: '2px 6px', borderRadius: '4px', cursor: 'pointer' }}>
                                                                        View Report
                                                                    </button>
                                                                </div>
                                                            </div>
                                                        ))}
                                                        {(!agentIntelligence?.runs || agentIntelligence.runs.length === 0) && (
                                                            <div style={{ padding: '20px', textAlign: 'center', fontSize: '11px', color: '#666' }}>No runs recorded.</div>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        ) : (
                                            /* Inspector Content */
                                            selectedElement ? (
                                                <>
                                                    <div style={{ padding: '0 0 16px 0', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent)' }}></div>
                                                            <span style={{ fontSize: '11px', fontWeight: 800, color: '#fff', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Inspector</span>
                                                        </div>
                                                        <div style={{ display: 'flex', gap: '4px' }}>
                                                            <button
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    fetchHierarchy();
                                                                    setRefreshKey(Date.now());
                                                                }}
                                                                className={isFetchingHierarchy ? 'spin' : ''}
                                                                style={{ background: 'none', border: 'none', color: '#666', cursor: 'pointer', fontSize: '14px', padding: '4px', display: 'flex', alignItems: 'center' }}
                                                                title="Refresh Hierarchy"
                                                            >
                                                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M23 4v6h-6"></path><path d="M1 20v-6h6"></path><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
                                                            </button>
                                                            <button onClick={() => setSelectedElement(null)} style={{ background: 'none', border: 'none', color: '#666', cursor: 'pointer', fontSize: '18px', padding: '4px' }}>×</button>
                                                        </div>
                                                    </div>
                                                    <div style={{ flex: 1, overflowY: 'auto', padding: '16px 0 0 0' }}>
                                                        {(() => {
                                                            const locators = getAvailableLocators(selectedElement);
                                                            const currentLocator = selectedElement.isPoint
                                                                ? { selector: { point: `${Math.round(popupPosition?.x || 0)}%,${Math.round(popupPosition?.y || 0)}%` }, syntax: `point: "${Math.round(popupPosition?.x || 0)}%,${Math.round(popupPosition?.y || 0)}%"` }
                                                                : (locators[selectedLocatorIndex] || locators[0] || { selector: { point: `${Math.round(popupPosition?.x || 0)}%,${Math.round(popupPosition?.y || 0)}%` }, syntax: `point: "${Math.round(popupPosition?.x || 0)}%,${Math.round(popupPosition?.y || 0)}%"` });

                                                            const selector = currentLocator.selector;
                                                            const stepCount = (editorContent.match(/^\s*-\s+/gm) || []).length + 1;

                                                            const labelText = currentLocator.type === 'Text' ? currentLocator.value : '';
                                                            const displayLabel = labelText.length > 20 ? labelText.substring(0, 18) + '...' : labelText;

                                                            const groups = [
                                                                {
                                                                    title: '👉 Tap & Click',
                                                                    actions: [
                                                                        { label: displayLabel ? `Tap "${displayLabel}"` : 'Tap Element', yaml: formatYaml('tapOn', selector), cmd: 'tapOn' }
                                                                    ]
                                                                },
                                                                {
                                                                    title: '👁️ Assertions',
                                                                    actions: [
                                                                        { label: displayLabel ? `Assert "${displayLabel}"` : 'Assert Visible', yaml: formatYaml('assertVisible', selector), cmd: 'assertVisible' },
                                                                        { label: 'Assert Not Visible', yaml: formatYaml('assertNotVisible', selector), cmd: 'assertNotVisible' }
                                                                    ]
                                                                },
                                                                {
                                                                    title: '🖐️ Swipe & Gestures',
                                                                    actions: [
                                                                        { label: 'Swipe Up', yaml: formatYaml('swipe', { direction: 'UP' }), cmd: 'swipe' },
                                                                        { label: 'Swipe Down', yaml: formatYaml('swipe', { direction: 'DOWN' }), cmd: 'swipe' },
                                                                        { label: 'Swipe Right', yaml: formatYaml('swipe', { direction: 'RIGHT' }), cmd: 'swipe' },
                                                                        { label: 'Swipe Left', yaml: formatYaml('swipe', { direction: 'LEFT' }), cmd: 'swipe' }
                                                                    ]
                                                                },
                                                                {
                                                                    title: '📜 Scroll',
                                                                    actions: [
                                                                        { label: 'Scroll Down', yaml: `- scroll:\n    direction: DOWN`, cmd: 'scroll' },
                                                                        { label: 'Scroll Up', yaml: `- scroll:\n    direction: UP`, cmd: 'scroll' },
                                                                        { label: 'Scroll Right', yaml: `- scroll:\n    direction: RIGHT`, cmd: 'scroll' },
                                                                        { label: 'Scroll Left', yaml: `- scroll:\n    direction: LEFT`, cmd: 'scroll' }
                                                                    ]
                                                                },
                                                                {
                                                                    title: '⌨️ Input & Text',
                                                                    actions: [
                                                                        { label: 'Input Text', yaml: `- inputText: "your text here"`, cmd: 'inputText' },
                                                                        { label: 'Press Enter', yaml: `- pressKey: Enter`, cmd: 'pressKey' }
                                                                    ]
                                                                }
                                                            ];

                                                            return (
                                                                <>
                                                                    <div style={{ marginBottom: '24px' }}>
                                                                        <div style={{ fontSize: '9px', color: 'var(--accent)', fontWeight: 800, textTransform: 'uppercase', marginBottom: '8px', letterSpacing: '0.05em' }}>AI Assistant</div>
                                                                        <div style={{ marginBottom: '8px' }}>
                                                                            <textarea
                                                                                placeholder="Describe action (e.g. 'Tap the Login button')"
                                                                                value={aiPrompt}
                                                                                onChange={(e) => setAiPrompt(e.target.value)}
                                                                                style={{
                                                                                    width: '100%',
                                                                                    background: 'rgba(0,0,0,0.2)',
                                                                                    border: '1px solid var(--border)',
                                                                                    borderRadius: '6px',
                                                                                    padding: '8px',
                                                                                    fontSize: '11px',
                                                                                    color: 'var(--text-primary)',
                                                                                    minHeight: '60px',
                                                                                    resize: 'vertical',
                                                                                    marginBottom: '4px',
                                                                                    fontFamily: 'inherit'
                                                                                }}
                                                                            />
                                                                            <button
                                                                                className="inspector-action-btn"
                                                                                style={{ width: '100%', border: '1px solid var(--accent)', background: 'var(--accent)', color: '#fff' }}
                                                                                onClick={(e) => handleAIGenerate(e, aiPrompt || null)}
                                                                                disabled={isGeneratingAI}
                                                                            >
                                                                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
                                                                                    {isGeneratingAI ? <span className="spin" style={{ fontSize: '12px' }}>↻</span> : <span style={{ fontSize: '12px' }}>✨</span>}
                                                                                    <span style={{ fontWeight: 600, fontSize: '11px' }}>Generate from Prompt</span>
                                                                                </div>
                                                                            </button>
                                                                        </div>

                                                                        <div style={{ display: 'flex', gap: '8px' }}>
                                                                            <button
                                                                                className="inspector-action-btn"
                                                                                style={{ flex: 1, border: '1px solid #10b981', background: 'rgba(16, 185, 129, 0.1)' }}
                                                                                onClick={(e) => handleAIGenerate(e, "Generate assertions for all visible text elements")}
                                                                                disabled={isGeneratingAI}
                                                                            >
                                                                                <span style={{ fontWeight: 600, fontSize: '10px' }}>Add Assertion</span>
                                                                            </button>
                                                                        </div>
                                                                    </div>

                                                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                                                                        {groups.map((group, gIdx) => (
                                                                            <div key={gIdx}>
                                                                                <div style={{ fontSize: '10px', fontWeight: 800, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '12px' }}>
                                                                                    {group.title}
                                                                                </div>
                                                                                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                                                                    {group.actions.map((action, aIdx) => (
                                                                                        <div key={aIdx} style={{ display: 'flex', gap: '4px' }}>
                                                                                            <button
                                                                                                className="inspector-action-btn"
                                                                                                style={{ flex: 1 }}
                                                                                                onClick={(e) => {
                                                                                                    e.stopPropagation();
                                                                                                    const cmd = `# ${stepCount}. ${action.label}\n${action.yaml}`;
                                                                                                    setEditorContent(prev => prev + (prev.endsWith('\n') ? '' : '\n') + cmd + '\n');
                                                                                                    addLog('success', `Added to YAML: ${action.label}`);
                                                                                                }}
                                                                                            >
                                                                                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                                                                    <span style={{ fontWeight: 600 }}>{action.label}</span>
                                                                                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
                                                                                                </div>
                                                                                            </button>
                                                                                            <button
                                                                                                className="btn-run-small"
                                                                                                onClick={(e) => {
                                                                                                    e.stopPropagation();
                                                                                                    // Build step logic for runStep
                                                                                                    let stepObj = {};
                                                                                                    if (action.cmd === 'tapOn' || action.cmd === 'assertVisible' || action.cmd === 'assertNotVisible') {
                                                                                                        stepObj[action.cmd] = selector;
                                                                                                    } else if (action.cmd === 'scroll') {
                                                                                                        let dir = 'DOWN';
                                                                                                        if (action.yaml.includes('UP')) dir = 'UP';
                                                                                                        else if (action.yaml.includes('RIGHT')) dir = 'RIGHT';
                                                                                                        else if (action.yaml.includes('LEFT')) dir = 'LEFT';
                                                                                                        stepObj.scroll = { direction: dir };
                                                                                                    } else if (action.cmd === 'swipe') {
                                                                                                        let dir = 'DOWN';
                                                                                                        if (action.yaml.includes('UP')) dir = 'UP';
                                                                                                        else if (action.yaml.includes('RIGHT')) dir = 'RIGHT';
                                                                                                        else if (action.yaml.includes('LEFT')) dir = 'LEFT';
                                                                                                        stepObj.swipe = { direction: dir };
                                                                                                    } else {
                                                                                                        // Fallback to YAML for complex commands
                                                                                                        runStep(action.yaml);
                                                                                                        return;
                                                                                                    }
                                                                                                    addLog('info', `Running: ${action.label}`);
                                                                                                    runStep(stepObj);
                                                                                                }}
                                                                                            >
                                                                                                ▶
                                                                                            </button>
                                                                                        </div>
                                                                                    ))}
                                                                                </div>
                                                                            </div>
                                                                        ))}
                                                                    </div>
                                                                </>
                                                            );
                                                        })()}
                                                    </div>
                                                </>
                                            ) : (
                                                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', opacity: 0.3, textAlign: 'center', padding: '40px' }}>
                                                    <div style={{ fontSize: '32px', marginBottom: '16px' }}>🖱️</div>
                                                    <div style={{ fontSize: '12px', fontWeight: 600 }}>Inspector Active</div>
                                                    <div style={{ fontSize: '10px' }}>Tap any element on the screen to view actions</div>
                                                </div>
                                            )
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </aside>
            </div>

            {/* Modal */}
            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>New Test Flow</h2>
                            <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
                        </div>
                        <div className="modal-body">
                            <div className="modal-form">
                                <div className="modal-tabs">
                                    <button className={`modal-tab ${modalData.type === 'Mobile Test' ? 'active' : ''}`} onClick={() => setModalData({ ...modalData, type: 'Mobile Test' })}>📱 MOBILE</button>
                                    <button className={`modal-tab ${modalData.type === 'Web Test' ? 'active' : ''}`} onClick={() => setModalData({ ...modalData, type: 'Web Test' })}>🌐 WEB</button>
                                    <button className={`modal-tab ${modalData.type === 'Javascript File' ? 'active' : ''}`} onClick={() => setModalData({ ...modalData, type: 'Javascript File' })}>📄 JS</button>
                                </div>
                                <div className="form-group">
                                    <label>Test Name</label>
                                    <div className="input-with-suffix">
                                        <input
                                            placeholder="e.g. login_flow"
                                            value={modalData.name}
                                            onChange={(e) => setModalData({ ...modalData, name: e.target.value })}
                                        />
                                        <span>.yaml</span>
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label>App Identifier</label>
                                    <div style={{ display: 'flex', gap: '8px' }}>
                                        <div style={{ flex: 1, position: 'relative' }}>
                                            <input
                                                type="text"
                                                placeholder={deviceConnected ? "Search or type app ID..." : "Device is not connected"}
                                                value={modalData.appId}
                                                onChange={(e) => {
                                                    setModalData({ ...modalData, appId: e.target.value });
                                                    setShowPackageDropdown(true);
                                                }}
                                                onFocus={() => setShowPackageDropdown(true)}
                                                onBlur={() => setTimeout(() => setShowPackageDropdown(false), 300)}
                                                onKeyDown={(e) => {
                                                    if (e.key === 'Enter') {
                                                        e.preventDefault();
                                                        const filtered = packages.filter(pkg => pkg.toLowerCase().includes((modalData.appId || '').toLowerCase()));
                                                        if (filtered.length > 0) {
                                                            setModalData({ ...modalData, appId: filtered[0] });
                                                            setShowPackageDropdown(false);
                                                        }
                                                    }
                                                }}
                                                disabled={!deviceConnected}
                                                style={{
                                                    width: '100%',
                                                    padding: '8px 12px',
                                                    background: 'rgba(0,0,0,0.3)',
                                                    border: '1px solid var(--border)',
                                                    borderRadius: '6px',
                                                    color: '#fff',
                                                    fontSize: '12px'
                                                }}
                                            />
                                            {showPackageDropdown && deviceConnected && packages.length > 0 && (
                                                <div style={{
                                                    position: 'absolute',
                                                    top: '100%',
                                                    left: 0,
                                                    right: 0,
                                                    maxHeight: '200px',
                                                    overflowY: 'auto',
                                                    background: 'var(--bg-secondary)',
                                                    border: '1px solid var(--border)',
                                                    borderRadius: '6px',
                                                    marginTop: '4px',
                                                    zIndex: 1000,
                                                    boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
                                                }} className="custom-scrollbar">
                                                    {packages
                                                        .filter(pkg => pkg.toLowerCase().includes((modalData.appId || '').toLowerCase()))
                                                        .slice(0, 50)
                                                        .map(pkg => (
                                                            <div
                                                                key={pkg}
                                                                onMouseDown={() => {
                                                                    setModalData({ ...modalData, appId: pkg });
                                                                    setShowPackageDropdown(false);
                                                                }}
                                                                style={{
                                                                    padding: '8px 12px',
                                                                    cursor: 'pointer',
                                                                    fontSize: '11px',
                                                                    borderBottom: '1px solid var(--border)',
                                                                    transition: 'background 0.2s'
                                                                }}
                                                                onMouseEnter={(e) => e.target.style.background = 'rgba(16, 185, 129, 0.1)'}
                                                                onMouseLeave={(e) => e.target.style.background = 'transparent'}
                                                            >
                                                                {pkg}
                                                            </div>
                                                        ))}
                                                </div>
                                            )}
                                        </div>
                                        <button className="btn btn-secondary" onClick={fetchPackages} title="Refresh Packages" disabled={!deviceConnected}>🔄</button>
                                    </div>
                                </div>
                            </div>
                            <div className="modal-preview">
                                <div style={{ fontSize: '10px', color: 'var(--accent)', marginBottom: '12px', fontWeight: 700, letterSpacing: '0.1em' }}>PREVIEW</div>
                                <pre>
                                    {`appId: ${modalData.appId}\n---\n- launchApp:\n    clearState: true`}
                                </pre>
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                            <button className="btn btn-primary" onClick={createTestFlow} disabled={!modalData.name}>Create Test</button>
                        </div>
                    </div>
                </div>
            )}
            {showSettings && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.8)', zIndex: 2000,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    backdropFilter: 'blur(5px)'
                }}>
                    <div style={{
                        background: 'var(--bg-secondary)', padding: '24px',
                        borderRadius: '16px', border: '1px solid var(--border)',
                        width: '400px',
                        boxShadow: '0 20px 50px rgba(0,0,0,0.5)'
                    }}>
                        <h3 style={{ margin: '0 0 16px 0', fontSize: '18px', fontWeight: 600 }}>Settings</h3>

                        <div style={{ marginBottom: '20px' }}>
                            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#888', marginBottom: '8px' }}>
                                OpenAI API Key
                            </label>
                            <input
                                type="password"
                                value={apiKey}
                                onChange={(e) => setApiKey(e.target.value)}
                                placeholder="sk-..."
                                style={{
                                    width: '100%',
                                    background: 'rgba(0,0,0,0.3)',
                                    border: '1px solid var(--border)',
                                    borderRadius: '8px',
                                    padding: '10px',
                                    color: '#fff',
                                    fontSize: '13px',
                                    outline: 'none'
                                }}
                            />
                            <p style={{ fontSize: '11px', color: '#666', marginTop: '6px' }}>
                                Required for AI Auto-Generation features. Stored locally.
                            </p>
                        </div>

                        <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                            <button
                                onClick={() => setShowSettings(false)}
                                style={{
                                    background: 'transparent', border: '1px solid var(--border)',
                                    color: '#fff', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer'
                                }}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={() => {
                                    localStorage.setItem('openai_api_key', apiKey);
                                    setShowSettings(false);
                                    addLog('success', 'Settings saved successfully');
                                }}
                                style={{
                                    background: 'var(--accent)', border: 'none',
                                    color: '#fff', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 600
                                }}
                            >
                                Save Settings
                            </button>
                        </div>
                    </div>
                </div>
            )}
            {/* Delete Confirmation Modal */}
            {fileToDelete && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.8)', zIndex: 2000,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    backdropFilter: 'blur(5px)'
                }}>
                    <div style={{
                        background: 'var(--bg-secondary)', padding: '24px',
                        borderRadius: '16px', border: '1px solid var(--border)',
                        width: '350px',
                        boxShadow: '0 20px 50px rgba(0,0,0,0.5)',
                        textAlign: 'center'
                    }}>
                        <h3 style={{ margin: '0 0 16px 0', fontSize: '18px', fontWeight: 600, color: 'var(--danger)' }}>Delete File?</h3>
                        <p style={{ color: '#aaa', marginBottom: '24px' }}>
                            Are you sure you want to delete <strong>{fileToDelete.name}</strong>?<br />
                            This action cannot be undone.
                        </p>
                        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
                            <button className="btn btn-secondary" onClick={() => setFileToDelete(null)}>Cancel</button>
                            <button className="btn" style={{ background: 'var(--danger)', color: 'white', border: 'none' }} onClick={confirmDelete}>Delete</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Rename Modal */}
            {fileToRename && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.8)', zIndex: 2000,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    backdropFilter: 'blur(5px)'
                }}>
                    <div style={{
                        background: 'var(--bg-secondary)', padding: '24px',
                        borderRadius: '16px', border: '1px solid var(--border)',
                        width: '350px',
                        boxShadow: '0 20px 50px rgba(0,0,0,0.5)'
                    }}>
                        <h3 style={{ margin: '0 0 16px 0', fontSize: '18px', fontWeight: 600 }}>Rename File</h3>
                        <input
                            type="text"
                            value={renameValue}
                            onChange={(e) => setRenameValue(e.target.value)}
                            placeholder="New filename"
                            autoFocus
                            style={{
                                width: '100%',
                                background: 'rgba(0,0,0,0.3)',
                                border: '1px solid var(--border)',
                                borderRadius: '8px',
                                padding: '12px',
                                color: '#fff',
                                marginBottom: '20px',
                                outline: 'none'
                            }}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter') confirmRename();
                                if (e.key === 'Escape') setFileToRename(null);
                            }}
                        />
                        <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                            <button className="btn btn-secondary" onClick={() => setFileToRename(null)}>Cancel</button>
                            <button className="btn btn-primary" onClick={confirmRename}>Rename</button>
                        </div>
                    </div>
                </div>
            )}
            {/* New Folder Modal */}
            {showNewFolderModal && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.8)', zIndex: 2000,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    backdropFilter: 'blur(5px)'
                }}>
                    <div style={{
                        background: 'var(--bg-secondary)', padding: '24px',
                        borderRadius: '16px', border: '1px solid var(--border)',
                        width: '350px',
                        boxShadow: '0 20px 50px rgba(0,0,0,0.5)'
                    }}>
                        <h3 style={{ margin: '0 0 16px 0', fontSize: '18px', fontWeight: 600 }}>Create New Folder</h3>
                        <input
                            type="text"
                            value={newFolderName}
                            onChange={(e) => setNewFolderName(e.target.value)}
                            placeholder="Folder Name"
                            autoFocus
                            style={{
                                width: '100%',
                                background: 'rgba(0,0,0,0.3)',
                                border: '1px solid var(--border)',
                                borderRadius: '8px',
                                padding: '12px',
                                color: '#fff',
                                marginBottom: '20px',
                                outline: 'none'
                            }}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                    if (newFolderName) {
                                        fetch(`${apiBaseUrl}/files`, {
                                            method: 'POST',
                                            headers: { 'Content-Type': 'application/json' },
                                            body: JSON.stringify({ path: newFolderName, type: 'folder' })
                                        })
                                            .then(() => {
                                                fetchFiles();
                                                setShowNewFolderModal(false);
                                                setNewFolderName('');
                                            })
                                            .catch(err => addLog('error', `Failed to create folder: ${err.message}`));
                                    }
                                }
                                if (e.key === 'Escape') setShowNewFolderModal(false);
                            }}
                        />
                        <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                            <button className="btn btn-secondary" onClick={() => setShowNewFolderModal(false)}>Cancel</button>
                            <button className="btn btn-primary" onClick={() => {
                                if (newFolderName) {
                                    fetch(`${apiBaseUrl}/files`, {
                                        method: 'POST',
                                        headers: { 'Content-Type': 'application/json' },
                                        body: JSON.stringify({ path: newFolderName, type: 'folder' })
                                    })
                                        .then(() => {
                                            fetchFiles();
                                            setShowNewFolderModal(false);
                                            setNewFolderName('');
                                        })
                                        .catch(err => addLog('error', `Failed to create folder: ${err.message}`));
                                }
                            }}>Create</button>
                        </div>
                    </div>
                </div>
            )}

            {/* AI Report Modal */}
            {showReportModal && currentReport && (
                <div
                    style={{
                        position: 'fixed',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        background: 'rgba(0, 0, 0, 0.85)',
                        backdropFilter: 'blur(8px)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        zIndex: 10000,
                        animation: 'fadeIn 0.2s ease-out'
                    }}
                    onClick={() => setShowReportModal(false)}
                >
                    <div
                        style={{
                            background: 'linear-gradient(135deg, rgba(22, 22, 24, 0.98) 0%, rgba(15, 15, 17, 0.98) 100%)',
                            border: '1px solid rgba(255, 255, 255, 0.1)',
                            borderRadius: '24px',
                            maxWidth: '720px',
                            width: '90%',
                            maxHeight: '85vh',
                            overflow: 'hidden',
                            boxShadow: '0 40px 80px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.05)',
                            animation: 'slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
                            display: 'flex',
                            flexDirection: 'column'
                        }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        {/* Modal Header */}
                        <div style={{
                            padding: '28px 32px 24px',
                            borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
                            background: 'linear-gradient(180deg, rgba(255, 255, 255, 0.02) 0%, transparent 100%)'
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                    <div style={{
                                        width: '40px',
                                        height: '40px',
                                        borderRadius: '12px',
                                        background: currentReport.summary.status === 'PASS'
                                            ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
                                            : 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        fontSize: '20px'
                                    }}>{currentReport.summary.status === 'PASS' ? '✓' : '✗'}</div>
                                    <div>
                                        <div style={{ fontSize: '20px', fontWeight: 800, color: '#fff', letterSpacing: '-0.02em' }}>
                                            Test Report
                                        </div>
                                        <div style={{ fontSize: '12px', color: '#888', marginTop: '2px' }}>
                                            {currentReport.summary.test_name}
                                        </div>
                                    </div>
                                </div>
                                <button
                                    onClick={() => setShowReportModal(false)}
                                    style={{
                                        width: '32px',
                                        height: '32px',
                                        borderRadius: '8px',
                                        border: '1px solid rgba(255, 255, 255, 0.1)',
                                        background: 'rgba(255, 255, 255, 0.03)',
                                        color: '#888',
                                        cursor: 'pointer',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        fontSize: '18px',
                                        transition: 'all 0.2s'
                                    }}
                                    onMouseEnter={(e) => {
                                        e.target.style.background = 'rgba(255, 255, 255, 0.08)';
                                        e.target.style.color = '#fff';
                                    }}
                                    onMouseLeave={(e) => {
                                        e.target.style.background = 'rgba(255, 255, 255, 0.03)';
                                        e.target.style.color = '#888';
                                    }}
                                >×</button>
                            </div>

                            {/* Summary Stats */}
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
                                <div style={{
                                    background: 'rgba(255, 255, 255, 0.03)',
                                    border: '1px solid rgba(255, 255, 255, 0.08)',
                                    borderRadius: '12px',
                                    padding: '14px',
                                    textAlign: 'center'
                                }}>
                                    <div style={{ fontSize: '10px', color: '#888', marginBottom: '6px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Total Steps</div>
                                    <div style={{ fontSize: '20px', fontWeight: 800, color: '#fff' }}>{currentReport.summary.total_steps}</div>
                                </div>

                                <div style={{
                                    background: 'rgba(16, 185, 129, 0.08)',
                                    border: '1px solid rgba(16, 185, 129, 0.2)',
                                    borderRadius: '12px',
                                    padding: '14px',
                                    textAlign: 'center'
                                }}>
                                    <div style={{ fontSize: '10px', color: '#888', marginBottom: '6px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Passed</div>
                                    <div style={{ fontSize: '20px', fontWeight: 800, color: '#10b981' }}>{currentReport.summary.passed_steps}</div>
                                </div>

                                <div style={{
                                    background: currentReport.summary.failed_steps > 0 ? 'rgba(239, 68, 68, 0.08)' : 'rgba(255, 255, 255, 0.03)',
                                    border: currentReport.summary.failed_steps > 0 ? '1px solid rgba(239, 68, 68, 0.2)' : '1px solid rgba(255, 255, 255, 0.08)',
                                    borderRadius: '12px',
                                    padding: '14px',
                                    textAlign: 'center'
                                }}>
                                    <div style={{ fontSize: '10px', color: '#888', marginBottom: '6px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Failed</div>
                                    <div style={{ fontSize: '20px', fontWeight: 800, color: currentReport.summary.failed_steps > 0 ? '#ef4444' : '#666' }}>
                                        {currentReport.summary.failed_steps}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Modal Body */}
                        <div style={{
                            flex: 1,
                            overflowY: 'auto',
                            padding: '24px 32px'
                        }}>
                            {/* Failure Details */}
                            {currentReport.failure_details && currentReport.failure_details.length > 0 && (
                                <div style={{ marginBottom: '28px' }}>
                                    <div style={{
                                        fontSize: '11px',
                                        fontWeight: 800,
                                        color: '#ef4444',
                                        textTransform: 'uppercase',
                                        letterSpacing: '0.08em',
                                        marginBottom: '14px',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '8px'
                                    }}>
                                        <span style={{ fontSize: '16px' }}>⚠️</span>
                                        What Failed
                                    </div>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                        {currentReport.failure_details.map((failure, i) => (
                                            <div key={i} style={{
                                                background: 'rgba(239, 68, 68, 0.05)',
                                                border: '1px solid rgba(239, 68, 68, 0.2)',
                                                borderLeft: '4px solid #ef4444',
                                                borderRadius: '8px',
                                                padding: '16px 18px'
                                            }}>
                                                <div style={{ fontSize: '13px', fontWeight: 700, color: '#fff', marginBottom: '8px' }}>
                                                    Step: {failure.failed_step}
                                                </div>
                                                <div style={{ fontSize: '12px', color: '#ef4444', marginBottom: '6px' }}>
                                                    ❌ {failure.reason}
                                                </div>
                                                {failure.details && (
                                                    <div style={{ fontSize: '11px', color: '#999', fontStyle: 'italic', marginTop: '8px', paddingTop: '8px', borderTop: '1px solid rgba(255, 255, 255, 0.05)' }}>
                                                        {failure.details}
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Recommendation */}
                            {currentReport.recommendation && (
                                <div style={{ marginBottom: '28px' }}>
                                    <div style={{
                                        fontSize: '11px',
                                        fontWeight: 800,
                                        color: '#888',
                                        textTransform: 'uppercase',
                                        letterSpacing: '0.08em',
                                        marginBottom: '14px'
                                    }}>Next Steps</div>
                                    <div style={{
                                        background: currentReport.summary.status === 'PASS'
                                            ? 'rgba(16, 185, 129, 0.05)'
                                            : 'rgba(59, 130, 246, 0.05)',
                                        border: currentReport.summary.status === 'PASS'
                                            ? '1px solid rgba(16, 185, 129, 0.2)'
                                            : '1px solid rgba(59, 130, 246, 0.2)',
                                        borderLeft: currentReport.summary.status === 'PASS'
                                            ? '4px solid #10b981'
                                            : '4px solid #3b82f6',
                                        borderRadius: '8px',
                                        padding: '16px 18px',
                                        fontSize: '13px',
                                        color: '#ddd',
                                        lineHeight: '1.6'
                                    }}>
                                        {currentReport.recommendation}
                                    </div>
                                </div>
                            )}

                            {/* Execution Steps */}
                            <div>
                                <div style={{
                                    fontSize: '11px',
                                    fontWeight: 800,
                                    color: '#888',
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.08em',
                                    marginBottom: '14px'
                                }}>Step-by-Step Execution</div>
                                <div style={{
                                    background: 'rgba(255, 255, 255, 0.02)',
                                    border: '1px solid rgba(255, 255, 255, 0.08)',
                                    borderRadius: '12px',
                                    overflow: 'hidden'
                                }}>
                                    {currentReport.execution_steps && currentReport.execution_steps.map((step, i) => (
                                        <div key={i} style={{
                                            padding: '12px 16px',
                                            borderBottom: i === currentReport.execution_steps.length - 1 ? 'none' : '1px solid rgba(255, 255, 255, 0.05)',
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '12px',
                                            background: step.status === 'FAIL' ? 'rgba(239, 68, 68, 0.03)' : 'transparent'
                                        }}>
                                            <div style={{
                                                width: '24px',
                                                height: '24px',
                                                borderRadius: '6px',
                                                background: step.status === 'SUCCESS'
                                                    ? 'rgba(16, 185, 129, 0.15)'
                                                    : 'rgba(239, 68, 68, 0.15)',
                                                color: step.status === 'SUCCESS' ? '#10b981' : '#ef4444',
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                fontSize: '12px',
                                                fontWeight: 700,
                                                flexShrink: 0
                                            }}>
                                                {step.status === 'SUCCESS' ? '✓' : '✗'}
                                            </div>
                                            <div style={{ flex: 1, minWidth: 0 }}>
                                                <div style={{ fontSize: '12px', color: '#ddd', fontWeight: 500 }}>
                                                    {step.action}
                                                </div>
                                            </div>
                                            <div style={{ fontSize: '10px', color: '#666', fontFamily: 'JetBrains Mono, monospace' }}>
                                                {step.time_ms}ms
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Modal Footer */}
                        <div style={{
                            padding: '20px 32px',
                            borderTop: '1px solid rgba(255, 255, 255, 0.08)',
                            background: 'rgba(0, 0, 0, 0.2)',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center'
                        }}>
                            <div style={{ fontSize: '11px', color: '#666' }}>
                                Duration: <span style={{ color: '#888', fontWeight: 600 }}>{currentReport.summary.duration_seconds}s</span>
                                <span style={{ margin: '0 8px', color: '#444' }}>•</span>
                                Run ID: <span style={{ color: '#888', fontFamily: 'JetBrains Mono, monospace' }}>{currentReport.summary.run_id}</span>
                            </div>
                            <div style={{ display: 'flex', gap: '12px' }}>
                                <button
                                    onClick={async () => {
                                        if (confirm('Are you sure you want to delete this test run?')) {
                                            try {
                                                await fetch(`${apiBaseUrl}/report/${currentReport.summary.run_id}`, {
                                                    method: 'DELETE'
                                                });
                                                setShowReportModal(false);
                                                fetchIntelligence(); // Refresh the list
                                            } catch (err) {
                                                console.error('Failed to delete run:', err);
                                            }
                                        }
                                    }}
                                    style={{
                                        background: 'rgba(239, 68, 68, 0.1)',
                                        border: '1px solid rgba(239, 68, 68, 0.3)',
                                        borderRadius: '8px',
                                        padding: '10px 20px',
                                        color: '#ef4444',
                                        fontSize: '13px',
                                        fontWeight: 600,
                                        cursor: 'pointer',
                                        transition: 'all 0.2s'
                                    }}
                                    onMouseEnter={(e) => {
                                        e.target.style.background = 'rgba(239, 68, 68, 0.2)';
                                        e.target.style.borderColor = 'rgba(239, 68, 68, 0.5)';
                                    }}
                                    onMouseLeave={(e) => {
                                        e.target.style.background = 'rgba(239, 68, 68, 0.1)';
                                        e.target.style.borderColor = 'rgba(239, 68, 68, 0.3)';
                                    }}
                                >Delete</button>
                                <button
                                    onClick={() => setShowReportModal(false)}
                                    style={{
                                        background: currentReport.summary.status === 'PASS'
                                            ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
                                            : 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
                                        border: 'none',
                                        borderRadius: '8px',
                                        padding: '10px 24px',
                                        color: '#fff',
                                        fontSize: '13px',
                                        fontWeight: 600,
                                        cursor: 'pointer',
                                        transition: 'all 0.2s'
                                    }}
                                    onMouseEnter={(e) => {
                                        e.target.style.transform = 'translateY(-1px)';
                                        e.target.style.boxShadow = currentReport.summary.status === 'PASS'
                                            ? '0 8px 16px rgba(16, 185, 129, 0.3)'
                                            : '0 8px 16px rgba(59, 130, 246, 0.3)';
                                    }}
                                    onMouseLeave={(e) => {
                                        e.target.style.transform = 'translateY(0)';
                                        e.target.style.boxShadow = 'none';
                                    }}
                                >Close</button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default App;
