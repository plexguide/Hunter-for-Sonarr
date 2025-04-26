import React from 'react';
import styles from './PageHeader.css';

interface HeaderProps {
  title?: string;
  subtitle?: string;
  logoUrl?: string;
}

const Header: React.FC<HeaderProps> = ({ title = 'My App', subtitle, logoUrl }) => {
  return (
    <header className={styles.header}>
      {logoUrl && <img src={logoUrl} alt="Logo" className={styles.logo} />}
      <div>
        <h1 className={styles.title}>{title}</h1>
        {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
      </div>
    </header>
  );
};

export default Header;
