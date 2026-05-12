export const TIMEOUT_AUTH = 8_000   // auth, heartbeat, logout
export const TIMEOUT_STD  = 10_000  // appels standard (profil, activités, admin)
export const TIMEOUT_GROQ = 45_000  // génération Groq, OCR, mail-groupe, purge BDD

export const MSG_TIMEOUT = 'Connexion lente ou indisponible. Vérifiez votre réseau et réessayez.'

export async function fetchWithTimeout(url, options = {}, timeout = TIMEOUT_STD) {
  const controller = new AbortController()
  const id = setTimeout(() => controller.abort(), timeout)
  try {
    return await fetch(url, { ...options, signal: controller.signal })
  } catch (err) {
    if (err.name === 'AbortError') throw new Error(MSG_TIMEOUT)
    throw err
  } finally {
    clearTimeout(id)
  }
}
