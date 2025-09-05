import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, Video, Map, Settings, ChevronLeft, ChevronRight } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';
import { toggleSidebar } from '../../store/slices/appSlice';

interface SidebarProps {
  className?: string;
}

const sidebarItems = [
  {
    path: '/',
    label: '首頁',
    icon: Home,
  },
  {
    path: '/video',
    label: '影片分析',
    icon: Video,
  },
  {
    path: '/mindmap',
    label: '心智圖',
    icon: Map,
  },
  {
    path: '/settings',
    label: '設定',
    icon: Settings,
  },
];

const Sidebar: React.FC<SidebarProps> = React.memo(({ className = '' }) => {
  const dispatch = useAppDispatch();
  const { sidebarCollapsed } = useAppSelector((state) => state.app);
  const location = useLocation();

  const handleToggleSidebar = () => {
    dispatch(toggleSidebar());
  };

  return (
    <aside
      className={`${className} bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 transition-all duration-300 ease-in-out ${
        sidebarCollapsed ? 'w-16' : 'w-64'
      }`}
      aria-label="主要導航"
    >
      <div className="flex flex-col h-full">
        <div className="flex items-center justify-end p-3 border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={handleToggleSidebar}
            className="p-1 rounded-md hover:bg-gray-200 dark:hover:bg-gray-800 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label={sidebarCollapsed ? '展開側邊欄' : '收合側邊欄'}
          >
            {sidebarCollapsed ? (
              <ChevronRight className="w-4 h-4 text-gray-600 dark:text-gray-300" />
            ) : (
              <ChevronLeft className="w-4 h-4 text-gray-600 dark:text-gray-300" />
            )}
          </button>
        </div>

        <nav className="flex-1 p-3" role="navigation">
          <ul className="space-y-2">
            {sidebarItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;

              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      isActive
                        ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                        : 'text-gray-700 hover:bg-gray-200 dark:text-gray-300 dark:hover:bg-gray-800'
                    }`}
                    aria-current={isActive ? 'page' : undefined}
                  >
                    <Icon className={`${sidebarCollapsed ? 'w-5 h-5' : 'w-4 h-4 mr-3'} flex-shrink-0`} />
                    {!sidebarCollapsed && (
                      <span className="truncate">{item.label}</span>
                    )}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </div>
    </aside>
  );
});

Sidebar.displayName = 'Sidebar';

export default Sidebar;