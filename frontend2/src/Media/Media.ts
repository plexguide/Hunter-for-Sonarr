import ModelBase from 'App/ModelBase';
import Language from 'Language/Language';

export type MediaType = 'anime' | 'daily' | 'standard';
export type MediaMonitor =
  | 'all'
  | 'future'
  | 'missing'
  | 'existing'
  | 'recent'
  | 'pilot'
  | 'firstSeason'
  | 'lastSeason'
  | 'monitorSpecials'
  | 'unmonitorSpecials'
  | 'none';

export type MediaStatus = 'continuing' | 'ended' | 'upcoming' | 'deleted';

export type MonitorNewItems = 'all' | 'none';

export type CoverType = 'poster' | 'banner' | 'fanart' | 'season';

export interface Image {
  coverType: CoverType;
  url: string;
  remoteUrl: string;
}

export interface Statistics {
  seasonCount: number;
  episodeCount: number;
  episodeFileCount: number;
  percentOfEpisodes: number;
  previousAiring?: Date;
  releaseGroups: string[];
  sizeOnDisk: number;
  totalEpisodeCount: number;
  lastAired?: string;
}

export interface Season {
  monitored: boolean;
  seasonNumber: number;
  statistics: Statistics;
  isSaving?: boolean;
}

export interface Ratings {
  votes: number;
  value: number;
}

export interface AlternateTitle {
  seasonNumber: number;
  sceneSeasonNumber?: number;
  title: string;
  sceneOrigin: 'unknown' | 'unknown:tvdb' | 'mixed' | 'tvdb';
  comment?: string;
}

export interface MediaAddOptions {
  monitor: MediaMonitor;
  searchForMissingEpisodes: boolean;
  searchForCutoffUnmetEpisodes: boolean;
}

interface Media extends ModelBase {
  added: string;
  alternateTitles: AlternateTitle[];
  certification: string;
  cleanTitle: string;
  ended: boolean;
  firstAired: string;
  genres: string[];
  images: Image[];
  imdbId?: string;
  monitored: boolean;
  monitorNewItems: MonitorNewItems;
  network: string;
  originalLanguage: Language;
  overview: string;
  path: string;
  previousAiring?: string;
  nextAiring?: string;
  qualityProfileId: number;
  ratings: Ratings;
  rootFolderPath: string;
  runtime: number;
  seasonFolder: boolean;
  seasons: Season[];
  seriesType: MediaType;
  sortTitle: string;
  statistics?: Statistics;
  status: MediaStatus;
  tags: number[];
  title: string;
  titleSlug: string;
  tvdbId: number;
  tvMazeId: number;
  tvRageId: number;
  tmdbId: number;
  useSceneNumbering: boolean;
  year: number;
  isSaving?: boolean;
  addOptions: MediaAddOptions;
}

export default Media;