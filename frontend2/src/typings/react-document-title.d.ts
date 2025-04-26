declare module 'react-document-title' {
    import { ComponentType, ReactNode } from 'react';
  
    interface DocumentTitleProps {
      title: string;
      children?: ReactNode;
    }
  
    const DocumentTitle: ComponentType<DocumentTitleProps>;
  
    export default DocumentTitle;
  }
  