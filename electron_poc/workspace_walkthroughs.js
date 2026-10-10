/* Task-layout tour copy and routes. Classic keeps its panel-arrangement tour. */
window.MsbtWorkspaceWalkthroughs={revision:2,configure(tours,tabs){
  if(!window.MsbtWorkspace?.enabled)return;
  const step=(title,body,tab,section,targetSel,extra={})=>({title,body,tab,section,targetSel,...extra});
  const home=(title,body,targetSel,extra={})=>step(title,body,'boosting','overview',targetSel,extra);
  const nav=home('Find your next task','Home groups the tools by task. Open a category in the sidebar, or use Ctrl+K to find a specific control. Opening a page never runs a game action.','.workspace-home-grid');
  const targets=step('Choose the recipient beside the action','Use the player selector beside the controls you are about to apply. Some tools affect your character or the whole session instead; read the scope note. A named player, All Players and Other Players are different targets.','boosting','levels','[data-msbt-panel="boost-levels"] .workspace-inline-target');
  const mayhem=step('Mayhem unlocks and UVH','Choose a player and a Mayhem rank from 1–20, then Unlock Mayhem when you intend to apply it. This unlocks the saved rank and prepares Takedown access; it keeps higher unlocks and does not change active difficulty. Hardcore needs rank 5. UVH and challenge completion affect live lobby players separately.','boosting','challenges','[data-msbt-panel="boost-uvh"]');
  const afk=step('Prepare items before starting AFK','Select items in the Catalog, Inventory or Saved Items and add them to the random or guaranteed AFK list. Serial Converter and Give Items also have shortcuts. Review AFK list opens the setup without starting the lobby. Mayhem is an optional per-guest boost; set the rank before Start.','boosting','afk','#afkLobbyPanel',{targetSel:'[data-msbt-panel="afk-lobby"]'});
  const view=home('Text size, language and appearance','Open App → View for text size and spacing. Choose a language in App; Australian slang is the explicit humorous option. The task layout keeps controls on their own pages. Classic retains the optional movable-panel layout.','[data-msbt-view-menu]',{revealDetails:'.workspace-app-menu'});
  tours.main.splice(0,tours.main.length,
    home('Welcome to Borderlands 4 Modding Tools','This guide explains the layout without applying boosts. Live actions need the game and MSBT SDK connected. Conversion and validation work offline. Home is the starting point for the task pages.','[data-msbt-panel="boost-essentials"]'),
    nav,
    step('Connection and players','Use Status in the header or Refresh Status on Players & Targets. Confirm the current roster before choosing a recipient. Disabled controls explain when the game connection is required.','boosting','players','[data-msbt-panel="boost-target"]'),
    targets,
    mayhem,
    afk,
    step('Items, saved gear and serials','Saved Items & Community holds your saved gear. Use Select Multiple to select several rows; selected rows turn red. Hover cards leave clicks available to the list; pinned cards can be inspected. Converter, validation, inventory and catalog each have their own page.','serial-tools','saved','[data-msbt-panel="serial-bookmarks"]'),
    step('Weapons and survival have separate controls','Infinite Reserve Ammo keeps reserve ammo. No Reload keeps the magazine from emptying. Turn No Reload off to compare reload speed. God Mode and action-skill controls have their own page and player selector.','boosting','combat','[data-msbt-panel="boost-weapon-tests"]'),
    step('Movement, travel and in-game shortcuts','Movement & Flight, Player Teleport, Map Travel and Saved Locations are separate pages. Movement form changes need Apply. Use gold + QM pins for in-game F7 shortcuts; Instant Drops / Instant Holds also support user-set direct oak2 hotkeys.','player-movement','movement','[data-msbt-panel="move-presets"]'),
    step('Updates, backups and help','App & Tools contains Updates & Backups, Activity & Connection, Mobile Pairing and Help. Keep a backup before replacing SDK files; restart the game after an SDK update. The install QR gets the phone app; the pairing QR connects it to this PC.','updates',null,'.updates-page'),
    view,
    home('Choose another guide','Choose a detailed guide below. Back revisits the previous step; Skip closes a guide. Replay from App → Walkthroughs. These guides navigate and explain controls; they do not start game actions.','[data-msbt-panel="boost-essentials"]',{type:'choices'})
  );
  tours.layout.splice(0,tours.layout.length,
    nav,
    home('Use the task sidebar','Expand a category and choose a page. The selected page stays highlighted. On a narrow window use the navigation button to open the sidebar.','.workspace-sidebar',{revealNavigation:true}),
    home('Search for a control','Press Ctrl+K or use this search field. A result opens the page containing that control. Searching and opening a result do not apply the control.','#appFinderInput'),
    home('Home and Back','Home returns to the task directory. Back returns to the previous page you visited, without undoing game actions.','#workspaceBackBtn',{revealNavigation:true}),
    targets,
    view,
    home('Replay a walkthrough','App → Walkthroughs reopens the guide chooser. Classic has its own panel-arrangement guide; the task layout uses pages instead of dragging panels.','#walkthroughHeaderBtn',{revealDetails:'.workspace-app-menu'})
  );
  for(const steps of Object.values(tabs))for(const row of steps){
    if(/msbt-layout-toolbar|msbt-layout-hint|msbt-panels-menu|dev-layout-toggle/.test(row.targetSel||'')){
      row.title='Navigate related tools';row.body='Use the sidebar for related pages, Ctrl+K for a specific control, and Back to return. App → View changes text size and spacing. The task layout keeps each tool on its own page.';
      row.targetSel='#tab-'+row.tab+' > .workspace-heading';delete row.revealPanels;
    }
  }
  const uvh=tabs.boosting.find(s=>s.title==='UVH 1–7');if(uvh)Object.assign(uvh,mayhem);
  for(const row of tabs.boosting){
    if(row.title==='Essentials')row.title='Home and task pages';
    if(row.title==='Challenges')row.body='Mayhem, UVH & Challenges keeps these different progression controls together. Challenge completion applies to live players in the lobby. Use category and search filters, then review the confirmation before completing challenges.';
    if(row.title==='Ground Loot')row.body='Ground Loot & Backpack Drops holds pull, hide and delete controls. Check the local or party scope before applying. Drop My Backpack affects your own character. Shinies Deliver uses its player target; Shinies Drop creates ground loot.';
  }
  const update=tabs.updates.find(s=>s.title==='Three update lanes');if(update)update.body='Open App & Tools → Updates & Backups for Desktop App, Game SDK Stack, Catalog Data and saved settings. Check Everything reads status without changing files.';
  const log=tabs.activity.find(s=>s.title==='Activity Log');if(log)log.body='App & Tools → Activity & Connection shows recent actions and errors. Copy useful details before opening Help & Report an Issue.';
}};
