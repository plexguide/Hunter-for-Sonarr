import React from 'react';
import { SelectProvider } from 'App/SelectContext';
import PageContent from 'Components/Page/PageContent';
import PageContentBody from 'Components/Page/PageContentBody';
import NoMedia from 'Media/NoMedia';
import MediaIndexFooter from './MediaIndexFooter';
import styles from './MediaIndex.scss';


function MediaIndex() {


  return (
    <SelectProvider items={items}>
      <PageContent>
          <PageContentBody>
            <NoMedia />
            <MediaIndexFooter />
          </PageContentBody>
      </PageContent>
    </SelectProvider>
  );
};

export default MediaIndex;