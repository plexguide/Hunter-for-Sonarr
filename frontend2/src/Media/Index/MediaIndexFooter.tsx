import classNames from 'classnames';
import { useSelector } from 'react-redux';
import { ColorImpairedConsumer } from 'App/ColorImpairedContext';
import { createSelector } from 'reselect';
import MediaAppState from 'App/State/MediaAppState';
import formatBytes from 'Utilities/Number/formatBytes';
import createClientSideCollectionSelector from 'Store/Selectors/createClientSideCollectionSelector';
import createDeepEqualSelector from 'Store/Selectors/createDeepEqualSelector';
import translate from 'Utilities/String/translate';
import './MediaIndexFooter.css';


function createUnoptimizedSelector() {
  return createSelector(
    createClientSideCollectionSelector('series', 'seriesIndex'),
    (media: MediaAppState) => {
      return media.items.map((s) => {
        const { monitored, status, statistics } = s;

        return {
          monitored,
          status,
          statistics,
        };
      });
    }
  );
}

function createMediaSelector() {
  return createDeepEqualSelector(
    createUnoptimizedSelector(),
    (series) => series
  );
}


export default function MediaIndexFooter() {
  const media = useSelector(createMediaSelector());
  const count = media.length;
  let episodes = 0;
  let episodeFiles = 0;
  let ended = 0;
  let continuing = 0;
  let monitored = 0;
  let totalFileSize = 0;

  media.forEach((s) => { 
    const {
      statistics = { episodeCount: 0, episodeFileCount: 0, sizeOnDisk: 0 },
    } = s;

    const {
      episodeCount = 0,
      episodeFileCount = 0,
      sizeOnDisk = 0,
    } = statistics;

    episodes += episodeCount;
    episodeFiles += episodeFileCount;

    if (s.status === 'ended') {
      ended++;
    } else {
      continuing++;
    }

    if (s.monitored) {
      monitored++;
    }

    totalFileSize += sizeOnDisk;
  });

  return (
    <ColorImpairedConsumer>
      {(enableColorImpairedMode) => {
        return (
          <div className={styles.footer}>
            <div>
              <div className={styles.legendItem}>
                <div
                  className={classNames(
                    styles.continuing,
                    enableColorImpairedMode && 'colorImpaired'
                  )}
                />
                <div>{translate('MediaIndexFooterContinuing')}</div>
              </div>

              <div className={styles.legendItem}>
                <div
                  className={classNames(
                    styles.ended,
                    enableColorImpairedMode && 'colorImpaired'
                  )}
                />
                <div>{translate('MediaIndexFooterEnded')}</div>
              </div>

              <div className={styles.legendItem}>
                <div
                  className={classNames(
                    styles.missingMonitored,
                    enableColorImpairedMode && 'colorImpaired'
                  )}
                />
                <div>{translate('MediaIndexFooterMissingMonitored')}</div>
              </div>

              <div className={styles.legendItem}>
                <div
                  className={classNames(
                    styles.missingUnmonitored,
                    enableColorImpairedMode && 'colorImpaired'
                  )}
                />
                <div>{translate('MediaIndexFooterMissingUnmonitored')}</div>
              </div>

              <div className={styles.legendItem}>
                <div
                  className={classNames(
                    styles.downloading,
                    enableColorImpairedMode && 'colorImpaired'
                  )}
                />
                <div>{translate('MediaIndexFooterDownloading')}</div>
              </div>
            </div>

            <div className={styles.statistics}>
              <DescriptionList>
                <DescriptionListItem title={translate('Media')} data={count} />

                <DescriptionListItem title={translate('Ended')} data={ended} />

                <DescriptionListItem
                  title={translate('Continuing')}
                  data={continuing}
                />
              </DescriptionList>

              <DescriptionList>
                <DescriptionListItem
                  title={translate('Monitored')}
                  data={monitored}
                />

                <DescriptionListItem
                  title={translate('Unmonitored')}
                  data={count - monitored}
                />
              </DescriptionList>

              <DescriptionList>
                <DescriptionListItem
                  title={translate('Episodes')}
                  data={episodes}
                />

                <DescriptionListItem
                  title={translate('Files')}
                  data={episodeFiles}
                />
              </DescriptionList>

              <DescriptionList>
                <DescriptionListItem
                  title={translate('TotalFileSize')}
                  data={formatBytes(totalFileSize)}
                />
              </DescriptionList>
            </div>
          </div>
        );
      }}
    </ColorImpairedConsumer>
  );
}