/**
 * 打包前置配置脚本
 * 运行方式：node build.js
 *
 * 只需修改下方 SYSTEM_NAME，脚本会自动同步到：
 *  - dist/config.json     (systemName)
 *  - dist/index.html      (<title>)
 *  - src-tauri/Cargo.toml (description)
 */

const fs = require('fs');
const path = require('path');

// =============================================
//   在这里修改系统名称（一处搞定）
// =============================================
const SYSTEM_NAME = '资源教室管理系统-IEP';
// =============================================

const ROOT = path.resolve(__dirname);

// 1. 更新 dist/config.json 的 systemName
function updateConfigJson() {
  const configPath = path.join(ROOT, 'dist', 'config.json');
  const raw = fs.readFileSync(configPath, 'utf-8');
  const config = JSON.parse(raw);
  config.systemName = SYSTEM_NAME;
  fs.writeFileSync(configPath, JSON.stringify(config, null, 2), 'utf-8');
  console.log(`[✓] dist/config.json → systemName = "${SYSTEM_NAME}"`);
}

// 2. 更新 dist/index.html 的 <title>
function updateDistIndexTitle() {
  const htmlPath = path.join(ROOT, 'dist', 'index.html');
  let html = fs.readFileSync(htmlPath, 'utf-8');
  html = html.replace(/<title>[^<]*<\/title>/, `<title>${SYSTEM_NAME}</title>`);
  fs.writeFileSync(htmlPath, html, 'utf-8');
  console.log(`[✓] dist/index.html → <title> = "${SYSTEM_NAME}"`);
}

// 3. 更新 src-tauri/Cargo.toml 的 description
function updateCargoToml() {
  const cargoPath = path.join(ROOT, 'src-tauri', 'Cargo.toml');
  let toml = fs.readFileSync(cargoPath, 'utf-8');
  toml = toml.replace(
    /^description\s*=\s*"[^"]*"/m,
    `description = "${SYSTEM_NAME}"`
  );
  fs.writeFileSync(cargoPath, toml, 'utf-8');
  console.log(`[✓] src-tauri/Cargo.toml → description = "${SYSTEM_NAME}"`);
}

// 执行
try {
  updateConfigJson();
  updateDistIndexTitle();
  updateCargoToml();
  console.log('\n✅ 所有配置已同步，可以开始打包。');
} catch (err) {
  console.error('\n❌ 出错：', err.message);
  process.exit(1);
}
