import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Huntarr.io',
  tagline: 'The Ultimate Arr Management Tool',
  favicon: 'img/favicon.ico',

  url: 'https://plexguide.github.io',
  baseUrl: '/Huntarr.io/',

  organizationName: 'plexguide',
  projectName: 'Huntarr.io',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          routeBasePath: '/', // This makes docs the main page
        },
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    colorMode: {
      defaultMode: 'dark',
      disableSwitch: false,
      respectPrefersColorScheme: false,
    },
    navbar: {
      title: 'Huntarr.io',
      logo: {
        alt: 'Huntarr.io Logo',
        src: 'img/favicon.ico',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'configurationSidebar',
          position: 'left',
          label: 'Docs',
          activeBasePath: '/docs',
        },
        {
          href: 'https://github.com/plexguide/Huntarr.io',
          label: 'GitHub',
          position: 'right',
        },
        {
          href: 'https://discord.com/invite/PGJJjR5Cww',
          label: 'Discord',
          position: 'right',
        }
      ],
    },
    footer: {
      style: 'dark',
      links: [],
      copyright: `Copyright © ${new Date().getFullYear()} Huntarr.io - Admin9705. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
    // Algolia search configuration removed
  } satisfies Preset.ThemeConfig,
};

export default config;
