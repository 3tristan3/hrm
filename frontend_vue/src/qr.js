// 二维码页面脚本：根据表单地址生成可扫码访问的二维码。
import QRCode from "qrcode";
import { FORM_URL } from "./config/runtime";

const formUrl = FORM_URL;

const container = document.getElementById("qr-app");

container.innerHTML = `
  <div class="qr-page">
    <div class="qr-card">
      <p class="qr-eyebrow">扫码入口</p>
      <h1>应聘信息填报</h1>
      <p class="qr-subtitle">请使用手机扫描二维码，进入信息填写页面。</p>
      <div class="qr-canvas-wrap">
        <canvas id="qr-canvas"></canvas>
      </div>
      <p class="qr-url" id="qr-url"></p>
      <div class="qr-actions">
        <a class="qr-link" href="${formUrl}" target="_blank" rel="noreferrer">
          直接打开填写页面
        </a>
        <button class="qr-button" id="copy-button">复制链接</button>
      </div>
    </div>
  </div>
  <style>
    :root {
      font-family: "IBM Plex Sans", "Noto Sans SC", sans-serif;
      color: #201a14;
      background: #f6efe6;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
    }

    .qr-page {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 40px 16px;
    }

    .qr-card {
      width: min(460px, 100%);
      background: #fff;
      border-radius: 24px;
      padding: 32px;
      box-shadow: 0 24px 60px rgba(78, 52, 30, 0.18);
      text-align: center;
    }

    .qr-eyebrow {
      text-transform: uppercase;
      letter-spacing: 0.3em;
      font-size: 0.7rem;
      margin: 0 0 12px;
      color: #7a5c43;
    }

    h1 {
      font-family: "Cormorant Garamond", "Noto Serif SC", serif;
      font-size: 2rem;
      margin: 0 0 8px;
    }

    .qr-subtitle {
      margin: 0 0 24px;
      color: #5a4635;
    }

    .qr-canvas-wrap {
      display: flex;
      justify-content: center;
      padding: 16px;
      border-radius: 18px;
      background: rgba(124, 84, 54, 0.08);
    }

    .qr-url {
      margin: 18px 0 0;
      font-size: 0.85rem;
      color: #5a4635;
      word-break: break-all;
    }

    .qr-actions {
      margin-top: 18px;
      display: flex;
      justify-content: center;
      gap: 12px;
      flex-wrap: wrap;
    }

    .qr-link,
    .qr-button {
      border-radius: 999px;
      padding: 10px 18px;
      border: 1px solid #2a1c12;
      background: transparent;
      color: #2a1c12;
      font-size: 0.9rem;
      cursor: pointer;
      text-decoration: none;
    }

    .qr-button {
      background: #2a1c12;
      color: #fff;
      border-color: #2a1c12;
    }
  </style>
`;

const urlLabel = document.getElementById("qr-url");
if (urlLabel) {
  urlLabel.textContent = formUrl;
}

const canvas = document.getElementById("qr-canvas");
QRCode.toCanvas(canvas, formUrl, {
  width: 240,
  margin: 1,
  color: {
    dark: "#2a1c12",
    light: "#ffffff",
  },
});

const copyButton = document.getElementById("copy-button");
if (copyButton) {
  copyButton.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(formUrl);
      copyButton.textContent = "已复制";
      setTimeout(() => {
        copyButton.textContent = "复制链接";
      }, 1600);
    } catch (err) {
      window.alert("复制失败，请手动复制链接");
    }
  });
}

