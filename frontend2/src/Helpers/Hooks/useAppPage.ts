import { useEffect, useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { createSelector } from 'reselect';
import AppState from 'App/State/AppState';
import { fetchUISettings } from 'Store/Actions/settingsActions';


const createErrorsSelector = () =>
  createSelector(
    (state: AppState) => state.settings.ui.error,
    (
      uiSettingsError,
    ) => {
      const hasError = !!(
        uiSettingsError
      );

      return {
        hasError,
        errors: {
          uiSettingsError,
        },
      };
    }
  );

const useAppPage = () => {
  const dispatch = useDispatch();

  const isPopulated = useSelector(
    (state: AppState) =>
      state.settings.ui.isPopulated
  );

  const { hasError, errors } = useSelector(createErrorsSelector());

  const isLocalStorageSupported = useMemo(() => {
    const key = 'sonarrTest';

    try {
      localStorage.setItem(key, key);
      localStorage.removeItem(key);

      return true;
    } catch {
      return false;
    }
  }, []);

  useEffect(() => {
    dispatch(fetchUISettings());
  }, [dispatch]);

  return useMemo(() => {
    return { errors, hasError, isLocalStorageSupported, isPopulated };
  }, [errors, hasError, isLocalStorageSupported, isPopulated]);
};

export default useAppPage;