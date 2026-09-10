package com.funkyoushift.msbt.mobile;

import java.math.BigInteger;

/** Build ordering for per-asset catalog descriptors; independent of Android. */
final class CatalogCachePolicy {
    private CatalogCachePolicy() {}

    static BigInteger gameBuild(String value) {
        if (value == null || !value.trim().matches("[0-9]+")) return null;
        BigInteger build = new BigInteger(value.trim());
        return build.signum() > 0 ? build : null;
    }

    static boolean isCurrent(String candidate, String bundled, String cached) {
        BigInteger value = gameBuild(candidate);
        for (String minimum : new String[]{bundled, cached}) {
            BigInteger floor = gameBuild(minimum);
            if (floor != null && (value == null || value.compareTo(floor) < 0)) return false;
        }
        return true;
    }

    static boolean validDigest(String expected, String actual) {
        return expected != null && actual != null
                && expected.matches("(?i)[0-9a-f]{64}") && expected.equalsIgnoreCase(actual);
    }
}
