import { ForwardedRef, forwardRef, ReactNode, useCallback } from 'react';
import Scroller, { OnScroll } from 'Components/Scroller/Scroller';
import { isLocked } from 'Utilities/scrollLock';
import styles from './PageContentBody.module.css';

interface PageContentBodyProps {
  className?: string;
  innerClassName?: string;
  children: ReactNode;
  initialScrollTop?: number;
}

const PageContentBody = forwardRef(
  (props: PageContentBodyProps, ref: ForwardedRef<HTMLDivElement>) => {
    const {
      className = styles.contentBody,
      innerClassName = styles.innerContentBody,
      children,
      ...otherProps
    } = props;

    const onScrollWrapper = useCallback(
      (payload: OnScroll) => {
        if (onScroll && !isLocked()) {
          onScroll(payload);
        }
      },
      [onScroll]
    );

    return (
      <Scroller
        ref={ref}
        {...otherProps}
        className={className}
        scrollDirection="vertical"
        onScroll={onScrollWrapper}
      >
        <div className={innerClassName}>{children}</div>
      </Scroller>
    );
  }
);

export default PageContentBody;