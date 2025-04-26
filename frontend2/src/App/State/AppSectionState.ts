export interface AppSectionItemState<T> {
    isFetching: boolean;
    isPopulated: boolean;
    error: Error;
    pendingChanges: Partial<T>;
    item: T;
  }