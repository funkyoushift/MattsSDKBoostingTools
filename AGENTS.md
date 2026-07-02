\# MSBT Codex Instructions



This project contains a Borderlands 4 SDK mod and an external Python control panel.



Goal:

Make BLImGui optional by moving backend/game-action logic out of blimgui\_panel.py.



Hard rules:

\- Do not delete the working BLImGui UI.

\- Do not rewrite the entire project at once.

\- Do not remove resources.

\- Do not change the external app layout unless explicitly asked.

\- external\_bridge.py must eventually avoid importing blimgui or blimgui\_panel.py.

\- BLImGui should become optional fallback only.

\- Keep changes small and commit-ready.



Important architecture:

\- blimgui\_panel.py currently mixes UI, state, and backend action wrappers.

\- Existing non-UI modules may include:

&#x20; player\_economy.py

&#x20; serial\_rewards.py

&#x20; legit\_builder\_core.py

&#x20; travel.py

&#x20; movement\_adjustments.py

&#x20; item\_pool\_spawning.py

&#x20; dev\_tools.py

&#x20; party\_helpers.py



Desired architecture:

\- backend\_actions.py contains bridge-safe non-UI action handlers.

\- external\_bridge.py calls backend\_actions.py.

\- blimgui\_panel.py may call backend\_actions.py but should not be required for the bridge.

\- External app owns static resources and UI.

\- SDK mod only handles live game interaction.



Testing:

\- Run Python syntax checks after changes.

\- Package .sdkmod only after import/syntax checks pass.

\- Do not claim BLImGui independence until bridge /status works with blimgui.zip disabled.

