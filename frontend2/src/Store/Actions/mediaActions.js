import _ from 'lodash';
import { createAction } from 'redux-actions';
import { batchActions } from 'redux-batched-actions';
import { filterBuilderTypes, filterBuilderValueTypes, filterTypes, sortDirections } from 'Helpers/Props';
import getFilterTypePredicate from 'Helpers/Props/getFilterTypePredicate';
import { createThunk, handleThunks } from 'Store/thunks';
import sortByProp from 'Utilities/Array/sortByProp';
import createAjaxRequest from 'Utilities/createAjaxRequest';
import translate from 'Utilities/String/translate';
import { set, updateItem } from './baseActions';



//
// Local

const MONITOR_TIMEOUT = 1000;
const seasonsToUpdate = {};
const seasonMonitorToggleTimeouts = {};

//
// Variables

export const section = 'media';

export const filters = [
  {
    key: 'all',
    label: () => translate('All'),
    filters: []
  },
  {
    key: 'monitored',
    label: () => translate('MonitoredOnly'),
    filters: [
      {
        key: 'monitored',
        value: true,
        type: filterTypes.EQUAL
      }
    ]
  },
  {
    key: 'unmonitored',
    label: () => translate('UnmonitoredOnly'),
    filters: [
      {
        key: 'monitored',
        value: false,
        type: filterTypes.EQUAL
      }
    ]
  },
  {
    key: 'continuing',
    label: () => translate('ContinuingOnly'),
    filters: [
      {
        key: 'status',
        value: 'continuing',
        type: filterTypes.EQUAL
      }
    ]
  },
  {
    key: 'ended',
    label: () => translate('EndedOnly'),
    filters: [
      {
        key: 'status',
        value: 'ended',
        type: filterTypes.EQUAL
      }
    ]
  },
  {
    key: 'missing',
    label: () => translate('MissingEpisodes'),
    filters: [
      {
        key: 'missing',
        value: true,
        type: filterTypes.EQUAL
      }
    ]
  }
];

export const filterPredicates = {
  episodeProgress: function(item, filterValue, type) {
    const { statistics = {} } = item;

    const {
      episodeCount = 0,
      episodeFileCount
    } = statistics;

    const progress = episodeCount ?
      episodeFileCount / episodeCount * 100 :
      100;

    const predicate = getFilterTypePredicate(type);

    return predicate(progress, filterValue);
  },

  missing: function(item) {
    const { statistics = {} } = item;

    return statistics.episodeCount - statistics.episodeFileCount > 0;
  },

  nextAiring: function(item, filterValue, type) {
    return dateFilterPredicate(item.nextAiring, filterValue, type);
  },

  previousAiring: function(item, filterValue, type) {
    return dateFilterPredicate(item.previousAiring, filterValue, type);
  },

  added: function(item, filterValue, type) {
    return dateFilterPredicate(item.added, filterValue, type);
  },

  ratings: function(item, filterValue, type) {
    const predicate = getFilterTypePredicate(type);
    const { value = 0 } = item.ratings;

    return predicate(value * 10, filterValue);
  },

  ratingVotes: function(item, filterValue, type) {
    const predicate = getFilterTypePredicate(type);
    const { votes = 0 } = item.ratings;

    return predicate(votes, filterValue);
  },

  originalLanguage: function(item, filterValue, type) {
    const predicate = getFilterTypePredicate(type);
    const { originalLanguage } = item;

    return predicate(originalLanguage ? originalLanguage.name : '', filterValue);
  },

  releaseGroups: function(item, filterValue, type) {
    const { statistics = {} } = item;

    const {
      releaseGroups = []
    } = statistics;

    const predicate = getFilterTypePredicate(type);

    return predicate(releaseGroups, filterValue);
  },

  seasonCount: function(item, filterValue, type) {
    const predicate = getFilterTypePredicate(type);
    const seasonCount = item.statistics ? item.statistics.seasonCount : 0;

    return predicate(seasonCount, filterValue);
  },

  sizeOnDisk: function(item, filterValue, type) {
    const predicate = getFilterTypePredicate(type);
    const sizeOnDisk = item.statistics && item.statistics.sizeOnDisk ?
      item.statistics.sizeOnDisk :
      0;

    return predicate(sizeOnDisk, filterValue);
  },

  hasMissingSeason: function(item, filterValue, type) {
    const predicate = getFilterTypePredicate(type);
    const { seasons = [] } = item;

    const hasMissingSeason = seasons.some((season) => {
      const {
        seasonNumber,
        statistics = {}
      } = season;

      const {
        episodeFileCount = 0,
        episodeCount = 0,
        totalEpisodeCount = 0
      } = statistics;

      return (
        seasonNumber > 0 &&
        totalEpisodeCount > 0 &&
        episodeCount === totalEpisodeCount &&
        episodeFileCount === 0
      );
    });

    return predicate(hasMissingSeason, filterValue);
  },

  seasonsMonitoredStatus: function(item, filterValue, type) {
    const predicate = getFilterTypePredicate(type);
    const { seasons = [] } = item;

    const { monitoredCount, unmonitoredCount } = seasons.reduce((acc, { seasonNumber, monitored }) => {
      if (seasonNumber <= 0) {
        return acc;
      }

      if (monitored) {
        acc.monitoredCount++;
      } else {
        acc.unmonitoredCount++;
      }

      return acc;
    }, { monitoredCount: 0, unmonitoredCount: 0 });

    let seasonsMonitoredStatus = 'partial';

    if (monitoredCount === 0) {
      seasonsMonitoredStatus = 'none';
    } else if (unmonitoredCount === 0) {
      seasonsMonitoredStatus = 'all';
    }

    return predicate(seasonsMonitoredStatus, filterValue);
  }
};

