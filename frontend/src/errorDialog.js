let _handler = null

export function registerErrorHandler(fn) {
  _handler = fn
}

export function showError(msg) {
  if (_handler) _handler(msg)
}
