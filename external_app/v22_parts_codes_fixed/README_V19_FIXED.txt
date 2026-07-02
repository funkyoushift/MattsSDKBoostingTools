V19 fixes the missing-tabs crash. Root cause: V18 BL4 Codes tab referenced ACCENT_COLORS/http_json/messagebox without importing them, causing layout construction to stop at BL4 Codes. V19 imports them and was tested to render all 10 tabs.

Run Launch_MattsBoostingTools_External.bat from a clean folder.
