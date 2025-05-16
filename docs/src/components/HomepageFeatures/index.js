import React from 'react';
import clsx from 'clsx';
import styles from './styles.module.css';

const FeatureList = [
  {
    title: 'Find Missing Content',
    description: (
      <>
        Huntarr intelligently scans your library to discover missing content and initiates searches to fill the gaps.
      </>
    ),
  },
  {
    title: 'Quality Upgrades',
    description: (
      <>
        Automatically search for better quality versions of your existing media based on your quality preferences.
      </>
    ),
  },
  {
    title: 'Smart API Management',
    description: (
      <>
        Advanced rate limiting and API management prevent overwhelming your indexers while continuously improving your collection.
      </>
    ),
  },
];

function Feature({title, description}) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center padding-horiz--md">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
} 