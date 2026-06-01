// Sauvegarde d'une activité dans « Mes activités ».
//
// Contrairement à l'ancien appel fire-and-forget (`.catch(() => {})` qui avalait tout),
// cette fonction LÈVE en cas d'échec — réseau (fetch rejette) OU statut HTTP non-ok —
// pour que l'appelant puisse prévenir le prof. Supprime la perte silencieuse d'activités
// (audit 15/05, Phase 2.1 du plan de reprise). Payload = contrat de POST /api/mes-activites.
export async function sauvegarderActivite(payload) {
  const res = await fetch('/api/mes-activites', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}
