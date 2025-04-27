import React from 'react';
import PageContent from 'Components/Page/PageContent';
import translate from 'Utilities/String/translate';
import styles from './NotFound.module.css';

interface NotFoundProps {
  message?: string;
}

function NotFound(props: NotFoundProps) {
  const { message = translate('DefaultNotFoundMessage') } = props;
  console.log('NotFound');
  return (
    <PageContent title="MIA">
      <div className={styles.container}>
        <div className={styles.message}>{message}</div>
        <h1>Missing</h1>
        <img
          className={styles.image}
          src={`${window.Huntarr.urlBase}/Images/404.jpg`}
        />
      </div>
    </PageContent>
  );
}

export default NotFound;