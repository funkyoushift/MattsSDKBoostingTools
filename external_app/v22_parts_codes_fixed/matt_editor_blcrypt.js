#!/usr/bin/env node
"use strict";

/*
 * Local MSBT wrapper for Mattmab's save/profile decryptor path.
 *
 * The encryption/decryption routine is adapted from:
 * mattmab/legit-builder Application/node-api/Encryption.js
 *
 * Matt's editor credits glacierpiece (@glacierpiece) for the original blcrypt.py
 * BL4 save utility powering save/profile encryption and decryption.
 */

const crypto = require("crypto");
const zlib = require("zlib");

class Encryption {
  static BASE_KEY = Buffer.from([
    0x35, 0xec, 0x33, 0x77, 0xf3, 0x5d, 0xb0, 0xea,
    0xbe, 0x6b, 0x83, 0x11, 0x54, 0x03, 0xeb, 0xfb,
    0x27, 0x25, 0x64, 0x2e, 0xd5, 0x49, 0x06, 0x29,
    0x05, 0x78, 0xbd, 0x60, 0xba, 0x4a, 0xa7, 0x87
  ]);

  static deriveKey(userid) {
    const trimmed = String(userid || "").trim();
    if (!trimmed) {
      throw new Error("Steam ID or Epic ID is required.");
    }

    if (/^[0-9a-fA-F]{32}$/.test(trimmed)) {
      const epicBytes = Buffer.alloc(trimmed.length * 2);
      for (let i = 0; i < trimmed.length; i += 1) {
        epicBytes[i * 2] = trimmed.charCodeAt(i);
        epicBytes[i * 2 + 1] = 0x00;
      }

      const key = Buffer.from(this.BASE_KEY);
      const length = Math.min(epicBytes.length, key.length);
      for (let i = 0; i < length; i += 1) {
        key[i] ^= epicBytes[i];
      }
      return key;
    }

    const sidStr = trimmed.replace(/\D/g, "");
    if (!sidStr) {
      throw new Error("Steam ID must contain digits, or use a 32-character Epic ID.");
    }

    const sidBytes = Buffer.allocUnsafe(8);
    sidBytes.writeBigUInt64LE(BigInt(sidStr), 0);

    const key = Buffer.from(this.BASE_KEY);
    for (let i = 0; i < 8; i += 1) {
      key[i] ^= sidBytes[i];
    }
    return key;
  }

  static decryptSavToYaml(ciphertext, steamid) {
    const cipherLen = ciphertext.length;
    if (cipherLen % 16 !== 0) {
      throw new Error(`Input .sav size ${cipherLen} not multiple of 16.`);
    }

    const key = this.deriveKey(steamid);
    const decipher = crypto.createDecipheriv("aes-256-ecb", key, null);
    decipher.setAutoPadding(false);

    const paddedPlaintext = Buffer.concat([decipher.update(ciphertext), decipher.final()]);
    const body = this.unpad(paddedPlaintext, 16);

    if (body.length >= 8) {
      const compressedData = body.slice(0, -8);
      const lengthBytes = body.slice(-4);
      let lastError = null;

      try {
        const decompressed = zlib.inflateSync(compressedData);
        const expectedLength = lengthBytes.readUInt32LE(0);
        if (decompressed.length !== expectedLength) {
          // Keep behavior non-fatal, matching Matt's implementation.
        }
        return decompressed;
      } catch (error) {
        lastError = error;
      }

      for (const attempt of [
        () => zlib.inflateSync(body),
        () => zlib.inflateSync(paddedPlaintext),
        () => zlib.inflateRawSync(compressedData),
        () => zlib.gunzipSync(compressedData)
      ]) {
        try {
          return attempt();
        } catch (error) {
          lastError = error;
        }
      }

      throw new Error(
        `Zlib decompression failed during decrypt. Tried zlib, raw deflate, and gzip formats. Last error: ${
          lastError ? lastError.message : "unknown"
        }`
      );
    }

    try {
      return zlib.inflateSync(body);
    } catch (error) {
      try {
        return zlib.inflateSync(paddedPlaintext);
      } catch {
        throw new Error(`Zlib decompression failed: data too short or invalid. Last error: ${error.message}`);
      }
    }
  }