export const filterBuilderProps = [
  {
    name: 'monitored',
    label: () => translate('Monitored'),
    type: filterBuilderTypes.EXACT,
    valueType: filterBuilderValueTypes.BOOL
  },
  {
    name: 'status',
    label: () => translate('Status'),
    type: filterBuilderTypes.EXACT,
    valueType: filterBuilderValueTypes.MEDIA_STATUS
  },
  {
    name: 'mediaType',
    label: () => translate('Type'),
    type: filterBuilderTypes.EXACT,
    valueType: filterBuilderValueTypes.MEDIA_TYPES
  },
  {
    name: 'title',
    label: () => translate('Title'),
    type: filterBuilderTypes.STRING
  },
  {
    name: 'network',
    label: () => translate('Network'),
    type: filterBuilderTypes.ARRAY,
    optionsSelector: function(items) {
      const tagList = items.reduce((acc, media) => {
        if (media.network) {
          acc.push({
            id: media.network,
            name: media.network
          });
        }

        return acc;
      }, []);

      return tagList.sort(sortByProp('name'));
    }
  },
  {
    name: 'qualityProfileId',
    label: () => translate('QualityProfile'),
    type: filterBuilderTypes.EXACT,
    valueType: filterBuilderValueTypes.QUALITY_PROFILE
  },
  {
    name: 'nextAiring',
    label: () => translate('NextAiring'),
    type: filterBuilderTypes.DATE,
    valueType: filterBuilderValueTypes.DATE
  },
  {
    name: 'previousAiring',
    label: () => translate('PreviousAiring'),
    type: filterBuilderTypes.DATE,
    valueType: filterBuilderValueTypes.DATE
  },
  {
    name: 'added',
    label: () => translate('Added'),
    type: filterBuilderTypes.DATE,
    valueType: filterBuilderValueTypes.DATE
  },
  {
    name: 'seasonCount',
    label: () => translate('SeasonCount'),
    type: filterBuilderTypes.NUMBER
  },
  {
    name: 'episodeProgress',
    label: () => translate('EpisodeProgress'),
    type: filterBuilderTypes.NUMBER
  },
  {
    name: 'path',
    label: () => translate('Path'),
    type: filterBuilderTypes.STRING
  },
  {
    name: 'rootFolderPath',
    label: () => translate('RootFolderPath'),
    type: filterBuilderTypes.EXACT
  },
  {
    name: 'sizeOnDisk',
    label: () => translate('SizeOnDisk'),
    type: filterBuilderTypes.NUMBER,
    valueType: filterBuilderValueTypes.BYTES
  },
  {
    name: 'genres',
    label: () => translate('Genres'),
    type: filterBuilderTypes.ARRAY,
    optionsSelector: function(items) {
      const tagList = items.reduce((acc, media) => {
        media.genres.forEach((genre) => {
          acc.push({
            id: genre,
            name: genre
          });
        });

        return acc;
      }, []);

      return tagList.sort(sortByProp('name'));
    }
  },
  {
    name: 'originalLanguage',
    label: () => translate('OriginalLanguage'),
    type: filterBuilderTypes.EXACT,
    optionsSelector: function(items) {
      const languageList = items.reduce((acc, media) => {
        if (media.originalLanguage) {
          acc.push({
            id: media.originalLanguage.name,
            name: media.originalLanguage.name
          });
        }

        return acc;
      }, []);

      return languageList.sort(sortByProp('name'));
    }
  },
  {
    name: 'releaseGroups',
    label: () => translate('ReleaseGroups'),
    type: filterBuilderTypes.ARRAY
  },
  {
    name: 'ratings',
    label: () => translate('Rating'),
    type: filterBuilderTypes.NUMBER
  },
  {
    name: 'ratingVotes',
    label: () => translate('RatingVotes'),
    type: filterBuilderTypes.NUMBER
  },
  {
    name: 'certification',
    label: () => translate('Certification'),
    type: filterBuilderTypes.EXACT
  },
  {
    name: 'tags',
    label: () => translate('Tags'),
    type: filterBuilderTypes.ARRAY,
    valueType: filterBuilderValueTypes.TAG
  },
  {
    name: 'useSceneNumbering',
    label: () => translate('SceneNumbering'),
    type: filterBuilderTypes.EXACT
  },
  {
    name: 'hasMissingSeason',
    label: () => translate('HasMissingSeason'),
    type: filterBuilderTypes.EXACT,
    valueType: filterBuilderValueTypes.BOOL
  },
  {
    name: 'seasonsMonitoredStatus',
    label: () => translate('SeasonsMonitoredStatus'),
    type: filterBuilderTypes.EXACT,
    valueType: filterBuilderValueTypes.SEASONS_MONITORED_STATUS
  },
  {
    name: 'year',
    label: () => translate('Year'),
    type: filterBuilderTypes.NUMBER
  }
];

