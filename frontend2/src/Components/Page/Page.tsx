import React, { useCallback, useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import ColorImpairedContext from 'App/ColorImpairedContext';
import AppState from 'App/State/AppState';
import PageHeader from './Header/PageHeader';
import useAppPage from 'Helpers/Hooks/useAppPage';
import { saveDimensions } from 'Store/Actions/appActions';
import createUISettingsSelector from 'Store/Selectors/createUISettingsSelector';
import ErrorPage from './ErrorPage';
import styles  from './Page.module.scss'


interface PageProps {
  children: React.ReactNode;
}

function Page({ children }: PageProps) {
  const dispatch = useDispatch();
  const { enableColorImpairedMode } = useSelector(createUISettingsSelector());
  const { hasError, errors, isLocalStorageSupported } =
  useAppPage();
  const { version } = useSelector(
    (state: AppState) => state.app
  );

  const handleResize = useCallback(() => {
    dispatch(
      saveDimensions({
        width: window.innerWidth,
        height: window.innerHeight,
      })
    );
  }, [dispatch]);

  useEffect(() => {
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [handleResize]);

  if (hasError || !isLocalStorageSupported) {
    return (
      <ErrorPage
        {...errors}
        version={version}
        isLocalStorageSupported={isLocalStorageSupported}
      />
    );
  }
  return (
    <ColorImpairedContext value={enableColorImpairedMode}>
      <PageHeader />

      <div className={styles.main}>
        {children}
      </div>
  </ColorImpairedContext>
  );
}

export default Page;