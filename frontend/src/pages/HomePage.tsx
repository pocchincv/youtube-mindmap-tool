import React from 'react';
import { Youtube, Map, Zap } from 'lucide-react';

const HomePage: React.FC = React.memo(() => {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
          YouTube 心智圖工具
        </h1>
        <p className="text-xl text-gray-600 dark:text-gray-300">
          將 YouTube 影片內容轉換為互動式心智圖，提升學習效率
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-8 mb-12">
        <div className="text-center p-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex justify-center mb-4">
            <Youtube className="w-12 h-12 text-red-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            影片分析
          </h3>
          <p className="text-gray-600 dark:text-gray-300">
            輸入 YouTube 影片連結，系統自動分析影片內容和結構
          </p>
        </div>

        <div className="text-center p-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex justify-center mb-4">
            <Map className="w-12 h-12 text-blue-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            心智圖生成
          </h3>
          <p className="text-gray-600 dark:text-gray-300">
            自動生成結構化心智圖，清晰呈現影片重點和關聯性
          </p>
        </div>

        <div className="text-center p-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex justify-center mb-4">
            <Zap className="w-12 h-12 text-yellow-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            智慧學習
          </h3>
          <p className="text-gray-600 dark:text-gray-300">
            互動式學習體驗，提升知識理解和記憶效果
          </p>
        </div>
      </div>

      <div className="text-center">
        <a
          href="/video"
          className="inline-flex items-center px-6 py-3 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
        >
          開始分析影片
        </a>
      </div>
    </div>
  );
});

HomePage.displayName = 'HomePage';

export default HomePage;