export const sortPredicates = {
  status: function(item) {
    let result = 0;

    if (item.monitored) {
      result += 2;
    }

    if (item.status === 'continuing') {
      result++;
    }

    return result;
  },

  sizeOnDisk: function(item) {
    const { statistics = {} } = item;

    return statistics.sizeOnDisk || 0;
  }
};

//
// State

export const defaultState = {
  isFetching: false,
  isPopulated: false,
  error: null,
  isSaving: false,
  saveError: null,
  isDeleting: false,
  deleteError: null,
  items: [],
  sortKey: 'sortTitle',
  sortDirection: sortDirections.ASCENDING,
  pendingChanges: {},
  deleteOptions: {
    addImportListExclusion: false
  }
};

export const persistState = [
  'media.deleteOptions'
];

//
// Actions Types

export const FETCH_MEDIA = 'media/fetchMedia';
export const SET_MEDIA_VALUE = 'media/setMediaValue';
export const SAVE_MEDIA = 'media/saveMedia';
export const DELETE_MEDIA = 'media/deleteMedia';

export const TOGGLE_MEDIA_MONITORED = 'media/toggleMediaMonitored';
export const TOGGLE_SEASON_MONITORED = 'media/toggleSeasonMonitored';
export const UPDATE_MEDIA_MONITOR = 'media/updateMediaMonitor';
export const SAVE_MEDIA_EDITOR = 'media/saveMediaEditor';
export const BULK_DELETE_MEDIA = 'media/bulkDeleteMedia';

