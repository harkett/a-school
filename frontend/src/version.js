import { version } from '../package.json'

export const APP_VERSION = import.meta.env.MODE === 'development'
  ? `${version}-dev`
  : version
