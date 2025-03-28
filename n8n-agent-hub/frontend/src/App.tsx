import React, { useEffect, useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box, CircularProgress, AppBar, Toolbar, Typography, Button } from '@mui/material';
import { useAuthStore } from './store/authStore';
import './App.css';
import ConversationUI from './components/ConversationUI';

// Lazy load pages
const Layout = React.lazy(() => import('./components/Layout/Layout'));
const Login = React.lazy(() => import('./pages/Auth/Login'));
const Register = React.lazy(() => import('./pages/Auth/Register'));
const Dashboard = () => {
  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Filesystem AI Assistant
          </Typography>
          <Button color="inherit">Settings</Button>
          <Button color="inherit" onClick={authStore.logout}>Logout</Button>
        </Toolbar>
      </AppBar>
      <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
        <ConversationUI />
      </Box>
    </Box>
  );
};
const AgentsList = React.lazy(() => import('./pages/Agents/AgentsList'));
const AgentCreate = React.lazy(() => import('./pages/Agents/AgentCreate'));
const AgentEdit = React.lazy(() => import('./pages/Agents/AgentEdit'));
const AgentDetail = React.lazy(() => import('./pages/Agents/AgentDetail'));
const Profile = React.lazy(() => import('./pages/Profile/Profile'));
const NotFound = React.lazy(() => import('./pages/NotFound/NotFound'));

// Protected route component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuthStore();

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  return <>{children}</>;
};

