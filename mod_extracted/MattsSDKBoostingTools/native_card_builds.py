"""Build-specific native card addresses. See docs/native-cards/EPIC_CARD_PROFILE.md.

Epic is an offline-verified test candidate; live validation is still required.
No pattern scanning or guessed address fallback is performed in the game.
"""

STEAM = 'steam-25372571'
EPIC = 'epic-4845623'

# Steam RVA: (Epic RVA, byte length, Steam SHA256, Epic SHA256)
EPIC_FUNCTIONS = {
    0x56D3CCA: (0x56E544A, 772, '5ce1aaa8933709a337c65faf40db6c17e45ec6bbc895296c8fc71b30d1a58802', '1a7077b37f3331c700de121f7ce4db682dc4e54a7b5ce12c220796f29f4f0208'),
    0xBABBE2: (0xBAD91E, 111, 'd69c483030211fa666465e66e55105f947ce61c406b5497d78f604528ecc5e70', 'd69c483030211fa666465e66e55105f947ce61c406b5497d78f604528ecc5e70'),
    0xBAC7D2: (0xBAE50E, 1681, '6aff5e04e3b4d3bb0ebbf2aafe5c21dc5f0150771b3b4b6bc7c07297527e5319', 'c0228d2bb71efe0dc66c0cc87dda0d7c50851e757bb14d202b2b58f6a3761f84'),
    0xBAF88E: (0xBB15CA, 4333, '51bd17ddef73d78301659fe08778d375c51dff57bdfb7cab293a941f66a6a4d5', 'df604e7c1ee07ed0de2deedbce20200535ac521ae065b135657c279d0a4d9d71'),
    0x8E1AA38: (0x8E1FA60, 38, 'fe7689fda843ad3179819bd789dc53c22f0d1778ea6ddfba9c14dbba199dc1d8', '4098d54bf63e2218097cb0d6afbd0d31c00c96cdf3654bb145bc33f27c922aac'),
    0xE69A30: (0xE67F80, 633, 'ec1f59a0363723667b0d3f99537cafe84f166171ea923ed07e46dabc86e0b593', 'b1bf381ff47eb93ad71412b476827ce245599a3b427f892de2eb900e7c626cb5'),
    0xE69D1A: (0xE6826A, 1085, '0a8a22ae8ab912bc37dd763440fd0322b20a12884fd804f3765f4a844c971c73', '660f04e42b1b27ae3a4ad563e9b8088a5625d7c97cae61f817f80e665c24c3b7'),
    0xE69CA9: (0xE681F9, 113, 'bfc0da2a7661a8f5f785a94a6f2ae2d54d5c0d89333506ac802a7b79a0fa67ed', 'fd621eea796007ccec41127a8d6228c9b473d2db72449784bffc47d3f9b0eef7'),
    0x20A8: (0x20A8, 64, '7b0652ce5487ac59d2d731b69715d6a77a54ebcf2bcd221ea82f7ed66108978f', '921a9f13e91c90dbe46da7fdeea94b947cd9afe8643c27d5822884fd7cde2152'),
    0x5C4B4F8: (0x5C59D5C, 22, 'ec1033a2760eeb536c16690b3e953b4cc1d1341147dd7e73d9aafacc9285e586', 'ec1033a2760eeb536c16690b3e953b4cc1d1341147dd7e73d9aafacc9285e586'),
    0x5C4B50E: (0x5C59D72, 374, '96c18b1dbda7900d1eb51cb989eeca169f923f1c7d842f676c7e4087abe770c9', '07e4c4ced2b1d7575a097c1dc6e83dbc6c6283edaef8b31df1e047376af63c29'),
    0x236036: (0x236036, 278, '471951c9b998dd98fe1120f420c18a7487e8167cf34972a3c32b3b42a881f9d1', 'cb1965c2209f96ee2f9e0693a5ab867d47d3190f7868ec43f557263398823584'),
    0x479623A: (0x47A79AA, 118, '0be1c20f5860b44ee8f6a96a66ece5716e2bb0c28e58c4b0e626034c7414cc34', '51fd90686b220f1fc45e4afdfb23842f58638d39dc7cb6ef26966fe43c2e3e6b'),
    0x4994E1A: (0x49A658A, 205, '92b6a793b98a730f39f4f464a6dcdc17d4d1fa44f68a902b7b5ba9d4f938e1ec', 'fe1b1b4e751e011ffb476ede49d14fe616f7386f613135516d272569c625ef9c'),
    0x4774916: (0x4786086, 384, 'f83496dc177e13c3d75b5b865591823d356ed2c4a9bde6fc21b04ae21cc84446', 'fcf4da5326bddffc39c863fb206da372b87ddbb86befdbde33baaaa8429903d4'),
    0xB95EC6: (0xB97C02, 98, '8d005584492b7e689def0e1a72e0834ab0e6474d4e347bd6774c757de08dfadf', '1a0577a3f571d18bbac1752e47aeec91d1b3b041bc22188110fe8713473d9933'),
    0xB95F28: (0xB97C64, 185, 'e7fde244391f8a884916c7c4a6b8f53b399540e14a0c47cedfd00bfc0135bd91', '20f84829efcf7dff4b4f4502011b837c937424108744f76168ee1bcd60f68a24'),
    0x58CF8C4: (0x58E0C0A, 235, 'ab40f436d65c9c3a2f61b79ead977c106d6d84e7fee392e8ef933aea2d8f2518', 'efd512045d89192f7c4b13c44898dee1d566f108811327d4e3ed7d3fec4b2ef1'),
    0xE95040: (0xE93114, 386, '83cf31d4221c0c77bbff7daa6094fea31a557c7e225fe3c6db1643d447025b7a', '15646672500830daf8d1866094b7f93ab6804f0f066f09d5d22db1d1565932d8'),
    0x11FC6BA: (0x11FA746, 20881, 'fb86d5e63e7e052c5badaf1a09fdbbfcb8ed45faa37e9fa743ccf5b3cd7f10c9', 'ed19e03602ba95294e4d2b2e7e4c2cf87f36d377cc0cacd2d4d9c7ae2c2c2566'),
    0x575204C: (0x57637CC, 38, '482279190c6ac5458d1017137810a2670fc207e692424eacbe5dff91ba0834cb', 'd0d65d419c41a9185bf35e09f8177379ee1b570431af1f182b6a787f125722c6'),
    0x5752072: (0x57637F2, 114, '9a07ffab4f3eac413527b7553cefbea1289bd8a66c69f60c67e1fabe6669ec10', 'cdce22232d214396be874297f518783ff30e9231f1b42c2409b3c68203700be9'),
    0x10F1BC6: (0x10EF92C, 1213, '9467c955bf42c217ba7a0acd98172b808f16bc9bc4d6d15b6bad168d67848601', 'e98809e2319929be22aa658c7893aefe3ffaa904d42f710b2bf46c0838a95b33'),
    0x167376E: (0x166DDA8, 1952, 'f464d4f455549b0f4859241a0696f1252abe11e550aa91f81b020b512b2b098c', 'd95e81c7fe8ae57d1e017686251947fbc00e826cc12a9c6656b80123565baab5'),
    0x10C71FE: (0x10C5104, 2315, '1bf67fc5592bd2e68edfc04a7ccbeaf3cee430cb47d89c443ea069bff2817156', 'a7a244cf0f1bd175b700d4e19f95186433917cf90a3255a52441e5117d64197e'),
    0x16193F4: (0x1614164, 1566, 'e1852cd6457b393abbb2051ebf026a303ae1a2747cba3913639b544d02339f2e', '1fefb3397f723b8a8b36a22c5855dade04b2da16c3a4ca19d5c7378ffc45f05b'),
}

