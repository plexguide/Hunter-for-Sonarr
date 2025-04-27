import React from 'react';
import { useScrollPosition } from 'Helpers/Hooks/useScrollPosition'; // or wherever you put it

interface WrappedComponentProps {
  initialScrollTop: number;
}

function withScrollPosition(
  WrappedComponent: React.FC<WrappedComponentProps>,
  scrollPositionKey: string
) {
  function ScrollPosition(props: {}) {
    const { initialScrollTop } = useScrollPosition(scrollPositionKey);

    return <WrappedComponent {...props} initialScrollTop={initialScrollTop} />;
  }

  return ScrollPosition;
}

export default withScrollPosition;
