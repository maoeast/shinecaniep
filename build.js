#!/usr/bin/env node
/**
 * 一键打包脚本
 *
 * 用法：
 *   node build.js <中文名称> <英文名称> <版本号>
 *
 * 示例：
 *   node build.js "认知评估与训练仪" "Cognitive Assessment and Training" "1.0.2"
 *
 * 会自动同步到以下文件的所有相关位置：
 *   - src-tauri/tauri.conf.json  (productName, version)
 *   - src-tauri/Cargo.toml       (name, version, description)
 *   - src-tauri/src/main.rs      (窗口标题 .title)
 *   - dist/config.json           (systemName, systemNameEn)
 *   - dist/index.html            (<title>)
 *
 * 同步完成后自动执行 cargo tauri build 打包。
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// =============================================
//   参数解析
// =============================================
const args = process.argv.slice(2);

if (args.length < 3) {
  console.log('用法: node build.js <中文名称> <英文名称> <版本号> [copyright] [logo路径]');
  console.log('');
  console.log('示例:');
  console.log('  node build.js "认知评估与训练仪" "Cognitive Assessment and Training" "1.0.2"');
  console.log('  node build.js "认知评估与训练仪" "Cognitive Assessment and Training" "1.0.2" "杭州炫灿科技有限公司"');
  process.exit(1);
}

const SYSTEM_NAME = args[0];
const SYSTEM_NAME_EN = args[1];
const VERSION = args[2];
const COPYRIGHT = args[3] || '';

// 验证版本号格式
if (!/^\d+\.\d+\.\d+/.test(VERSION)) {
  console.error(`❌ 版本号格式无效: "${VERSION}"，应为 x.y.z 格式`);
  process.exit(1);
}

const ROOT = path.resolve(__dirname);

console.log('========================================');
console.log('  一键打包配置');
console.log('========================================');
console.log(`  中文名: ${SYSTEM_NAME}`);
console.log(`  英文名: ${SYSTEM_NAME_EN}`);
console.log(`  版本号: ${VERSION}`);
if (COPYRIGHT) console.log(`  copyright: ${COPYRIGHT}`);
console.log('========================================\n');

// =============================================
//   1. src-tauri/tauri.conf.json
// =============================================
function updateTauriConf() {
  const filePath = path.join(ROOT, 'src-tauri', 'tauri.conf.json');
  let content = fs.readFileSync(filePath, 'utf-8');
  const original = content;

  content = content.replace(
    /"productName"\s*:\s*"[^"]*"/,
    `"productName": "${SYSTEM_NAME}"`
  );
  content = content.replace(
    /"version"\s*:\s*"[^"]*"/,
    `"version": "${VERSION}"`
  );
  if (COPYRIGHT) {
    content = content.replace(
      /"copyright"\s*:\s*"[^"]*"/,
      `"copyright": "${COPYRIGHT}"`
    );
  }

  if (content !== original) {
    fs.writeFileSync(filePath, content, 'utf-8');
    console.log(`[✓] src-tauri/tauri.conf.json → productName="${SYSTEM_NAME}", version="${VERSION}"${COPYRIGHT ? `, copyright="${COPYRIGHT}"` : ''}`);
  } else {
    console.log(`[=] src-tauri/tauri.conf.json → 无变化`);
  }
}

// =============================================
//   2. src-tauri/Cargo.toml
// =============================================
function updateCargoToml() {
  const filePath = path.join(ROOT, 'src-tauri', 'Cargo.toml');
  let content = fs.readFileSync(filePath, 'utf-8');
  const original = content;

  content = content.replace(
    /^name\s*=\s*"[^"]*"/m,
    `name = "${SYSTEM_NAME}"`
  );
  content = content.replace(
    /^version\s*=\s*"[^"]*"/m,
    `version = "${VERSION}"`
  );
  content = content.replace(
    /^description\s*=\s*"[^"]*"/m,
    `description = "${SYSTEM_NAME}"`
  );

  if (content !== original) {
    fs.writeFileSync(filePath, content, 'utf-8');
    console.log(`[✓] src-tauri/Cargo.toml → name="${SYSTEM_NAME}", version="${VERSION}", description="${SYSTEM_NAME}"`);
  } else {
    console.log(`[=] src-tauri/Cargo.toml → 无变化`);
  }
}

// =============================================
//   3. src-tauri/src/main.rs (窗口标题)
// =============================================
function updateMainRs() {
  const filePath = path.join(ROOT, 'src-tauri', 'src', 'main.rs');
  let content = fs.readFileSync(filePath, 'utf-8');
  const original = content;

  // 匹配 .title("...") —— 窗口标题
  content = content.replace(
    /\.title\("[^"]*"\)/,
    `.title("${SYSTEM_NAME}")`
  );

  if (content !== original) {
    fs.writeFileSync(filePath, content, 'utf-8');
    console.log(`[✓] src-tauri/src/main.rs → 窗口标题="${SYSTEM_NAME}"`);
  } else {
    console.log(`[=] src-tauri/src/main.rs → 无变化`);
  }
}

// =============================================
//   4. dist/config.json
// =============================================
function updateDistConfig() {
  const filePath = path.join(ROOT, 'dist', 'config.json');
  const raw = fs.readFileSync(filePath, 'utf-8');
  const config = JSON.parse(raw);

  let changed = false;
  if (config.systemName !== SYSTEM_NAME) {
    config.systemName = SYSTEM_NAME;
    changed = true;
  }
  if (config.systemNameEn !== SYSTEM_NAME_EN) {
    config.systemNameEn = SYSTEM_NAME_EN;
    changed = true;
  }
  if (COPYRIGHT && config.copyright !== COPYRIGHT) {
    config.copyright = COPYRIGHT;
    changed = true;
  }

  if (changed) {
    fs.writeFileSync(filePath, JSON.stringify(config, null, 2), 'utf-8');
    console.log(`[✓] dist/config.json → systemName="${SYSTEM_NAME}", systemNameEn="${SYSTEM_NAME_EN}"${COPYRIGHT ? `, copyright="${COPYRIGHT}"` : ''}`);
  } else {
    console.log(`[=] dist/config.json → 无变化`);
  }
}

// =============================================
//   5. dist/index.html (<title>)
// =============================================
function updateDistIndexTitle() {
  const filePath = path.join(ROOT, 'dist', 'index.html');
  let html = fs.readFileSync(filePath, 'utf-8');
  const original = html;

  html = html.replace(
    /<title>[^<]*<\/title>/,
    `<title>${SYSTEM_NAME}</title>`
  );

  if (html !== original) {
    fs.writeFileSync(filePath, html, 'utf-8');
    console.log(`[✓] dist/index.html → <title>="${SYSTEM_NAME}"`);
  } else {
    console.log(`[=] dist/index.html → 无变化`);
  }
}

// =============================================
//   6. 执行 cargo tauri build
// =============================================
function buildTauri() {
  console.log('\n========================================');
  console.log('  开始编译打包 ...');
  console.log('========================================\n');

  const cargoDir = path.join(ROOT, 'src-tauri');
  execSync('cargo tauri build', {
    cwd: cargoDir,
    stdio: 'inherit',
    timeout: 10 * 60 * 1000,  // 10 分钟超时
  });
}

// =============================================
//   执行
// =============================================
try {
  updateTauriConf();
  updateCargoToml();
  updateMainRs();
  updateDistConfig();
  updateDistIndexTitle();

  console.log('\n✅ 所有配置已同步，开始打包...\n');
  buildTauri();

  // 计算输出路径
  const exeName = `${SYSTEM_NAME}.exe`;
  const setupName = `${SYSTEM_NAME}_${VERSION}_x64-setup.exe`;
  const releaseDir = path.join(ROOT, 'src-tauri', 'target', 'release');
  const nsisDir = path.join(releaseDir, 'bundle', 'nsis');

  console.log('\n========================================');
  console.log('  ✅ 打包完成！');
  console.log('========================================');
  console.log(`  可执行文件: ${path.join(releaseDir, exeName)}`);
  console.log(`  安装包:     ${path.join(nsisDir, setupName)}`);
  console.log('========================================');
} catch (err) {
  console.error('\n❌ 出错：', err.message);
  process.exit(1);
}
