/* Shared desktop/mobile UI translations. Game messages and item data remain verbatim. */
(() => {
  const rows = {
    start: ['Start AFK Lobby','Iniciar sala AFK','Démarrer le salon AFK','Iniciar sala AFK',"AFK-Lobby starten","AFK-lobby starten"],
    stop: ['Stop AFK Lobby','Detener sala AFK','Arrêter le salon AFK','Parar sala AFK',"AFK-Lobby stoppen","AFK-lobby stoppen"],
    openShift: ['Open SHiFT','Abrir SHiFT','Ouvrir SHiFT','Abrir SHiFT',"SHiFT öffnen","SHiFT openen"],
    closeShift: ['Close SHiFT','Cerrar SHiFT','Fermer SHiFT','Fechar SHiFT',"SHiFT schließen","SHiFT sluiten"],
    restore: ['Close SHiFT / restore controls','Cerrar SHiFT / recuperar controles','Fermer SHiFT / rétablir les commandes','Fechar SHiFT / restaurar controles',"SHiFT schließen / Steuerung wiederherstellen","SHiFT sluiten / besturing herstellen"],
    walkthroughs: ['Walkthroughs','Tutoriales','Tutoriels','Tutoriais',"Anleitungen","Handleidingen"],
    afkWalkthrough: ['AFK Lobby walkthrough','Tutorial de la sala AFK','Tutoriel du salon AFK','Tutorial da sala AFK',"Anleitung zur AFK-Lobby","Handleiding voor de AFK-lobby"],
    pull: ['Load PC settings','Cargar ajustes del PC','Charger les réglages du PC','Carregar configurações do PC',"PC-Einstellungen laden","PC-instellingen laden"],
    refresh: ['Refresh bookmarks','Actualizar favoritos','Actualiser les favoris','Atualizar favoritos',"Lesezeichen aktualisieren","Bladwijzers vernieuwen"],
    addPool: ['Add selected to loot','Añadir selección al botín','Ajouter la sélection au butin','Adicionar seleção ao saque',"Auswahl zur Beute hinzufügen","Selectie aan buit toevoegen"],
    addFixed: ['Add selected to guaranteed items','Añadir selección a objetos garantizados','Ajouter la sélection aux objets garantis','Adicionar seleção aos itens garantidos',"Auswahl zu garantierten Gegenständen hinzufügen","Selectie aan gegarandeerde voorwerpen toevoegen"],
    createFolder: ['Create folder','Crear carpeta','Créer un dossier','Criar pasta',"Ordner erstellen","Map maken"],
    moveFolder: ['Move selected to folder','Mover selección a la carpeta','Déplacer la sélection dans le dossier','Mover seleção para a pasta',"Auswahl in Ordner verschieben","Selectie naar map verplaatsen"],
    folder: ['Folder path','Ruta de la carpeta','Chemin du dossier','Caminho da pasta',"Ordnerpfad","Mappad"],
    count: ['Random delivery size','Cantidad de objetos aleatorios','Nombre d’objets aléatoires','Quantidade de itens aleatórios',"Anzahl zufälliger Gegenstände","Aantal willekeurige voorwerpen"],
    all: ['Send all selected items · password above 70','Enviar todos los objetos seleccionados · contraseña para más de 70','Envoyer tous les objets sélectionnés · mot de passe au-delà de 70','Enviar todos os itens selecionados · senha acima de 70',"Alle ausgewählten Gegenstände senden · über 70 nur mit Passwort","Alle geselecteerde voorwerpen sturen · wachtwoord vereist boven 70"],
    random: ['Guaranteed items + random fill','Objetos garantizados + selección aleatoria','Objets garantis + sélection aléatoire','Itens garantidos + seleção aleatória',"Garantierte Gegenstände + zufällige Ergänzung","Gegarandeerde voorwerpen + willekeurige aanvulling"],
    level: ['Max level','Nivel máximo','Niveau maximal','Nível máximo',"Maximales Level","Maximaal niveau"],
    spec: ['Max specialization rank','Rango de especialización máximo','Rang de spécialisation maximal','Grau de especialização máximo',"Maximaler Spezialisierungsrang","Maximale specialisatierang"],
    sdu: ['Max SDUs · 3,225','SDU · 3225','SDU · 3225','SDU · 3225',"Maximale SDUs · 3225","Maximale SDU’s · 3225"],
    cash: ['Max cash','Dinero máximo','Argent maximal','Dinheiro máximo',"Maximales Geld","Maximaal geld"],
    eridium: ['Max Eridium','Eridio máximo','Éridium maximal','Erídio máximo',"Maximales Eridium","Maximaal Eridium"],
    keys: ['Max vault card keys · cards 1–5','Llaves de tarjetas de la Cámara al máximo · tarjetas 1–5','Clés de cartes de l’Arche au maximum · cartes 1–5','Chaves de cartões da Arca no máximo · cartões 1–5',"Maximale Kammer-Karten-Schlüssel · Karten 1–5","Maximale Vault Card-sleutels · kaarten 1–5"],
    challenges: ['Complete non-UVHM challenges','Completar desafíos excepto UVHM','Terminer les défis hors UVHM','Concluir desafios exceto UVHM',"Herausforderungen außer UVHM abschließen","Uitdagingen behalve UVHM voltooien"],
    uvhm: ['UVHM 1–7','UVHM 1–7','UVHM 1–7','UVHM 1–7',"UVHM 1–7","UVHM 1–7"],
    cosmetics: ['Cosmetics + vehicle unlocks','Cosméticos + vehículos','Cosmétiques + véhicules','Cosméticos + veículos',"Kosmetik + Fahrzeugfreischaltungen","Cosmetische items + voertuigen ontgrendelen"],
    loot: ['Send selected loot','Enviar botín seleccionado','Envoyer le butin sélectionné','Enviar saque selecionado',"Ausgewählte Beute senden","Geselecteerde buit sturen"],
    auto_accept: ['Auto-accept SHiFT friends','Aceptar amigos de SHiFT automáticamente','Accepter automatiquement les amis SHiFT','Aceitar amigos SHiFT automaticamente',"SHiFT-Freundesanfragen automatisch annehmen","SHiFT-vriendschapsverzoeken automatisch accepteren"],
    auto_kick: ['Kick after everyone on the connection finishes','Expulsar cuando terminen todos los jugadores de la conexión','Expulser quand tous les joueurs de la connexion ont terminé','Expulsar quando todos os jogadores da conexão terminarem',"Entfernen, sobald alle Spieler dieser Verbindung fertig sind","Verwijderen zodra alle spelers op deze verbinding klaar zijn"],
    counts: ['Guest joins: {session} this session · {lifetime} lifetime','Entradas: {session} en esta sesión · {lifetime} en total','Arrivées : {session} cette session · {lifetime} au total','Entradas: {session} nesta sessão · {lifetime} no total',"Gastbeitritte: {session} in dieser Sitzung · {lifetime} insgesamt","Deelnames: {session} deze sessie · {lifetime} in totaal"],
    unavailable: ['unavailable','no disponible','indisponible','indisponível',"nicht verfügbar","niet beschikbaar"]
  };
  const locales = ['en','es','fr','pt-BR','de','nl'];
  const storageKey = 'msbt.ui.language.v1';
  let language = 'en';
  try { const saved = localStorage.getItem(storageKey); if(locales.includes(saved))language=saved; } catch {}
  function t(key, values={}) {
    const text = rows[key]?.[locales.indexOf(language)] ?? rows[key]?.[0] ?? key;
    return text.replace(/\{(\w+)\}/g, (match,key) => Object.hasOwn(values,key) ? String(values[key]) : match);
  }
  function apply() {
    document.documentElement.lang = language;
    document.querySelectorAll('[data-i18n]').forEach(el=>{el.textContent=t(el.dataset.i18n);});
    document.querySelectorAll('[data-language-selector]').forEach(el=>{el.value=language;});
  }
  function setLanguage(value) {
    if(!locales.includes(value))return;
    language=value;try{localStorage.setItem(storageKey,value);}catch{}
    apply();window.dispatchEvent(new Event('msbt-language-change'));
  }
  function labelText(label,key) {
    if(!label)return;
    const nodes=[...label.childNodes].filter(node=>node.nodeType===Node.TEXT_NODE && node.textContent.trim());
    for(const node of nodes){const span=document.createElement('span');span.dataset.i18n=key;node.replaceWith(span);}
  }
  const ids={afkStart:'start',afkMobileStart:'start',afkStop:'stop',afkMobileStop:'stop',afkShiftOpen:'openShift',afkShiftClose:'closeShift',afkCloseShift:'restore',walkthroughHeaderBtn:'walkthroughs',afkWalkthroughBtn:'afkWalkthrough',afkPull:'pull',afkLoadBookmarks:'refresh',afkAddBookmarks:'addPool',afkAddGuaranteedBookmarks:'addFixed',bookmarkCreateFolderBtn:'createFolder',bookmarkMoveFolderBtn:'moveFolder'};
  Object.entries(ids).forEach(([id,key])=>{const el=document.getElementById(id);if(el)el.dataset.i18n=key;});
  document.querySelectorAll('[data-afk-boost],[data-afk]').forEach(el=>labelText(el.closest('label'),el.dataset.afkBoost||el.dataset.afk));
  [['afkAutoAccept','auto_accept'],['afkAutoKick','auto_kick'],['afkCount','count'],['afkRandomCount','count']].forEach(([id,key])=>labelText(document.getElementById(id)?.closest('label'),key));
  ['bookmarkGroup','bookmarkFolderPath'].forEach(id=>{const el=document.querySelector('label[for="'+id+'"]');if(el)el.dataset.i18n='folder';});
  document.querySelectorAll('#afkMode option,#afkLootMode option').forEach(el=>{el.dataset.i18n=el.value==='all'?'all':'random';});
  document.querySelectorAll('[data-language-selector]').forEach(el=>{el.addEventListener('change',()=>setLanguage(el.value));});
  window.msbtI18n={t,setLanguage,apply,locales,rows,get language(){return language}};
  apply();
})();
