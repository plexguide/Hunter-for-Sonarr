import { Navigate, Route } from 'react-router-dom';
import Switch from 'Components/Router/Switch';
import getPathWithUrlBase from 'Utilities/getPathWithUrlBase';
import NotFound from 'Components/NotFound';
import Settings from 'Settings/Settings';

function RedirectWithUrlBase() {
  return <Navigate to={getPathWithUrlBase('/')} />;
}

function AppRoutes() {
  return (
    <Switch>
      {/*
       Root
      */}

      {window.Huntarr.urlBase && (
        <Route
          path="/"
          // eslint-disable-next-line @typescript-eslint/ban-ts-comment
          // @ts-ignore
          addUrlBase={false}
          render={RedirectWithUrlBase}
        />
      )}


      {/*
        Settings
      */}

      <Route path="/settings" element={<Settings />} />



      {/*
        System
      */}


      {/*
        Not Found
      */}

      <Route path="*" element={<NotFound />} />
    </Switch>
  );
}

export default AppRoutes;