  static adler32(data) {
    let a = 1;
    let b = 0;
    for (let i = 0; i < data.length; i += 1) {
      a = (a + data[i]) % 65521;
      b = (b + a) % 65521;
    }
    return ((b << 16) | a) >>> 0;
  }

  static encryptYamlToSav(yamlData, steamid) {
    const yamlBuffer = Buffer.isBuffer(yamlData) ? yamlData : Buffer.from(String(yamlData || ""), "utf8");
    if (!yamlBuffer.length) {
      throw new Error("YAML content is required.");
    }

    const compressed = zlib.deflateSync(yamlBuffer, { level: 9 });
    const adler32 = this.adler32(yamlBuffer);

    const adler32Buffer = Buffer.allocUnsafe(4);
    adler32Buffer.writeUInt32LE(adler32, 0);
    const lengthBuffer = Buffer.allocUnsafe(4);
    lengthBuffer.writeUInt32LE(yamlBuffer.length, 0);

    const packed = Buffer.concat([compressed, adler32Buffer, lengthBuffer]);
    const padded = this.pad(packed, 16);

    const key = this.deriveKey(steamid);
    const cipher = crypto.createCipheriv("aes-256-ecb", key, null);
    cipher.setAutoPadding(false);
    return Buffer.concat([cipher.update(padded), cipher.final()]);
  }

  static pad(data, blockSize) {
    const pad = blockSize - (data.length % blockSize);
    return Buffer.concat([data, Buffer.alloc(pad, pad)]);
  }

  static unpad(data, blockSize) {
    const pad = data[data.length - 1];
    if (pad < 1 || pad > blockSize) {
      return data;
    }
    return data.slice(0, -pad);
  }
}

function normalizedBase64(value) {
  const text = String(value || "").trim();
  const marker = "base64,";
  const markerIndex = text.indexOf(marker);
  return markerIndex >= 0 ? text.slice(markerIndex + marker.length) : text;
}

function yamlFromPayload(payload) {
  if (typeof payload.yaml_content === "string") {
    return payload.yaml_content;
  }
  if (typeof payload.yaml_data === "string") {
    return payload.yaml_data;
  }
  if (payload.yaml_data && typeof payload.yaml_data === "object") {
    return JSON.stringify(payload.yaml_data, null, 2);
  }
  return "";
}

function run(payload) {
  const command = String(payload.command || "").trim().toLowerCase();
  const steamid = payload.steamid || payload.steam_id || payload.user_id || "";

  if (command === "decrypt") {
    const savData = normalizedBase64(payload.sav_data || payload.save_data || payload.profile_data || "");
    if (!savData) {
      throw new Error("sav_data is required.");
    }
    const yaml = Encryption.decryptSavToYaml(Buffer.from(savData, "base64"), steamid).toString("utf8");
    return {
      success: true,
      yaml_content: yaml,
      message: "Save/profile decrypted locally."
    };
  }

  if (command === "encrypt") {
    const yaml = yamlFromPayload(payload);
    const sav = Encryption.encryptYamlToSav(yaml, steamid).toString("base64");
    return {
      success: true,
      sav_data: sav,
      encrypted: sav,
      message: "Save/profile encrypted locally."
    };
  }

  throw new Error(`Unsupported blcrypt command: ${command || "(blank)"}`);
}

function readStdin() {
  return new Promise((resolve, reject) => {
    let body = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => {
      body += chunk;
    });
    process.stdin.on("error", reject);
    process.stdin.on("end", () => resolve(body));
  });
}

async function main() {
  try {
    const body = await readStdin();
    const payload = JSON.parse(body || "{}");
    const result = run(payload && typeof payload === "object" ? payload : {});
    process.stdout.write(JSON.stringify(result));
  } catch (error) {
    process.stdout.write(
      JSON.stringify({
        success: false,
        error: error && error.message ? error.message : String(error)
      })
    );
  }
}

main();
