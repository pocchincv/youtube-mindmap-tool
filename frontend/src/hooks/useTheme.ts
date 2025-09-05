import { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from './redux';
import { setTheme } from '../store/slices/appSlice';

export const useTheme = () => {
  const dispatch = useAppDispatch();
  const theme = useAppSelector((state) => state.app.theme);

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null;
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme) {
      dispatch(setTheme(savedTheme));
    } else if (prefersDark) {
      dispatch(setTheme('dark'));
    }
  }, [dispatch]);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    dispatch(setTheme(theme === 'light' ? 'dark' : 'light'));
  };

  return { theme, toggleTheme };
};