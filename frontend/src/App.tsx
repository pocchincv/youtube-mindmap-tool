import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store';
import MainLayout from './components/layout/MainLayout';
import ErrorBoundary from './components/common/ErrorBoundary';
import HomePage from './pages/HomePage';
import VideoPage from './pages/VideoPage';
import MindMapPage from './pages/MindMapPage';
import SettingsPage from './pages/SettingsPage';
import NotFoundPage from './pages/NotFoundPage';

const App: React.FC = () => {
  return (
    <Provider store={store}>
      <ErrorBoundary>
        <Router>
          <Routes>
            <Route path="/" element={
              <MainLayout>
                <HomePage />
              </MainLayout>
            } />
            <Route path="/video" element={
              <MainLayout>
                <VideoPage />
              </MainLayout>
            } />
            <Route path="/mindmap" element={
              <MainLayout>
                <MindMapPage />
              </MainLayout>
            } />
            <Route path="/settings" element={
              <MainLayout>
                <SettingsPage />
              </MainLayout>
            } />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Router>
      </ErrorBoundary>
    </Provider>
  );
};

export default App;
