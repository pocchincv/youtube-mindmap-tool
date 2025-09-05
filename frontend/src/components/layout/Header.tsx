import React from 'react';
import { Menu, Sun, Moon, Youtube } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';
import { toggleSidebar } from '../../store/slices/appSlice';
import { useTheme } from '../../hooks/useTheme';

const Header: React.FC = React.memo(() => {
  const dispatch = useAppDispatch();
  const { sidebarCollapsed } = useAppSelector((state) => state.app);
  const { theme, toggleTheme } = useTheme();

  const handleToggleSidebar = () => {
    dispatch(toggleSidebar());
  };

  return (
    <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 h-16 flex items-center justify-between px-4 transition-colors">
      <div className="flex items-center space-x-4">
        <button
          onClick={handleToggleSidebar}
          className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label={sidebarCollapsed ? '展開側邊欄' : '收合側邊欄'}
          aria-expanded={!sidebarCollapsed}
        >
          <Menu className="w-5 h-5 text-gray-600 dark:text-gray-300" />
        </button>
        
        <div className="flex items-center space-x-2">
          <Youtube className="w-6 h-6 text-red-600" />
          <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
            YouTube 心智圖工具
          </h1>
        </div>
      </div>

      <div className="flex items-center space-x-2">
        <button
          onClick={toggleTheme}
          className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label={theme === 'light' ? '切換到深色模式' : '切換到淺色模式'}
        >
          {theme === 'light' ? (
            <Moon className="w-5 h-5 text-gray-600 dark:text-gray-300" />
          ) : (
            <Sun className="w-5 h-5 text-gray-600 dark:text-gray-300" />
          )}
        </button>
      </div>
    </header>
  );
});

Header.displayName = 'Header';

export default Header;