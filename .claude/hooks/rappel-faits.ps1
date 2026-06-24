# Hook UserPromptSubmit — injecte ce rappel dans le contexte de l'assistant a CHAQUE message.
# stdout (exit 0) = ajoute au contexte que l'assistant lit (doc Claude Code).
# Texte volontairement SANS accents (robustesse encodage cote hook).
Write-Output @'
RAPPEL (a chaque message, non negociable) :
- Ne devine pas, n'invente pas. N'affirme QUE ce qui est verifie (code lu en entier,
  test lance, donnee constatee de tes propres yeux).
- Lis les documents / fichiers demandes EN ENTIER avant de repondre.
- Chaque affirmation porte sa preuve a cote (fichier/ligne, resultat de commande).
  Pas de preuve -> ecris "pas verifie" et verifie AVANT de parler.
'@
exit 0
