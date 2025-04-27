import Button from 'Components/Link/Button';
import { kinds } from 'Helpers/Props';
import translate from 'Utilities/String/translate';
import styles from './NoMedia.css';

interface NoMediaProps {
  totalItems: number;
}

function NoMedia(props: NoMediaProps) {
  const { totalItems } = props;

  if (totalItems > 0) {
    return (
      <div>
        <div className={styles.message}>
          {translate('AllMediaAreHiddenByTheAppliedFilter')}
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className={styles.message}>
        {translate('NoMediaFoundImportOrAdd')}
      </div>

      <div className={styles.buttonContainer}>
        <Button to="/add/import" kind={kinds.PRIMARY}>
          {translate('ImportExistingMedia')}
        </Button>
      </div>

      <div className={styles.buttonContainer}>
        <Button to="/add/new" kind={kinds.PRIMARY}>
          {translate('AddNewMedia')}
        </Button>
      </div>
    </div>
  );
}

export default NoMedia;