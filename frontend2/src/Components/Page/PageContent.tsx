import React from 'react';
import DocumentTitle from 'react-document-title';
import styles from './PageContent.css';

interface PageContentProps {
  className?: string;
  title?: string;
  children: React.ReactNode;
}

function PageContent({
  className = styles.content,
  title,
  children,
}: PageContentProps) {
  return (
    <DocumentTitle
    title={
        title
        ? `${title} - ${window.Huntarr.instanceName}`
        : window.Huntarr.instanceName
    }
    >
    <div className={className}>{children}</div>
    </DocumentTitle>
  );
}

export default PageContent;