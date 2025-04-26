import React from 'react';
import PageHeader from './Header/PageHeader';




type PageProps = {
  footer?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
};

export default function Page({ footer, children, className = '' }: PageProps) {
  return (
    <div className={`min-h-screen flex flex-col ${className}`}>
      <PageHeader />
    </div>
  );
}
