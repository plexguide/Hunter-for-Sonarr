import dark from './dark';
import light from './light';


const defaultDark = typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches;
const auto = defaultDark ? dark : light;

const themes = {
  auto,
  light,
  dark,
};

export default themes;
