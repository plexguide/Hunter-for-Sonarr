import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import DocumentTitle from 'react-document-title';
import { Provider } from 'react-redux';
import ErrorBoundary from 'Components/Error/ErrorBoundry';
import ApplyTheme from './ApplyTheme';
import AppRoutes from './AppRoutes';
import Page from 'Components/Page/Page';
import { Store } from 'redux';
import './App.css'

const queryClient = new QueryClient(); // Assuming you're initializing a query client

interface AppProps {
  store: Store;
}


  console.log('App');
function App({ store }: AppProps) {
    return (
      <DocumentTitle title={window.Huntarr.instanceName}>
        <QueryClientProvider client={queryClient}>
          <Provider store={store}>
            <BrowserRouter>
                <Page>
                  <AppRoutes />
                </Page>
            </BrowserRouter>
          </Provider>
        </QueryClientProvider>
      </DocumentTitle>
    );
  }

export default App;


