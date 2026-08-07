package com.funkyoushift.msbt.mobile;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.webkit.JavascriptInterface;
import android.webkit.PermissionRequest;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import androidx.webkit.WebViewAssetLoader;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public class MainActivity extends Activity {
    private static final String ASSET_BASE = "https://appassets.androidplatform.net/assets/";
    private static final int REQ_CAMERA = 1001;

    private WebView webView;
    private PermissionRequest pendingWebPermission;

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

    private void notifyCameraPermission(boolean granted) {
        if (webView == null) {
            return;
        }
        final String js = "window.__msbtCameraPermission && window.__msbtCameraPermission("
                + (granted ? "true" : "false") + ");";
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
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.destroy();
        }
        super.onDestroy();
    }
}
