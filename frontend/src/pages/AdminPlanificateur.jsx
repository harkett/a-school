import { useEffect, useState } from 'react'
import { fetchWithTimeout, TIMEOUT_STD, MSG_TIMEOUT } from '../utils/api.js'
import { showError } from '../errorDialog.js'

// LE PLANIFICATEUR — ce que l'application fait toute seule, réglé sans développeur.
//
// L'heure de la veille des tarifs et la cadence de la surveillance étaient écrites dans le code :
// passer un contrôle de 6 h à 22 h demandait une modification, une relecture et un redéploiement
// pour deux chiffres qui ne regardent que l'exploitation.
//
// CE QUE CET ÉCRAN MONTRE, ET POURQUOI CHAQUE COLONNE EST LÀ :
//   - le dernier passage et son résultat : sans eux, une tâche muette est indiscernable d'une
//     tâche morte — l'écran dirait « active » d'un travail arrêté depuis trois semaines ;
//   - le prochain passage, demandé à l'ordonnanceur lui-même : c'est la preuve que le réglage
//     enregistré est bien celui qui tourne ;
//   - « Exécuter maintenant », parce qu'un réglage quotidien ne se vérifie pas autrement qu'en
//     attendant le lendemain.

const BTN = {
  display: 'inline-flex', alignItems: 'center', gap: 6, height: 30, padding: '0 12px',
  borderRadius: 7, fontSize: 12, fontWeight: 500, cursor: 'pointer', border: '1px solid transparent',
}
const BTN_VALIDER = { ...BTN, background: '#1F6EEB', color: '#fff' }
const BTN_NEUTRE  = { ...BTN, background: '#fff', color: '#374151', borderColor: '#d1d5db' }
const grise = style => ({ ...style, opacity: 0.45, cursor: 'not-allowed' })

const CADENCES = [
  { cle: 'quotidien',  libelle: 'chaque jour à…' },
  { cle: 'intervalle', libelle: 'toutes les…' },
]

// Les heures sont celles du SERVEUR (UTC), pas celles du navigateur : c'est l'ordonnanceur qui
// déclenche, et il vit sur le serveur. Afficher une heure locale ferait croire à un réglage qui
// n'existe pas — et deux administrateurs de fuseaux différents liraient deux réglages différents
// pour la même ligne.
const deuxChiffres = n => String(n).padStart(2, '0')

function quand(t) {
  if (t.type_planif === 'intervalle') {
    const m = t.intervalle_minutes || 0
    return m % 60 === 0 && m >= 60 ? `toutes les ${m / 60} h` : `toutes les ${m} min`
  }
  return `chaque jour à ${deuxChiffres(t.heure || 0)} h ${deuxChiffres(t.minute || 0)} UTC`
}

function moment(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return `${deuxChiffres(d.getDate())}/${deuxChiffres(d.getMonth() + 1)} ${deuxChiffres(d.getHours())}:${deuxChiffres(d.getMinutes())}`
}

