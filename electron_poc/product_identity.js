"use strict";

const PRODUCT_NAME = "Borderlands 4 Modding Tools — Powered by Funk";

function applyProductIdentity(app) {
  // package.json.name remains matts-sdk-boosting-tools. Capture its existing
  // profile (or an explicit caller override) before changing the display name.
  const userData = app.getPath("userData");
  const sessionData = app.getPath("sessionData");
  app.setName(PRODUCT_NAME);
  app.setPath("userData", userData);
  app.setPath("sessionData", sessionData);
  app.setAboutPanelOptions({
    applicationName: PRODUCT_NAME,
    credits: "Maintained by FunkYouSHiFT. Original project and editor by Mattmab (Matt)."
  });
}

module.exports = { PRODUCT_NAME, applyProductIdentity };
