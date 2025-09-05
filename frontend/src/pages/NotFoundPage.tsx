import React from 'react';
import { Link } from 'react-router-dom';
import { Home } from 'lucide-react';

const NotFoundPage: React.FC = React.memo(() => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-8 text-center">
        <h1 className="text-6xl font-bold text-gray-400 dark:text-gray-600 mb-4">404</h1>
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
          找不到頁面
        </h2>
        <p className="text-gray-600 dark:text-gray-300 mb-8">
          很抱歉，您要找的頁面不存在或已被移除。
        </p>
        <Link
          to="/"
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
        >
          <Home className="w-4 h-4 mr-2" />
          回到首頁
        </Link>
      </div>
    </div>
  );
});

NotFoundPage.displayName = 'NotFoundPage';

export default NotFoundPage;