export default function AdminPlanificateur() {
  const [data, setData]     = useState(null)
  const [erreur, setErreur] = useState('')
  const [occupe, setOccupe] = useState('')     // le code de la tâche en cours de traitement
  const [form, setForm]     = useState(null)   // { code, valeurs } — une seule tâche ouverte

  function charger() {
    return fetchWithTimeout('/api/admin/taches', { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : Promise.reject(new Error('Lecture des tâches impossible.'))))
      .then(setData)
      .catch(e => setErreur(e.message === 'timeout' ? MSG_TIMEOUT : e.message))
  }

  useEffect(() => { charger() }, [])

  async function envoyer(url, methode, corps, code) {
    setOccupe(code)
    try {
      const res = await fetchWithTimeout(url, {
        method: methode, credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: corps ? JSON.stringify(corps) : undefined,
      }, TIMEOUT_STD)
      const d = await res.json().catch(() => ({}))
      if (!res.ok) { showError(d.detail || 'L’opération a échoué.'); return null }
      setForm(null)
      await charger()
      return d
    } catch (e) {
      showError(e.message === 'timeout' ? MSG_TIMEOUT : 'L’opération a échoué.')
      return null
    } finally {
      setOccupe('')
    }
  }

  const maj = (cle, val) => setForm(f => ({ ...f, valeurs: { ...f.valeurs, [cle]: val } }))

  return (
    <div className="flex flex-col gap-4">

      {erreur && <p className="text-xs" style={{ color: '#b91c1c' }}>{erreur}</p>}
      {!data && !erreur && <p className="text-xs text-gray-400">Chargement…</p>}

      {data && data.taches.map(t => {
        const edition = form?.code === t.code
        return (
          <div key={t.code} style={{
            background: '#fff', border: '1px solid #e5e7eb', borderRadius: 10, padding: '14px 16px',
            opacity: t.actif ? 1 : 0.75,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
              <span style={{ fontSize: 14, fontWeight: 700, color: '#111827' }}>{t.libelle}</span>
              <span style={{
                fontSize: 10, fontWeight: 700, padding: '1px 8px', borderRadius: 99,
                background: t.actif ? '#ede9fe' : '#f3f4f6',
                color: t.actif ? '#6d28d9' : '#9ca3af',
              }} title={t.actif ? 'Cette tâche est programmée et se déclenchera toute seule.'
                                : 'Cette tâche ne se déclenchera pas. Elle reste lançable à la main.'}>
                {t.actif ? quand(t) : 'en pause'}
              </span>
              {/* Une ligne en base dont la fonction n'existe plus : le dire, plutôt que d'afficher
                  une tâche qui ne ferait rien le jour où elle se déclenche. */}
              {t.orpheline && (
                <span style={{ fontSize: 10, fontWeight: 700, color: '#b91c1c' }}
                      title="Aucune fonction ne porte ce code : la tâche ne fera rien. À supprimer de la base.">
                  sans fonction
                </span>
              )}
              <span style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
                <button
                  onClick={() => envoyer(`/api/admin/taches/${t.code}/executer`, 'POST', null, t.code)}
                  disabled={!!occupe || t.orpheline}
                  title="Lancer cette tâche tout de suite, par le même chemin que le déclenchement automatique. C’est la seule façon de vérifier un réglage sans attendre le lendemain."
                  style={(occupe || t.orpheline) ? grise(BTN_NEUTRE) : BTN_NEUTRE}
                >{occupe === t.code ? 'En cours…' : 'Exécuter maintenant'}</button>
                <button
                  onClick={() => setForm(edition ? null : { code: t.code, valeurs: { ...t } })}
                  disabled={!!occupe}
                  title="Changer l’heure, la cadence, le destinataire, ou mettre la tâche en pause."
                  style={occupe ? grise(BTN_NEUTRE) : BTN_NEUTRE}
                >{edition ? 'Fermer' : 'Régler'}</button>
              </span>
            </div>

            <p style={{ fontSize: 12, color: '#6b7280', margin: '6px 0 0', lineHeight: 1.5 }}>
              {t.description}
            </p>

            <div style={{ marginTop: 8, display: 'flex', gap: 18, flexWrap: 'wrap', fontSize: 11, color: '#6b7280' }}>
              <span title="Le dernier déclenchement, automatique ou lancé à la main.">
                dernier passage : <strong style={{ color: '#374151' }}>{moment(t.dernier_passage)}</strong>
                {t.derniere_duree_ms != null && <span> ({(t.derniere_duree_ms / 1000).toFixed(1)} s)</span>}
              </span>
              <span title="Ce que l’ordonnanceur a réellement programmé — pas un calcul refait par cet écran.">
                prochain : <strong style={{ color: '#374151' }}>{moment(t.prochain_passage)}</strong>
              </span>
              <span title="À qui part le courriel quand la tâche a quelque chose à signaler.">
                courriel : <strong style={{ color: '#374151' }}>
                  {t.destinataire || data.destinataire_par_defaut || 'aucune adresse'}
                </strong>
                {!t.destinataire && data.destinataire_par_defaut && <span> (adresse du serveur)</span>}
              </span>
            </div>

            {t.dernier_resultat && (
              <p style={{
                marginTop: 8, padding: '7px 10px', borderRadius: 7, fontSize: 11, lineHeight: 1.45,
                background: t.dernier_ok ? '#f0fdf4' : '#fef2f2',
                border: `1px solid ${t.dernier_ok ? '#bbf7d0' : '#fecaca'}`,
                color: t.dernier_ok ? '#166534' : '#b91c1c',
              }}>{t.dernier_resultat}</p>
            )}

            {edition && (
              <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid #f3f4f6',
                            display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-end' }}>
                <label style={{ display: 'flex', flexDirection: 'column', gap: 3, fontSize: 11, color: '#6b7280' }}
                       title="Décochée, la tâche ne se déclenche plus toute seule. Elle reste lançable à la main — utile pour arrêter un travail sans le supprimer.">
                  Activée
                  <input type="checkbox" checked={!!form.valeurs.actif}
                         onChange={e => maj('actif', e.target.checked)} style={{ marginTop: 4 }} />
                </label>

                <label style={{ display: 'flex', flexDirection: 'column', gap: 3, fontSize: 11, color: '#6b7280' }}
                       title="« Chaque jour à » pour un travail qui n’a de sens qu’une fois par jour (relever des tarifs) ; « toutes les » pour une surveillance qui doit réagir vite.">
                  Cadence
                  <select value={form.valeurs.type_planif} onChange={e => maj('type_planif', e.target.value)}
                          style={{ fontSize: 12, padding: '4px 6px', border: '1px solid #d1d5db', borderRadius: 6 }}>
                    {CADENCES.map(c => <option key={c.cle} value={c.cle}>{c.libelle}</option>)}
                  </select>
                </label>

                {form.valeurs.type_planif === 'quotidien' ? (
                  <label style={{ display: 'flex', flexDirection: 'column', gap: 3, fontSize: 11, color: '#6b7280' }}
                         title="Heure du SERVEUR (UTC) : c’est lui qui déclenche. En France, ajoutez 2 heures en été, 1 heure en hiver.">
                    Heure (UTC)
                    <span style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
                      <input type="number" min="0" max="23" value={form.valeurs.heure ?? 0}
                             onChange={e => maj('heure', Number(e.target.value))}
                             style={{ width: 56, fontSize: 12, padding: '4px 6px', border: '1px solid #d1d5db', borderRadius: 6 }} />
                      <span>h</span>
                      <input type="number" min="0" max="59" value={form.valeurs.minute ?? 0}
                             onChange={e => maj('minute', Number(e.target.value))}
                             style={{ width: 56, fontSize: 12, padding: '4px 6px', border: '1px solid #d1d5db', borderRadius: 6 }} />
                    </span>
                  </label>
                ) : (
                  <label style={{ display: 'flex', flexDirection: 'column', gap: 3, fontSize: 11, color: '#6b7280' }}
                         title="En minutes, de 1 à 1440 (24 h). Plus court veut dire réagir plus vite, et travailler plus souvent pour rien quand il ne se passe rien.">
                    Toutes les (minutes)
                    <input type="number" min="1" max="1440" value={form.valeurs.intervalle_minutes ?? 5}
                           onChange={e => maj('intervalle_minutes', Number(e.target.value))}
                           style={{ width: 90, fontSize: 12, padding: '4px 6px', border: '1px solid #d1d5db', borderRadius: 6 }} />
                  </label>
                )}

                <label style={{ display: 'flex', flexDirection: 'column', gap: 3, fontSize: 11, color: '#6b7280', flex: 1, minWidth: 220 }}
                       title="Laisser vide pour écrire à l’adresse d’administration du serveur. Une adresse ici ne concerne que cette tâche.">
                  Destinataire du courriel
                  <input type="text" value={form.valeurs.destinataire || ''}
                         onChange={e => maj('destinataire', e.target.value)}
                         placeholder={data.destinataire_par_defaut || 'adresse@exemple.fr'}
                         style={{ fontSize: 12, padding: '4px 6px', border: '1px solid #d1d5db', borderRadius: 6, width: '100%' }} />
                </label>

                <button
                  onClick={() => envoyer(`/api/admin/taches/${t.code}`, 'PUT', form.valeurs, t.code)}
                  disabled={!!occupe}
                  title="Enregistrer et appliquer tout de suite : la tâche est reprogrammée sans attendre un redémarrage."
                  style={occupe ? grise(BTN_VALIDER) : BTN_VALIDER}
                >Valider</button>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
