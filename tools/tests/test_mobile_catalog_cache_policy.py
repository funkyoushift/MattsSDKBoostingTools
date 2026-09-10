"""Exercise Android's build/digest guard on a plain JVM without an emulator."""

from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "mobile_controller/app/src/main/java/com/funkyoushift/msbt/mobile/CatalogCachePolicy.java"


def test_android_catalog_build_and_digest_policy(tmp_path):
    javac, java = shutil.which("javac"), shutil.which("java")
    if not javac or not java:
        pytest.skip("JDK not installed")
    harness = tmp_path / "CatalogPolicyHarness.java"
    harness.write_text('''
package com.funkyoushift.msbt.mobile;
public class CatalogPolicyHarness {
    private static void require(boolean result) {
        if (!result) throw new AssertionError("Catalog cache policy regression");
    }
    public static void main(String[] args) {
        require(!CatalogCachePolicy.isCurrent("", "25234898", ""));
        require(!CatalogCachePolicy.isCurrent("25234897", "25234898", ""));
        require(!CatalogCachePolicy.isCurrent("25234898", "25234898", "25234900"));
        require(!CatalogCachePolicy.isCurrent("invalid", "25234898", ""));
        require(!CatalogCachePolicy.isCurrent("0", "25234898", ""));
        require(CatalogCachePolicy.isCurrent("25234898", "25234898", ""));
        require(CatalogCachePolicy.isCurrent("25234900", "25234898", "25234900"));
        require(CatalogCachePolicy.isCurrent("", "", ""));
        require(!CatalogCachePolicy.isCurrent("9007199254740992", "9007199254740993", ""));
        String digest = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";
        require(CatalogCachePolicy.validDigest(digest.toUpperCase(), digest));
        require(!CatalogCachePolicy.validDigest("", digest));
        require(!CatalogCachePolicy.validDigest(digest, digest.substring(1)));
        require(!CatalogCachePolicy.validDigest("bad", "bad"));
    }
}
''', encoding="utf-8")
    subprocess.run([javac, "-d", str(tmp_path), str(POLICY), str(harness)], check=True, capture_output=True, text=True)
    subprocess.run([java, "-cp", str(tmp_path), "com.funkyoushift.msbt.mobile.CatalogPolicyHarness"], check=True, capture_output=True, text=True)