# Original constructors/formatting code reference these vtables.
EPIC_DATA = {
    0x9E12790: 0x9DFE790,
    0xB9B7700: 0xB9A3530,
}


def require_card_profile(profile):
    if profile not in (STEAM, EPIC):
        raise RuntimeError(f'Game cards are not supported by this game build ({profile})')


def card_rva(profile, steam_rva):
    """Resolve only explicitly recovered functions/data; never mix profiles."""
    require_card_profile(profile)
    if steam_rva not in EPIC_FUNCTIONS and steam_rva not in EPIC_DATA:
        raise RuntimeError(f'Unmapped native card address: {steam_rva:x}')
    if profile == STEAM:
        return steam_rva
    if steam_rva in EPIC_DATA:
        return EPIC_DATA[steam_rva]
    return EPIC_FUNCTIONS[steam_rva][0]


def card_gates(profile, steam_gates):
    require_card_profile(profile)
    if profile == STEAM:
        return steam_gates
    result = []
    for start, end, digest in steam_gates:
        entry = EPIC_FUNCTIONS.get(start)
        if entry is None or entry[1] != end - start or entry[2] != digest:
            raise RuntimeError(f'Native card profile evidence mismatch: {start:x}')
        target, size, _, target_digest = entry
        result.append((target, target + size, target_digest))
    return tuple(result)
