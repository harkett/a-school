// « Ce texte ressemble-t-il à du charabia ? » — le garde-fou qui évite de payer un appel pour du
// clavier tapé au hasard. Il vit ici parce qu'il était écrit DEUX fois, mot pour mot, dans les
// deux écrans d'analyse (Ambiguïtés et Consignes) : deux copies d'une même heuristique, qu'une
// correction sur l'une aurait laissée fausse sur l'autre.
//
// L'heuristique : parmi les mots de plus de 8 lettres, ceux dont moins de 15 % des caractères
// sont des voyelles sont suspects. Au-delà d'un quart de mots suspects, c'est du charabia. Elle
// est volontairement grossière — elle ne juge pas la qualité du texte, elle repère « azertyuiop ».
export function isTexteGibberish(t) {
  const words = (t || '').trim().split(/\s+/).filter(w => w.length > 2)
  if (words.length < 2) return false
  const vowels = /[aeiouyàâäéèêëîïôöùûüæœAEIOUYÀÂÄÉÈÊËÎÏÔÖÙÛÜÆŒ]/
  let suspect = 0
  for (const word of words) {
    const alpha = word.replace(/[^a-zA-ZÀ-ÿ]/g, '')
    if (alpha.length > 8) {
      const vRatio = alpha.split('').filter(c => vowels.test(c)).length / alpha.length
      if (vRatio < 0.15) suspect++
    }
  }
  return suspect / words.length > 0.25
}
