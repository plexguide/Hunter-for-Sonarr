import {
    useCallback,
    useEffect,
    useRef,
    useState,
  } from 'react';
  import { useDispatch, useSelector } from 'react-redux';
  import { SelectProvider } from 'App/SelectContext';
  import PageContent from 'Components/Page/PageContent';
  import PageContentBody from 'Components/Page/PageContentBody';
  import MediaAppState, { MediaIndexAppState } from 'App/State/MediaAppState';
  import NoMedia from 'Media/NoMedia';
  import { align, icons, kinds } from 'Helpers/Props';
  import { DESCENDING } from 'Helpers/Props/sortDirections';
  import translate from 'Utilities/String/translate';
  import withScrollPosition from 'Components/withScrollPosition';
  import MediaIndexFooter from './MediaIndexFooter';
  import styles from './MediaIndex.scss';
  
  function getViewComponent(view: string) {
    return MediaIndexTable;
  }
  
  interface MediaIndexProps {
    initialScrollTop?: number;
  }
  
  const MediaIndex = withScrollPosition((props: MediaIndexProps) => {
    const {
      isPopulated,
      error,
      totalItems,
      items,
      sortKey,
      sortDirection,
      view,
    }: MediaAppState & MediaIndexAppState & ClientSideCollectionAppState =
      useSelector(createMediaClientSideCollectionItemsSelector('mediaIndex'));
  
    const { isSmallScreen } = useSelector(createDimensionsSelector());
    const dispatch = useDispatch();
    const scrollerRef = useRef<HTMLDivElement>(null);
    const [isOptionsModalOpen, setIsOptionsModalOpen] = useState(false);
    const [jumpToCharacter, setJumpToCharacter] = useState<string | undefined>(
      undefined
    );
    const [isSelectMode, setIsSelectMode] = useState(false);
  
    useEffect(() => {
      dispatch(fetchMedia());
      dispatch(fetchQueueDetails({ all: true }));
    }, [dispatch]);
  
    const onRssSyncPress = useCallback(() => {
      dispatch(
        executeCommand({
          name: RSS_SYNC,
        })
      );
    }, [dispatch]);
  
    const onSelectModePress = useCallback(() => {
      setIsSelectMode(!isSelectMode);
    }, [isSelectMode, setIsSelectMode]);
  
    const onTableOptionChange = useCallback(
      (payload: unknown) => {
        dispatch(setMediaTableOption(payload));
      },
      [dispatch]
    );
  
    const onViewSelect = useCallback(
      (value: string) => {
        dispatch(setMediaView({ view: value }));
  
        if (scrollerRef.current) {
          scrollerRef.current.scrollTo(0, 0);
        }
      },
      [scrollerRef, dispatch]
    );
  
    const onSortSelect = useCallback(
      (value: string) => {
        dispatch(setMediaSort({ sortKey: value }));
      },
      [dispatch]
    );
  
    const onFilterSelect = useCallback(
      (value: string | number) => {
        dispatch(setMediaFilter({ selectedFilterKey: value }));
      },
      [dispatch]
    );
  
    const onOptionsPress = useCallback(() => {
      setIsOptionsModalOpen(true);
    }, [setIsOptionsModalOpen]);
  
    const onOptionsModalClose = useCallback(() => {
      setIsOptionsModalOpen(false);
    }, [setIsOptionsModalOpen]);
  
  
    const onJumpBarItemPress = useCallback(
      (character: string) => {
        setJumpToCharacter(character);
      },
      [setJumpToCharacter]
    );
  
    const onScroll = useCallback(
      ({ scrollTop }: { scrollTop: number }) => {
        setJumpToCharacter(undefined);
        scrollPositions.seriesIndex = scrollTop;
      },
      [setJumpToCharacter]
    );
  
  
    const isLoaded = !!(!error && isPopulated && items.length);

  
    return (
      <SelectProvider items={items}>
        <PageContent>
          <div className={styles.pageContentBodyWrapper}>
            <PageContentBody
              ref={scrollerRef}
              className={styles.contentBody}
              // eslint-disable-next-line @typescript-eslint/ban-ts-comment
              // @ts-ignore
              innerClassName={styles[`${view}InnerContentBody`]}
              initialScrollTop={props.initialScrollTop}
            >

  
  
              {isLoaded ? (
                <div className={styles.contentBodyContainer}>
                  <ViewComponent
                    scrollerRef={scrollerRef}
                    items={items}
                    sortKey={sortKey}
                    sortDirection={sortDirection}
                    jumpToCharacter={jumpToCharacter}
                    isSelectMode={isSelectMode}
                    isSmallScreen={isSmallScreen}
                  />
  
                  <MediaIndexFooter />
                </div>
              ) : null}
  
              {!error && isPopulated && !items.length ? (
                <NoMedia totalItems={totalItems} />
              ) : null}
              <NoMedia />
            </PageContentBody>
          </div>
        
        </PageContent>
      </SelectProvider>
    );
  }, 'mediaIndex');
  
  export default MediaIndex;