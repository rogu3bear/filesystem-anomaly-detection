import React, { useEffect, useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box, CircularProgress } from '@mui/material';
import { useAuthStore } from './store/authStore';

// Lazy load pages
const Layout = React.lazy(() => import('./components/Layout/Layout'));
const Login = React.lazy(() => import('./pages/Auth/Login'));
const Register = React.lazy(() => import('./pages/Auth/Register'));
const Dashboard = React.lazy(() => import('./pages/Dashboard/Dashboard'));
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
