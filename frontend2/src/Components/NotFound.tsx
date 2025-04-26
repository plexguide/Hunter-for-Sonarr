import PageContent from 'Components/Page/PageContent';
import translate from 'Utilities/String/translate';
import styles from './NotFound.css';

interface NotFoundProps {
  message?: string;
}

function NotFound(props: NotFoundProps) {
  const { message = translate('DefaultNotFoundMessage') } = props;

  return (
    <PageContent title="MIA">
      <div className={styles.container}>
        <div className={styles.message}>{message}</div>

        <img
          className={styles.image}
          src={`${window.Huntarr.urlBase}/Content/Images/404.jpg`}
        />
      </div>
    </PageContent>
  );
}

export default NotFound;