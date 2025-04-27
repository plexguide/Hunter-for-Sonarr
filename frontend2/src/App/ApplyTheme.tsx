import { useCallback, useEffect, Component, ReactNode } from 'react';
import useTheme from 'Helpers/Hooks/useTheme';
import themes from 'Styles/Themes';




function ApplyTheme() {
  const theme = useTheme();
  console.log('Apply Theme');
  const updateCSSVariables = useCallback(() => {
    Object.entries(themes[theme]).forEach(([key, value]) => {
      document.documentElement.style.setProperty(`--${key}`, value);
    });
  }, [theme]);

  // On Component Mount and Component Update
  useEffect(() => {
    updateCSSVariables();
  }, [updateCSSVariables, theme]);

  return null;
}

export default ApplyTheme;