import { useLocation, useParams, useNavigationType, NavigationType } from 'react-router-dom';
import scrollPositions from 'Store/scrollPositions';

export function useScrollPosition(scrollPositionKey: string) {
  const location = useLocation();
  const params = useParams();
  const navigationType = useNavigationType(); // 'POP', 'PUSH', 'REPLACE'

  const initialScrollTop =
    navigationType === 'POP' ? scrollPositions[scrollPositionKey] : 0;

  return {
    location,
    params,
    navigationType,
    initialScrollTop,
  };
}
