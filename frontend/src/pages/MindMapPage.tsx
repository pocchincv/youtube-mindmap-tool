import React from 'react';
import LoadingSpinner from '../components/ui/LoadingSpinner';

const MindMapPage: React.FC = React.memo(() => {
  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-8">
        心智圖
      </h1>
      
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-8">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            功能開發中
          </h2>
          <p className="text-gray-600 dark:text-gray-300 mb-6">
            心智圖功能正在開發中，敬請期待...
          </p>
          <LoadingSpinner size="lg" message="準備中..." />
        </div>
      </div>
    </div>
  );
});

MindMapPage.displayName = 'MindMapPage';

export default MindMapPage;