export const SET_DELETE_OPTION = 'media/setDeleteOption';

//
// Action Creators

export const fetchMedia = createThunk(FETCH_MEDIA);
export const saveMedia = createThunk(SAVE_MEDIA, (payload) => {
  const newPayload = {
    ...payload
  };

  if (payload.moveFiles) {
    newPayload.queryParams = {
      moveFiles: true
    };
  }

  delete newPayload.moveFiles;

  return newPayload;
});

export const deleteMedia = createThunk(DELETE_MEDIA, (payload) => {
  return {
    ...payload,
    queryParams: {
      deleteFiles: payload.deleteFiles,
      addImportListExclusion: payload.addImportListExclusion
    }
  };
});

export const toggleMediaMonitored = createThunk(TOGGLE_MEDIA_MONITORED);
export const toggleSeasonMonitored = createThunk(TOGGLE_SEASON_MONITORED);
export const updateMediaMonitor = createThunk(UPDATE_MEDIA_MONITOR);
export const saveMediaEditor = createThunk(SAVE_MEDIA_EDITOR);
export const bulkDeleteMedia = createThunk(BULK_DELETE_MEDIA);

export const setMediaValue = createAction(SET_MEDIA_VALUE, (payload) => {
  return {
    section,
    ...payload
  };
});

export const setDeleteOption = createAction(SET_DELETE_OPTION);

//
// Helpers

function getSaveAjaxOptions({ ajaxOptions, payload }) {
  if (payload.moveFolder) {
    ajaxOptions.url = `${ajaxOptions.url}?moveFolder=true`;
  }

  return ajaxOptions;
}

//
// Action Handlers

