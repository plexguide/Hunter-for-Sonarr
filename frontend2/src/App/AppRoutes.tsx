import React from 'react';
import { Navigate, Route } from 'react-router-dom';
import RouteSwitch from 'Components/Router/RouteSwitch';
import getPathWithUrlBase from 'Utilities/getPathWithUrlBase';
import MediaIndex from 'Media/Index/MediaIndex';
import NotFound from 'Components/NotFound';
import Settings from 'Settings/Settings';

function RedirectWithUrlBase() {
  return <Navigate to={getPathWithUrlBase('/')} />;
}
console.log('AppRoutes');
function AppRoutes() {
  return (
    <RouteSwitch>
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
      <Route path="/" element={<NotFound />} />

      {/*
        Settings
      */}

      <Route path="/settings" element={<Settings />} />
      <Route path="/media" element={<MediaIndex />} />

      {/*
        Not Found
      */}

      <Route path="*" element={<NotFound />} />
    </RouteSwitch>
  );
}

export default AppRoutes;