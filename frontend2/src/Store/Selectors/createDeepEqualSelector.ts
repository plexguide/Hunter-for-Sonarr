import { createSelectorCreator } from 'reselect';
import { isEqual } from 'lodash';

// Custom memoization function using isEqual for deep comparison
const customMemoize = <T extends (...args: any[]) => any>(func: T): T => {
  let lastArgs: any[] | null = null;
  let lastResult: any = null;

  return ((...args: any[]) => {
    // If args are deeply equal, return the last result
    if (lastArgs && isEqual(args, lastArgs)) {
      return lastResult;
    }

    // Otherwise, compute and store the result
    lastArgs = args;
    lastResult = func(...args);
    return lastResult;
  }) as T;
};

// Create a deep equality selector using the custom memoization
const createDeepEqualSelector = createSelectorCreator(customMemoize);

export default createDeepEqualSelector;