// Setup Wizard Components
const SetupWizard = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [setupStatus, setSetupStatus] = useState<any>({
    loading: true,
    n8nInstalled: false,
    n8nRunning: false,
    configExists: false,
    systemInfo: {}
  });
  const [config, setConfig] = useState({
    sourceDir: '',
    targetDir: '',
    organizeBy: 'extension',
    scanInterval: 300
  });
  const [installOutput, setInstallOutput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [apiKey, setApiKey] = useState('');

  // Fetch initial setup status
  useEffect(() => {
    fetchSetupStatus();
  }, []);

  const fetchSetupStatus = async () => {
    try {
      const response = await fetch('/api/setup/status');
      const data = await response.json();
      setSetupStatus({
        ...data,
        loading: false
      });
      
      // Auto advance to the appropriate step based on status
      if (!data.n8nInstalled) {
        setCurrentStep(0); // Need to install n8n
      } else if (!data.n8nRunning) {
        setCurrentStep(1); // Need to start n8n
      } else if (!data.configExists) {
        setCurrentStep(2); // Need to configure
      } else {
        setCurrentStep(3); // All done
      }
    } catch (error) {
      console.error('Error fetching setup status:', error);
      setSetupStatus({
        loading: false,
        error: 'Failed to fetch setup status'
      });
    }
  };

  const installN8n = async () => {
    setLoading(true);
    setError('');
    setSuccess('');
    setInstallOutput('Installing n8n... This may take a few minutes.');
    
    try {
      const response = await fetch('/api/setup/install-n8n', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      if (data.success) {
        setSuccess('n8n installed successfully!');
        setInstallOutput(data.output || 'Installation completed successfully.');
        await fetchSetupStatus();
        setCurrentStep(1);
      } else {
        setError(data.error || 'Installation failed');
        setInstallOutput(data.errorOutput || 'Installation failed with unknown error.');
      }
    } catch (error) {
      console.error('Installation error:', error);
      setError('Failed to install n8n. See console for details.');
    } finally {
      setLoading(false);
    }
  };

  const startN8n = async () => {
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      const response = await fetch('/api/setup/start-n8n', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      if (data.success) {
        setSuccess('n8n started successfully!');
        setTimeout(async () => {
          await fetchSetupStatus();
          setCurrentStep(2);
        }, 2000);
      } else {
        setError(data.error || 'Failed to start n8n');
      }
    } catch (error) {
      console.error('n8n start error:', error);
      setError('Failed to start n8n. See console for details.');
    } finally {
      setLoading(false);
    }
  };

  const saveConfiguration = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      const response = await fetch('/api/setup/configure', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
      });
      
      const data = await response.json();
      if (data.success) {
        setSuccess('Configuration saved successfully!');
        setApiKey(data.apiKey);
        await fetchSetupStatus();
        setCurrentStep(3);
      } else {
        setError(data.error || 'Failed to save configuration');
      }
    } catch (error) {
      console.error('Configuration error:', error);
      setError('Failed to save configuration. See console for details.');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setConfig({
      ...config,
      [name]: value
    });
  };

  // Render setup steps
  const renderStep = () => {
    switch(currentStep) {
      case 0: // Install n8n
        return (
          <div className="setup-step">
            <h2>Step 1: Install n8n</h2>
            <p>n8n is required for file organization automation.</p>
            
            {!setupStatus.n8nInstalled ? (
              <>
                <button 
                  onClick={installN8n} 
                  disabled={loading}
                  className="primary-button"
                >
                  {loading ? 'Installing...' : 'Install n8n'}
                </button>
                
                {installOutput && (
                  <div className="install-output">
                    <h3>Installation Progress:</h3>
                    <pre>{installOutput}</pre>
                  </div>
                )}
              </>
            ) : (
              <>
                <div className="success-message">
                  <span className="success-icon">✓</span> n8n is already installed
                </div>
                <button 
                  onClick={() => setCurrentStep(1)}
                  className="primary-button"
                >
                  Next: Start n8n
                </button>
              </>
            )}
          </div>
        );
        
      case 1: // Start n8n
        return (
          <div className="setup-step">
            <h2>Step 2: Start n8n</h2>
            <p>n8n needs to be running for file organization to work.</p>
            
            {!setupStatus.n8nRunning ? (
              <button 
                onClick={startN8n} 
                disabled={loading}
                className="primary-button"
              >
                {loading ? 'Starting...' : 'Start n8n'}
              </button>
            ) : (
              <>
                <div className="success-message">
                  <span className="success-icon">✓</span> n8n is already running
                </div>
                <button 
                  onClick={() => setCurrentStep(2)}
                  className="primary-button"
                >
                  Next: Configure
                </button>
              </>
            )}
          </div>
        );
        
      case 2: // Configure
        return (
          <div className="setup-step">
            <h2>Step 3: Configure File Organization</h2>
            <p>Set up source and target directories for your file organization.</p>
            
            <form onSubmit={saveConfiguration}>
              <div className="form-group">
                <label htmlFor="sourceDir">Source Directory:</label>
                <input
                  type="text"
                  id="sourceDir"
                  name="sourceDir"
                  value={config.sourceDir}
                  onChange={handleInputChange}
                  placeholder={`${process.env.HOME}/Downloads`}
                  className="form-control"
                />
                <small>Directory to monitor for new files</small>
              </div>
              
              <div className="form-group">
                <label htmlFor="targetDir">Target Directory:</label>
                <input
                  type="text"
                  id="targetDir"
                  name="targetDir"
                  value={config.targetDir}
                  onChange={handleInputChange}
                  placeholder={`${process.env.HOME}/Organized`}
                  className="form-control"
                />
                <small>Directory where files will be organized</small>
              </div>
              
              <div className="form-group">
                <label htmlFor="organizeBy">Organize By:</label>
                <select
                  id="organizeBy"
                  name="organizeBy"
                  value={config.organizeBy}
                  onChange={handleInputChange}
                  className="form-control"
                >
                  <option value="extension">File Extension</option>
                  <option value="date">Date</option>
                  <option value="type">File Type</option>
                  <option value="size">File Size</option>
                </select>
              </div>
              
              <div className="form-group">
                <label htmlFor="scanInterval">Scan Interval (seconds):</label>
                <input
                  type="number"
                  id="scanInterval"
                  name="scanInterval"
                  value={config.scanInterval}
                  onChange={handleInputChange}
                  min="10"
                  className="form-control"
                />
                <small>How often to check for new files</small>
              </div>
              
              <button 
                type="submit" 
                disabled={loading}
                className="primary-button"
              >
                {loading ? 'Saving...' : 'Save Configuration'}
              </button>
            </form>
          </div>
        );
        
      case 3: // Complete
        return (
          <div className="setup-step">
            <h2>Setup Complete!</h2>
            <div className="success-container">
              <div className="success-icon">✓</div>
              <p>Your Filesystem Anomaly Detection is now configured and ready to use.</p>
            </div>
            
            {apiKey && (
              <div className="api-key-container">
                <h3>Your API Key:</h3>
                <div className="api-key">{apiKey}</div>
                <p className="warning">Keep this key secure! It's required for API access.</p>
              </div>
            )}
            
            <div className="next-steps">
              <h3>Next Steps:</h3>
              <ul>
                <li>Access n8n at: <a href="http://localhost:5678" target="_blank" rel="noopener noreferrer">http://localhost:5678</a></li>
                <li>Access the Filesystem Anomaly Detection dashboard at: <a href="/" onClick={() => window.location.href = '/'}>Dashboard</a></li>
              </ul>
            </div>
            
            <button 
              onClick={() => window.location.href = '/'}
              className="primary-button"
            >
              Go to Dashboard
            </button>
          </div>
        );
        
      default:
        return <div>Unknown step</div>;
    }
  };

  // Loading indicator
  if (setupStatus.loading) {
    return (
      <div className="setup-loading">
        <div className="spinner"></div>
        <p>Loading setup status...</p>
      </div>
    );
  }

  // Main setup wizard component
  return (
    <div className="setup-wizard">
      <header className="setup-header">
        <h1>Filesystem Anomaly Detection Setup</h1>
        <div className="progress-indicator">
          <div className={`step ${currentStep >= 0 ? 'active' : ''} ${setupStatus.n8nInstalled ? 'completed' : ''}`}>1</div>
          <div className={`step ${currentStep >= 1 ? 'active' : ''} ${setupStatus.n8nRunning ? 'completed' : ''}`}>2</div>
          <div className={`step ${currentStep >= 2 ? 'active' : ''} ${setupStatus.configExists ? 'completed' : ''}`}>3</div>
          <div className={`step ${currentStep >= 3 ? 'active' : ''}`}>4</div>
        </div>
      </header>
      
      <main className="setup-content">
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}
        
        {renderStep()}
      </main>
      
      <footer className="setup-footer">
        <p>Filesystem Anomaly Detection | v1.0.0</p>
      </footer>
    </div>
  );
};

const App: React.FC = () => {
  const { checkAuth } = useAuthStore();
  const [appReady, setAppReady] = useState(false);

  useEffect(() => {
    const initApp = async () => {
      await checkAuth();
      setAppReady(true);
    };

    initApp();
  }, [checkAuth]);

  if (!appReady) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <React.Suspense
      fallback={
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
          <CircularProgress />
        </Box>
      }
    >
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/setup" element={<SetupWizard />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="agents">
            <Route index element={<AgentsList />} />
            <Route path="create" element={<AgentCreate />} />
            <Route path=":id" element={<AgentDetail />} />
            <Route path=":id/edit" element={<AgentEdit />} />
          </Route>
          <Route path="profile" element={<Profile />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </React.Suspense>
  );
};

export default App;
