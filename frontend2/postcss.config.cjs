const autoprefixer = require('autoprefixer');
const postcssMixins = require('postcss-mixins');
const postcssSimpleVars = require('postcss-simple-vars');
const postcssColorFunction = require('postcss-color-mix');
const postcssNested = require('postcss-nested');
const path = require('path');
const { pathToFileURL } = require('url');


const cssVarsFiles = [
  './src/Styles/Variables/fonts.cjs',
  './src/Styles/Variables/animations.cjs',
].map((p) => path.resolve(__dirname, p));

const mixinsFiles = [
  'frontend2/src/Styles/Mixins/cover.css',
  'frontend2/src/Styles/Mixins/linkOverlay.css',
  'frontend2/src/Styles/Mixins/scroller.css',
  'frontend2/src/Styles/Mixins/truncate.css'
];


async function loadVars() {
  const variables = {};

  for (const file of cssVarsFiles) {
    const module = await import(pathToFileURL(file));
    Object.assign(variables, module.default ?? module);
  }

  return variables;
}

module.exports = {
  plugins: [
    autoprefixer(),
    postcssMixins({ mixinsFiles }),
    postcssSimpleVars({
      variables: async () => {
        return await loadVars();
      }
    }),
    postcssColorFunction(),
    postcssNested()
  ]
};
