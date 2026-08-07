package com.funkyoushift.msbt.mobile;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.os.Bundle;
import android.webkit.JavascriptInterface;
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
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

public class MainActivity extends Activity {
    private static final String ASSET_BASE = "https://appassets.androidplatform.net/assets/";

    private WebView webView;

    /**
     * Narrow asset reader fallback. Primary loading uses WebViewAssetLoader so
     * large catalog JSON can stream through normal fetch() instead of a giant
     * JavascriptInterface string return (GZO alone is multi-megabyte).
     */
    public static class AssetBridge {
        private final Activity activity;
        private static final Set<String> ALLOWED = new HashSet<>(Arrays.asList(
                "MattsSDKBoostingTools_gzo_codes.json",
                "MattsSDKBoostingTools_lootlemon_codes.json",
                "custom_bl4_codes.json",
                "item_pools.json",
                "travelmaps_flat.json",
                "travelstations.json",
                "dev_spawner_catalog.json"
        ));

        AssetBridge(Activity activity) {
            this.activity = activity;
        }

        @JavascriptInterface
        public String readText(String fileName) {
            if (fileName == null) {
                return errorJson("missing file name");
            }
            String name = fileName.trim();
            if (name.contains("/") || name.contains("\\") || name.contains("..") || !ALLOWED.contains(name)) {
                return errorJson("asset not allowed: " + name);
            }
            try (InputStream input = activity.getAssets().open(name);
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
            return fileName != null && ALLOWED.contains(fileName.trim());
        }

        private static String errorJson(String message) {
            String safe = String.valueOf(message)
                    .replace("\\", "\\\\")
                    .replace("\"", "\\\"")
                    .replace("\n", " ")
                    .replace("\r", " ");
            return "{\"__msbtAssetError\":true,\"message\":\"" + safe + "\"}";
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
        settings.setMediaPlaybackRequiresUserGesture(true);

        webView.addJavascriptInterface(new AssetBridge(this), "MSBTAssets");
        webView.loadUrl(ASSET_BASE + "index.html");
        setContentView(webView);
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
