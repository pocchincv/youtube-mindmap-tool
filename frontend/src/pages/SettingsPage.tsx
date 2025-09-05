import React from 'react';
import { useTheme } from '../hooks/useTheme';
import { useAppDispatch, useAppSelector } from '../hooks/redux';
import { setSidebarCollapsed } from '../store/slices/appSlice';

const SettingsPage: React.FC = React.memo(() => {
  const { theme, toggleTheme } = useTheme();
  const dispatch = useAppDispatch();
  const { sidebarCollapsed } = useAppSelector((state) => state.app);

  const handleSidebarToggle = (collapsed: boolean) => {
    dispatch(setSidebarCollapsed(collapsed));
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-8">
        設定
      </h1>

      <div className="space-y-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            外觀設定
          </h2>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  主題
                </label>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  選擇淺色或深色主題
                </p>
              </div>
              <button
                onClick={toggleTheme}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                  theme === 'dark' ? 'bg-blue-600' : 'bg-gray-200'
                }`}
                role="switch"
                aria-checked={theme === 'dark'}
                aria-label="切換主題"
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    theme === 'dark' ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  側邊欄
                </label>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  預設側邊欄狀態
                </p>
              </div>
              <button
                onClick={() => handleSidebarToggle(!sidebarCollapsed)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                  !sidebarCollapsed ? 'bg-blue-600' : 'bg-gray-200'
                }`}
                role="switch"
                aria-checked={!sidebarCollapsed}
                aria-label="切換側邊欄狀態"
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    !sidebarCollapsed ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            系統資訊
          </h2>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-gray-400">版本:</span>
              <span className="text-gray-900 dark:text-white">1.0.0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-gray-400">建置時間:</span>
              <span className="text-gray-900 dark:text-white">{new Date().toLocaleDateString('zh-TW')}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
});

SettingsPage.displayName = 'SettingsPage';

export default SettingsPage;