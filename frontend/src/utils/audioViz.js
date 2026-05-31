// Fonctions pures du visualiseur de volume de la dictée vocale.
// Isolées ici (sans React ni DOM) pour être testables sans navigateur.

// Formate une durée en secondes vers "m:ss" (ex. 4 -> "0:04", 83 -> "1:23").
// Robuste : valeurs négatives / nulles / non définies -> "0:00".
export function formatTime(totalSeconds) {
  const s = Math.max(0, Math.floor(totalSeconds || 0))
  const m = Math.floor(s / 60)
  const sec = s % 60
  return `${m}:${String(sec).padStart(2, '0')}`
}

// Convertit les données de fréquence de l'AnalyserNode (Uint8Array, valeurs 0..255)
// en `nBars` niveaux normalisés 0..1, en moyennant les bins par paquets égaux.
// Robuste : entrée vide / absente -> tableau de nBars zéros.
export function computeBarLevels(freqData, nBars = 12) {
  const n = Math.max(1, nBars | 0)
  const out = new Array(n).fill(0)
  if (!freqData || !freqData.length) return out
  const binsPerBar = Math.max(1, Math.floor(freqData.length / n))
  for (let b = 0; b < n; b++) {
    const start = b * binsPerBar
    const end = Math.min(freqData.length, start + binsPerBar)
    let sum = 0
    let count = 0
    for (let i = start; i < end; i++) { sum += freqData[i]; count++ }
    const avg = count ? sum / count : 0
    out[b] = Math.min(1, Math.max(0, avg / 255))
  }
  return out
}