export const actionHandlers = handleThunks({

  [FETCH_MEDIA]: createFetchHandler(section, '/media'),
  [SAVE_MEDIA]: createSaveProviderHandler(section, '/media', { getAjaxOptions: getSaveAjaxOptions }),
  [DELETE_MEDIA]: createRemoveItemHandler(section, '/media'),

  [TOGGLE_MEDIA_MONITORED]: (getState, payload, dispatch) => {
    const {
      mediaId: id,
      monitored
    } = payload;

    const media = _.find(getState().media.items, { id });

    dispatch(updateItem({
      id,
      section,
      isSaving: true
    }));

    const promise = createAjaxRequest({
      url: `/media/${id}`,
      method: 'PUT',
      data: JSON.stringify({
        ...media,
        monitored
      }),
      dataType: 'json'
    }).request;

    promise.done((data) => {
      dispatch(updateItem({
        id,
        section,
        isSaving: false,
        monitored
      }));
    });

    promise.fail((xhr) => {
      dispatch(updateItem({
        id,
        section,
        isSaving: false
      }));
    });
  },

  [TOGGLE_SEASON_MONITORED]: function(getState, payload, dispatch) {
    const {
      mediaId: id,
      seasonNumber,
      monitored
    } = payload;

    const seasonMonitorToggleTimeout = seasonMonitorToggleTimeouts[id];

    if (seasonMonitorToggleTimeout) {
      clearTimeout(seasonMonitorToggleTimeout);
      delete seasonMonitorToggleTimeouts[id];
    }

    const media = getState().media.items.find((s) => s.id === id);
    const seasons = _.cloneDeep(media.seasons);
    const season = seasons.find((s) => s.seasonNumber === seasonNumber);

    season.isSaving = true;

    dispatch(updateItem({
      id,
      section,
      seasons
    }));

    seasonsToUpdate[seasonNumber] = monitored;
    season.monitored = monitored;

    seasonMonitorToggleTimeouts[id] = setTimeout(() => {
      createAjaxRequest({
        url: `/media/${id}`,
        method: 'PUT',
        data: JSON.stringify({
          ...media,
          seasons
        }),
        dataType: 'json'
      }).request.then(
        (data) => {
          const changedSeasons = [];

          data.seasons.forEach((s) => {
            if (seasonsToUpdate.hasOwnProperty(s.seasonNumber)) {
              if (s.monitored === seasonsToUpdate[s.seasonNumber]) {
                changedSeasons.push(s);
              } else {
                s.isSaving = true;
              }
            }
          });

          const episodesToUpdate = getState().episodes.items.reduce((acc, episode) => {
            if (episode.mediaId !== data.id) {
              return acc;
            }

            const changedSeason = changedSeasons.find((s) => s.seasonNumber === episode.seasonNumber);

            if (!changedSeason) {
              return acc;
            }

            acc.push(updateItem({
              id: episode.id,
              section: 'episodes',
              monitored: changedSeason.monitored
            }));

            return acc;
          }, []);

          dispatch(batchActions([
            updateItem({
              id,
              section,
              ...data
            }),

            ...episodesToUpdate
          ]));

          changedSeasons.forEach((s) => {
            delete seasonsToUpdate[s.seasonNumber];
          });
        },
        (xhr) => {
          dispatch(updateItem({
            id,
            section,
            seasons: media.seasons
          }));

          Object.keys(seasonsToUpdate).forEach((s) => {
            delete seasonsToUpdate[s];
          });
        });
    }, MONITOR_TIMEOUT);
  },

  [UPDATE_MEDIA_MONITOR]: function(getState, payload, dispatch) {
    const {
      mediaIds,
      monitor,
      monitored,
      shouldFetchEpisodesAfterUpdate = false
    } = payload;

    const media = [];

    mediaIds.forEach((id) => {
      const mediaToUpdate = { id };

      if (monitored != null) {
        mediaToUpdate.monitored = monitored;
      }

      media.push(mediaToUpdate);
    });

    dispatch(set({
      section,
      isSaving: true
    }));

    const promise = createAjaxRequest({
      url: '/seasonPass',
      method: 'POST',
      data: JSON.stringify({
        media,
        monitoringOptions: { monitor }
      }),
      dataType: 'json'
    }).request;

    promise.done((data) => {
      if (shouldFetchEpisodesAfterUpdate) {
        dispatch(fetchEpisodes({ mediaId: mediaIds[0] }));
      }

      dispatch(set({
        section,
        isSaving: false,
        saveError: null
      }));
    });

    promise.fail((xhr) => {
      dispatch(set({
        section,
        isSaving: false,
        saveError: xhr
      }));
    });
  },

  [SAVE_MEDIA_EDITOR]: function(getState, payload, dispatch) {
    dispatch(set({
      section,
      isSaving: true
    }));

    const promise = createAjaxRequest({
      url: '/media/editor',
      method: 'PUT',
      data: JSON.stringify(payload),
      dataType: 'json'
    }).request;

    promise.done((data) => {
      dispatch(batchActions([
        ...data.map((media) => {

          const {
            alternateTitles,
            images,
            rootFolderPath,
            statistics,
            ...propsToUpdate
          } = media;

          return updateItem({
            id: media.id,
            section: 'media',
            ...propsToUpdate
          });
        }),

        set({
          section,
          isSaving: false,
          saveError: null
        })
      ]));
    });

    promise.fail((xhr) => {
      dispatch(set({
        section,
        isSaving: false,
        saveError: xhr
      }));
    });
  },

  [BULK_DELETE_MEDIA]: function(getState, payload, dispatch) {
    dispatch(set({
      section,
      isDeleting: true
    }));

    const promise = createAjaxRequest({
      url: '/media/editor',
      method: 'DELETE',
      data: JSON.stringify(payload),
      dataType: 'json'
    }).request;

    promise.done(() => {
      // SignaR will take care of removing the media from the collection

      dispatch(set({
        section,
        isDeleting: false,
        deleteError: null
      }));
    });

    promise.fail((xhr) => {
      dispatch(set({
        section,
        isDeleting: false,
        deleteError: xhr
      }));
    });
  }
});

//
// Reducers

export const reducers = createHandleActions({

  [SET_MEDIA_VALUE]: createSetSettingValueReducer(section),

  [SET_DELETE_OPTION]: (state, { payload }) => {
    return {
      ...state,
      deleteOptions: {
        ...payload
      }
    };
  }

}, defaultState, section);