import React from 'react';
import Header from './Header';
import Sidebar from './Sidebar';
import ErrorBoundary from '../common/ErrorBoundary';

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = React.memo(({ children }) => {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
      <Header />
      <div className="flex h-[calc(100vh-4rem)]">
        <Sidebar />
        <main
          className="flex-1 overflow-auto focus:outline-none"
          role="main"
          tabIndex={-1}
        >
          <ErrorBoundary>
            <div className="p-6">
              {children}
            </div>
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
});

MainLayout.displayName = 'MainLayout';

export default MainLayout;