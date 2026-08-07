package com.funkyoushift.msbt.mobile;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.webkit.JavascriptInterface;
import android.webkit.PermissionRequest;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import androidx.core.content.FileProvider;
import androidx.webkit.WebViewAssetLoader;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class MainActivity extends Activity {
    private static final String ASSET_BASE = "https://appassets.androidplatform.net/assets/";
    private static final int REQ_CAMERA = 1001;
    private static final int REQ_INSTALL = 1002;
    private static final String VERSION_JSON_URL =
            "https://github.com/funkyoushift/MattsSDKBoostingTools/releases/download/mobile-beta/mobile-beta-version.json";
    private static final String RELEASE_API_URL =
            "https://api.github.com/repos/funkyoushift/MattsSDKBoostingTools/releases/tags/mobile-beta";
    private static final String FALLBACK_APK_URL =
            "https://github.com/funkyoushift/MattsSDKBoostingTools/releases/download/mobile-beta/MSBT-Mobile-Controller.apk";
    private static final Pattern VERSION_PATTERN =
            Pattern.compile("(\\d+)\\.(\\d+)\\.(\\d+)(?:-beta\\.(\\d+))?", Pattern.CASE_INSENSITIVE);

    private WebView webView;
    private PermissionRequest pendingWebPermission;
    private final ExecutorService bg = Executors.newSingleThreadExecutor();
    private String pendingInstallApkUrl;
    private volatile boolean updateCheckRunning;
    private volatile boolean downloadRunning;

    /**
     * Narrow asset reader fallback. Primary loading uses WebViewAssetLoader so
     * large catalog JSON can stream through normal fetch() instead of a giant
     * JavascriptInterface string return (GZO alone is multi-megabyte).
     */
    public class AssetBridge {
        private final Set<String> allowed = new HashSet<>(Arrays.asList(
                "MattsSDKBoostingTools_gzo_codes.json",
                "MattsSDKBoostingTools_lootlemon_codes.json",
                "custom_bl4_codes.json",
                "item_pools.json",
                "travelmaps_flat.json",
                "travelstations.json",
                "dev_spawner_catalog.json"
        ));

        @JavascriptInterface
        public String readText(String fileName) {
            if (fileName == null) {
                return errorJson("missing file name");
            }
            String name = fileName.trim();
            if (name.contains("/") || name.contains("\\") || name.contains("..") || !allowed.contains(name)) {
                return errorJson("asset not allowed: " + name);
            }
            try (InputStream input = MainActivity.this.getAssets().open(name);
                 BufferedReader reader = new BufferedReader(new InputStreamReader(input, StandardCharsets.UTF_8))) {
                StringBuilder builder = new StringBuilder();
                char[] buffer = new char[8192];
                int read;
                while ((read = reader.read(buffer)) >= 0) {
                    builder.append(buffer, 0, read);
                }
                return builder.toString();
            } catch (Exception error) {
                return errorJson(error.getMessage() == null ? String.valueOf(error) : error.getMessage());
            }
        }

        @JavascriptInterface
        public boolean canRead(String fileName) {
            return fileName != null && allowed.contains(fileName.trim());
        }

        @JavascriptInterface
        public String getAppVersion() {
            return MainActivity.this.currentVersionName();
        }

        @JavascriptInterface
        public int getAppVersionCode() {
            return MainActivity.this.currentVersionCode();
        }

        @JavascriptInterface
        public void checkForUpdate() {
            MainActivity.this.checkForUpdateAsync();
        }

        @JavascriptInterface
        public void downloadAndInstallUpdate(String apkUrl) {
            MainActivity.this.downloadAndInstallAsync(apkUrl);
        }

        @JavascriptInterface
        public void openExternalUrl(String url) {
            if (url == null || url.trim().isEmpty()) {
                return;
            }
            MainActivity.this.runOnUiThread(() -> {
                try {
                    Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url.trim()));
                    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                    startActivity(intent);
                } catch (Exception ignored) {
                    // Quiet for closed beta — UI already shows download CTA.
                }
            });
        }

        @JavascriptInterface
        public boolean hasCameraPermission() {
            return MainActivity.this.checkSelfPermission(Manifest.permission.CAMERA)
                    == PackageManager.PERMISSION_GRANTED;
        }

        @JavascriptInterface
        public void requestCameraPermission() {
            MainActivity.this.runOnUiThread(() -> {
                if (hasCameraPermission()) {
                    notifyCameraPermission(true);
                    return;
                }
                MainActivity.this.requestPermissions(new String[]{Manifest.permission.CAMERA}, REQ_CAMERA);
            });
        }

        private String errorJson(String message) {
            String safe = String.valueOf(message)
                    .replace("\\", "\\\\")
                    .replace("\"", "\\\"")
                    .replace("\n", " ")
                    .replace("\r", " ");
            return "{\"__msbtAssetError\":true,\"message\":\"" + safe + "\"}";
        }
    }

    private String currentVersionName() {
        try {
            PackageInfo info = getPackageManager().getPackageInfo(getPackageName(), 0);
            return info.versionName != null ? info.versionName : "0.0.0";
        } catch (Exception error) {
            return "0.0.0";
        }
    }

    private int currentVersionCode() {
        try {
            PackageInfo info = getPackageManager().getPackageInfo(getPackageName(), 0);
            if (Build.VERSION.SDK_INT >= 28) {
                return (int) info.getLongVersionCode();
            }
            return info.versionCode;
        } catch (Exception error) {
            return 0;
        }
    }

    private void notifyCameraPermission(boolean granted) {
        if (webView == null) {
            return;
        }
        final String js = "window.__msbtCameraPermission && window.__msbtCameraPermission("
                + (granted ? "true" : "false") + ");";
        webView.post(() -> webView.evaluateJavascript(js, null));
    }

    private void notifyJs(String functionName, String jsonPayload) {
        if (webView == null) {
            return;
        }
        final String safe = jsonPayload == null ? "{}" : jsonPayload;
        final String js = "window." + functionName + " && window." + functionName + "(" + safe + ");";
        webView.post(() -> webView.evaluateJavascript(js, null));
    }

    private void grantPendingWebPermissionIfAllowed() {
        if (pendingWebPermission == null) {
            return;
        }
        if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            return;
        }
        PermissionRequest request = pendingWebPermission;
        pendingWebPermission = null;
        String[] resources = request.getResources();
        List<String> allowed = new ArrayList<>();
        if (resources != null) {
            for (String resource : resources) {
                if (PermissionRequest.RESOURCE_VIDEO_CAPTURE.equals(resource)
                        || PermissionRequest.RESOURCE_AUDIO_CAPTURE.equals(resource)) {
                    allowed.add(resource);
                }
            }
        }
        if (allowed.isEmpty()) {
            request.deny();
        } else {
            request.grant(allowed.toArray(new String[0]));
        }
    }

    private void checkForUpdateAsync() {
        if (updateCheckRunning) {
            return;
        }
        updateCheckRunning = true;
        bg.execute(() -> {
            try {
                JSONObject remote = fetchRemoteVersion();
                if (remote == null) {
                    notifyJs("__msbtUpdateCheck", "{\"ok\":false,\"offline\":true,\"message\":\"Could not reach update server.\"}");
                    return;
                }
                String localName = currentVersionName();
                int localCode = currentVersionCode();
                String remoteName = remote.optString("versionName", "");
                int remoteCode = remote.optInt("versionCode", 0);
                String apkUrl = remote.optString("apkUrl", FALLBACK_APK_URL);
                String versionedUrl = remote.optString("apkVersionedUrl", "");
                boolean newer = isNewer(remoteName, remoteCode, localName, localCode);
                JSONObject out = new JSONObject();
                out.put("ok", true);
                out.put("updateAvailable", newer);
                out.put("currentVersion", localName);
                out.put("currentVersionCode", localCode);
                out.put("availableVersion", remoteName);
                out.put("availableVersionCode", remoteCode);
                out.put("apkUrl", apkUrl);
                if (!versionedUrl.isEmpty()) {
                    out.put("apkVersionedUrl", versionedUrl);
                }
                out.put("source", remote.optString("source", "unknown"));
                notifyJs("__msbtUpdateCheck", out.toString());
            } catch (Exception error) {
                String msg = error.getMessage() == null ? String.valueOf(error) : error.getMessage();
                notifyJs("__msbtUpdateCheck", "{\"ok\":false,\"offline\":true,\"message\":"
                        + jsonQuote(msg) + "}");
            } finally {
                updateCheckRunning = false;
            }
        });
    }

    private JSONObject fetchRemoteVersion() {
        JSONObject fromJson = fetchVersionJson();
        if (fromJson != null) {
            return fromJson;
        }
        return fetchVersionFromReleaseApi();
    }

    private JSONObject fetchVersionJson() {
        try {
            String body = httpGet(VERSION_JSON_URL, 12000);
            if (body == null || body.trim().isEmpty()) {
                return null;
            }
            JSONObject json = new JSONObject(body);
            if (!json.has("versionName") && !json.has("versionCode")) {
                return null;
            }
            if (!json.has("apkUrl") || json.optString("apkUrl").isEmpty()) {
                json.put("apkUrl", FALLBACK_APK_URL);
            }
            json.put("source", "version.json");
            return json;
        } catch (Exception ignored) {
            return null;
        }
    }

    private JSONObject fetchVersionFromReleaseApi() {
        try {
            String body = httpGet(RELEASE_API_URL, 15000);
            if (body == null || body.trim().isEmpty()) {
                return null;
            }
            JSONObject release = new JSONObject(body);
            String bestName = "";
            int bestCode = 0;
            String bestUrl = FALLBACK_APK_URL;
            String versionedUrl = "";

            JSONArray assets = release.optJSONArray("assets");
            if (assets != null) {
                for (int i = 0; i < assets.length(); i++) {
                    JSONObject asset = assets.optJSONObject(i);
                    if (asset == null) {
                        continue;
                    }
                    String name = asset.optString("name", "");
                    String url = asset.optString("browser_download_url", "");
                    if ("mobile-beta-version.json".equals(name) && !url.isEmpty()) {
                        String nested = httpGet(url, 12000);
                        if (nested != null) {
                            try {
                                JSONObject json = new JSONObject(nested);
                                json.put("source", "release-asset-version.json");
                                if (!json.has("apkUrl") || json.optString("apkUrl").isEmpty()) {
                                    json.put("apkUrl", FALLBACK_APK_URL);
                                }
                                return json;
                            } catch (Exception ignored) {
                                // keep scanning assets
                            }
                        }
                    }
                    if (name.startsWith("MSBT-Mobile-Controller-") && name.endsWith(".apk")) {
                        Matcher matcher = VERSION_PATTERN.matcher(name);
                        if (matcher.find()) {
                            String parsed = matcher.group(0);
                            int code = versionSortKey(parsed);
                            if (code >= bestCode) {
                                bestCode = code;
                                bestName = parsed;
                                versionedUrl = url;
                                bestUrl = url;
                            }
                        }
                    } else if ("MSBT-Mobile-Controller.apk".equals(name) && !url.isEmpty()) {
                        bestUrl = url;
                    }
                }
            }

            if (bestName.isEmpty()) {
                String haystack = release.optString("body", "") + " " + release.optString("name", "");
                Matcher matcher = VERSION_PATTERN.matcher(haystack);
                String found = "";
                while (matcher.find()) {
                    String candidate = matcher.group(0);
                    if (candidate.toLowerCase(Locale.US).contains("beta")
                            || versionSortKey(candidate) > versionSortKey(found)) {
                        found = candidate;
                    }
                }
                bestName = found;
                bestCode = versionSortKey(found);
            }

            if (bestName.isEmpty()) {
                return null;
            }
            JSONObject out = new JSONObject();
            out.put("versionName", bestName);
            // Prefer name comparison in JS/native; leave code 0 when only parsed from asset names.
            out.put("versionCode", 0);
            out.put("apkUrl", bestUrl.isEmpty() ? FALLBACK_APK_URL : bestUrl);
            if (!versionedUrl.isEmpty()) {
                out.put("apkVersionedUrl", versionedUrl);
            }
            out.put("source", "github-release-api");
            return out;
        } catch (Exception ignored) {
            return null;
        }
    }

    private static boolean isNewer(String remoteName, int remoteCode, String localName, int localCode) {
        int remoteSort = versionSortKey(remoteName);
        int localSort = versionSortKey(localName);
        // Prefer semver/beta name comparison so API-parsed names stay consistent
        // with PackageManager versionName (versionCode alone can disagree).
        if (remoteSort > 0 && localSort > 0) {
            return remoteSort > localSort;
        }
        if (remoteCode > 0 && localCode > 0) {
            return remoteCode > localCode;
        }
        return remoteSort > localSort;
    }

    /** Sort key: major*1e9 + minor*1e6 + patch*1e3 + betaN (release builds sort above same patch beta). */
    private static int versionSortKey(String versionName) {
        if (versionName == null || versionName.trim().isEmpty()) {
            return 0;
        }
        Matcher matcher = VERSION_PATTERN.matcher(versionName.trim());
        if (!matcher.find()) {
            return 0;
        }
        int major = parseIntSafe(matcher.group(1));
        int minor = parseIntSafe(matcher.group(2));
        int patch = parseIntSafe(matcher.group(3));
        String beta = matcher.group(4);
        int betaN = beta == null ? 999 : parseIntSafe(beta);
        return major * 1_000_000_000 + minor * 1_000_000 + patch * 1_000 + betaN;
    }

    private static int parseIntSafe(String value) {
        try {
            return Integer.parseInt(value);
        } catch (Exception error) {
            return 0;
        }
    }

    private static String jsonQuote(String value) {
        String safe = String.valueOf(value)
                .replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", " ")
                .replace("\r", " ");
        return "\"" + safe + "\"";
    }

    private String httpGet(String urlString, int timeoutMs) throws Exception {
        HttpURLConnection connection = null;
        try {
            URL url = new URL(urlString);
            connection = (HttpURLConnection) url.openConnection();
            connection.setConnectTimeout(timeoutMs);
            connection.setReadTimeout(timeoutMs);
            connection.setInstanceFollowRedirects(true);
            connection.setRequestProperty("Accept", "application/json, text/plain, */*");
            connection.setRequestProperty("User-Agent", "MSBT-Mobile-Controller/" + currentVersionName());
            int code = connection.getResponseCode();
            InputStream stream = code >= 400 ? connection.getErrorStream() : connection.getInputStream();
            if (stream == null || code >= 400) {
                return null;
            }
            BufferedReader reader = new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8));
            StringBuilder builder = new StringBuilder();
            char[] buffer = new char[8192];
            int read;
            while ((read = reader.read(buffer)) >= 0) {
                builder.append(buffer, 0, read);
            }
            reader.close();
            return builder.toString();
        } finally {
            if (connection != null) {
                connection.disconnect();
            }
        }
    }

    private void downloadAndInstallAsync(String apkUrl) {
        final String url = (apkUrl == null || apkUrl.trim().isEmpty()) ? FALLBACK_APK_URL : apkUrl.trim();
        if (downloadRunning) {
            notifyJs("__msbtUpdateProgress", "{\"phase\":\"busy\",\"message\":\"Download already in progress.\"}");
            return;
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && !getPackageManager().canRequestPackageInstalls()) {
            pendingInstallApkUrl = url;
            notifyJs("__msbtUpdateProgress",
                    "{\"phase\":\"need_permission\",\"message\":\"Allow installs from this app, then tap Update again.\"}");
            runOnUiThread(() -> {
                try {
                    Intent intent = new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES);
                    intent.setData(Uri.parse("package:" + getPackageName()));
                    startActivityForResult(intent, REQ_INSTALL);
                } catch (Exception error) {
                    notifyJs("__msbtUpdateProgress", "{\"phase\":\"error\",\"message\":"
                            + jsonQuote("Could not open install permission settings.") + "}");
                }
            });
            return;
        }
        downloadRunning = true;
        notifyJs("__msbtUpdateProgress", "{\"phase\":\"downloading\",\"message\":\"Downloading update…\"}");
        bg.execute(() -> {
            File apkFile = null;
            try {
                File dir = new File(getCacheDir(), "updates");
                if (!dir.exists() && !dir.mkdirs()) {
                    throw new IllegalStateException("Could not create update cache.");
                }
                apkFile = new File(dir, "MSBT-Mobile-Controller-update.apk");
                if (apkFile.exists() && !apkFile.delete()) {
                    // overwrite below
                }
                downloadToFile(url, apkFile);
                if (!apkFile.exists() || apkFile.length() < 10_000) {
                    throw new IllegalStateException("Downloaded APK looks incomplete.");
                }
                final File installFile = apkFile;
                notifyJs("__msbtUpdateProgress", "{\"phase\":\"installing\",\"message\":\"Opening installer…\"}");
                runOnUiThread(() -> launchApkInstaller(installFile));
            } catch (Exception error) {
                if (apkFile != null && apkFile.exists()) {
                    //noinspection ResultOfMethodCallIgnored
                    apkFile.delete();
                }
                String msg = error.getMessage() == null ? String.valueOf(error) : error.getMessage();
                notifyJs("__msbtUpdateProgress", "{\"phase\":\"error\",\"message\":" + jsonQuote(msg) + "}");
            } finally {
                downloadRunning = false;
            }
        });
    }

    private void downloadToFile(String urlString, File dest) throws Exception {
        HttpURLConnection connection = null;
        try {
            URL url = new URL(urlString);
            connection = (HttpURLConnection) url.openConnection();
            connection.setConnectTimeout(20000);
            connection.setReadTimeout(120000);
            connection.setInstanceFollowRedirects(true);
            connection.setRequestProperty("User-Agent", "MSBT-Mobile-Controller/" + currentVersionName());
            int code = connection.getResponseCode();
            if (code >= 400) {
                throw new IllegalStateException("Download failed (HTTP " + code + ").");
            }
            try (InputStream input = connection.getInputStream();
                 FileOutputStream output = new FileOutputStream(dest)) {
                byte[] buffer = new byte[8192];
                int read;
                long total = 0;
                long reported = 0;
                while ((read = input.read(buffer)) >= 0) {
                    output.write(buffer, 0, read);
                    total += read;
                    if (total - reported >= 512_000) {
                        reported = total;
                        notifyJs("__msbtUpdateProgress",
                                "{\"phase\":\"downloading\",\"message\":\"Downloading update… "
                                        + (total / 1024) + " KB\"}");
                    }
                }
                output.flush();
            }
        } finally {
            if (connection != null) {
                connection.disconnect();
            }
        }
    }

    private void launchApkInstaller(File apkFile) {
        try {
            Uri uri = FileProvider.getUriForFile(
                    this,
                    getPackageName() + ".fileprovider",
                    apkFile
            );
            Intent intent = new Intent(Intent.ACTION_VIEW);
            intent.setDataAndType(uri, "application/vnd.android.package-archive");
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(intent);
            notifyJs("__msbtUpdateProgress", "{\"phase\":\"ready\",\"message\":\"Installer opened. Confirm to update.\"}");
        } catch (Exception error) {
            String msg = error.getMessage() == null ? String.valueOf(error) : error.getMessage();
            notifyJs("__msbtUpdateProgress", "{\"phase\":\"error\",\"message\":" + jsonQuote(msg) + "}");
        }
    }

    @SuppressLint({"SetJavaScriptEnabled", "AddJavascriptInterface"})
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        final WebViewAssetLoader assetLoader = new WebViewAssetLoader.Builder()
                .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this))
                .build();

        webView = new WebView(this);
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                return assetLoader.shouldInterceptRequest(request.getUrl());
            }
        });
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onPermissionRequest(final PermissionRequest request) {
                runOnUiThread(() -> {
                    pendingWebPermission = request;
                    if (checkSelfPermission(Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
                        grantPendingWebPermissionIfAllowed();
                    } else {
                        requestPermissions(new String[]{Manifest.permission.CAMERA}, REQ_CAMERA);
                    }
                });
            }
        });
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(false);
        // Closed-beta LAN pairing talks to desktop MSBT over cleartext HTTP from
        // the https://appassets.androidplatform.net origin.
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setMediaPlaybackRequiresUserGesture(false);

        webView.addJavascriptInterface(new AssetBridge(), "MSBTAssets");
        webView.loadUrl(ASSET_BASE + "index.html");
        setContentView(webView);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode != REQ_CAMERA) {
            return;
        }
        boolean granted = grantResults.length > 0
                && grantResults[0] == PackageManager.PERMISSION_GRANTED;
        notifyCameraPermission(granted);
        if (granted) {
            grantPendingWebPermissionIfAllowed();
        } else if (pendingWebPermission != null) {
            pendingWebPermission.deny();
            pendingWebPermission = null;
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != REQ_INSTALL) {
            return;
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                && getPackageManager().canRequestPackageInstalls()
                && pendingInstallApkUrl != null) {
            String url = pendingInstallApkUrl;
            pendingInstallApkUrl = null;
            downloadAndInstallAsync(url);
        } else if (pendingInstallApkUrl != null) {
            notifyJs("__msbtUpdateProgress",
                    "{\"phase\":\"need_permission\",\"message\":\"Install permission still required to update in-app.\"}");
        }
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onDestroy() {
        bg.shutdownNow();
        if (webView != null) {
            webView.destroy();
        }
        super.onDestroy();
    }
}
