import AppSectionState, {
    AppSectionDeleteState,
    AppSectionSaveState,
  } from 'App/State/AppSectionState';
  import Column from 'Components/Table/Column';
  import { SortDirection } from 'Helpers/Props/sortDirections';
  import Media from 'Media/Media';
  import { Filter, FilterBuilderProp } from './AppState';


export interface MediaIndexAppState {
    sortKey: string;
    sortDirection: SortDirection;
    secondarySortKey: string;
    secondarySortDirection: SortDirection;
    view: string;
  
    posterOptions: {
      detailedProgressBar: boolean;
      size: string;
      showTitle: boolean;
      showMonitored: boolean;
      showQualityProfile: boolean;
      showTags: boolean;
      showSearchAction: boolean;
    };
  
    overviewOptions: {
      detailedProgressBar: boolean;
      size: string;
      showMonitored: boolean;
      showNetwork: boolean;
      showQualityProfile: boolean;
      showPreviousAiring: boolean;
      showAdded: boolean;
      showSeasonCount: boolean;
      showPath: boolean;
      showSizeOnDisk: boolean;
      showTags: boolean;
      showSearchAction: boolean;
    };
  
    tableOptions: {
      showBanners: boolean;
      showSearchAction: boolean;
    };
  
    selectedFilterKey: string;
    filterBuilderProps: FilterBuilderProp<Media>[];
    filters: Filter[];
    columns: Column[];
  }
  
  interface MediaAppState
    extends AppSectionState<Media>,
      AppSectionDeleteState,
      AppSectionSaveState {
    itemMap: Record<number, number>;
  
    deleteOptions: {
      addImportListExclusion: boolean;
    };
  
    pendingChanges: Partial<Media>;
  }
  
  export default MediaAppState;