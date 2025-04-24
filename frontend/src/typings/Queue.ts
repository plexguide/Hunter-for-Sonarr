import ModelBase from 'App/ModelBase';
import Episode from 'Episode/Episode';
import Language from 'Language/Language';


export type QueueTrackedDownloadStatus = 'ok' | 'warning' | 'error';

export type QueueTrackedDownloadState =
  | 'downloading'
  | 'importBlocked'
  | 'importPending'
  | 'importing'
  | 'imported'
  | 'failedPending'
  | 'failed'
  | 'ignored';

export interface StatusMessage {
  title: string;
  messages: string[];
}

interface Queue extends ModelBase {
  languages: Language[];
  customFormatScore: number;
  size: number;
  title: string;
  sizeleft: number;
  timeleft: string;
  estimatedCompletionTime: string;
  added?: string;
  status: string;
  trackedDownloadStatus: QueueTrackedDownloadStatus;
  trackedDownloadState: QueueTrackedDownloadState;
  statusMessages: StatusMessage[];
  errorMessage: string;
  downloadId: string;
  downloadClient: string;
  outputPath: string;
  episodeHasFile: boolean;
  seriesId?: number;
  episodeId?: number;
  seasonNumber?: number;
  downloadClientHasPostImportCategory: boolean;
  episode?: Episode;
}

export default Queue;