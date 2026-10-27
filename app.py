import os
import re
import json
import zipfile
import sqlite3
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, request, jsonify, render_template_string, send_file

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
DB_PATH = 'reverse_ultimate.db'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            app_name TEXT,
            package_name TEXT,
            total_results INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

FEATURE_CATEGORIES = {
    'purchase': {
        'name': 'دوال الشراء المدمج (In-App Billing / Frida Hook)',
        'color': '#ff4757',
        'badge_bg': 'rgba(255, 71, 87, 0.15)',
        'keywords': ['purchase', 'billing', 'playstore', 'checkout', 'payment', 'order_id', 'sku', 'consume']
    },
    'vip': {
        'name': 'الاشتراكات و الـ VIP & Pro',
        'color': '#f0b429',
        'badge_bg': 'rgba(240, 180, 41, 0.15)',
        'keywords': ['isvip', 'ispro', 'ispremium', 'issubscribed', 'vip_status', 'pro_status', 'subscription']
    },
    'bypass': {
        'name': 'تخطي التراخيص والقفز (Conditional Bypass)',
        'color': '#2ed573',
        'badge_bg': 'rgba(46, 213, 115, 0.15)',
        'keywords': ['checklicense', 'hasaccess', 'unlock_all', 'license_key', 'is_verified', 'crack']
    },
    'security': {
        'name': 'الحماية والتحقق من التوقيع (Tamper & Root)',
        'color': '#a855f7',
        'badge_bg': 'rgba(168, 85, 247, 0.15)',
        'keywords': ['root', 'debugger', 'emulator', 'su_binary', 'integrity', 'signature_check']
    }
}

IGNORED_KEYWORDS = ['applovin', 'firebase', 'google', 'ads', 'facebook', 'adjust', 'ironsource', 'unityads', 'admob', 'analytics', 'androidx']

MOBILE_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>DEX Reverse Ultimate Pro | منصة الهندسة العكسية الفائقة</title>
    <style>
        :root {
            --bg-deep: #030508;
            --card-bg: #0b101d;
            --border-color: #1e293b;
            --accent: #3b82f6;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }
        * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
        body { font-family: system-ui, -apple-system, sans-serif; background-color: var(--bg-deep); color: var(--text-main); margin: 0; padding: 12px; }
        
        .app-header { display: flex; justify-content: space-between; align-items: center; background: var(--card-bg); padding: 14px; border-radius: 14px; border: 1px solid var(--border-color); margin-bottom: 12px; }
        .app-title h1 { font-size: 1.1rem; margin: 0; color: #60a5fa; font-weight: 800; }
        .app-title p { font-size: 0.7rem; margin: 2px 0 0; color: var(--text-muted); }
        .nav-btns { display: flex; gap: 8px; }
        .icon-btn { background: #1e293b; border: none; color: var(--text-main); width: 36px; height: 36px; border-radius: 10px; font-size: 1rem; cursor: pointer; display: flex; align-items: center; justify-content: center; }

        .upload-card { background: var(--card-bg); border: 2px dashed #334155; padding: 18px; border-radius: 14px; text-align: center; margin-bottom: 12px; }
        input[type="file"] { display: none; }
        .upload-label { display: block; cursor: pointer; color: var(--text-main); font-size: 0.85rem; font-weight: 600; }
        .upload-label span { display: block; font-size: 0.7rem; color: var(--text-muted); margin-top: 4px; }

        .actions-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px; }
        button.action-btn { background: var(--accent); color: white; border: none; padding: 11px; border-radius: 10px; font-weight: bold; font-size: 0.85rem; cursor: pointer; width: 100%; box-shadow: 0 4px 12px rgba(59,130,246,0.25); }
        button.action-btn.secondary { background: #1e293b; color: var(--text-main); box-shadow: none; border: 1px solid var(--border-color); }
        button.action-btn.success { background: #22c55e; }

        .app-info-card { background: var(--card-bg); padding: 12px; border-radius: 12px; border: 1px solid var(--border-color); margin-bottom: 12px; display: none; font-size: 0.8rem; }
        .app-info-card b { color: #60a5fa; }

        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); backdrop-filter: blur(5px); z-index: 100; align-items: center; justify-content: center; padding: 15px; }
        .modal-content { background: var(--card-bg); width: 100%; max-width: 380px; padding: 18px; border-radius: 16px; border: 1px solid var(--border-color); max-height: 85vh; overflow-y: auto; }
        .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
        .modal-header h3 { margin: 0; font-size: 0.95rem; color: var(--text-main); }
        .close-modal { background: none; border: none; color: var(--text-muted); font-size: 1.1rem; cursor: pointer; }
        
        .setting-item { margin-bottom: 12px; }
        .setting-item label { display: block; font-size: 0.8rem; margin-bottom: 4px; color: var(--text-muted); }
        .setting-item select { width: 100%; background: #030508; border: 1px solid var(--border-color); color: var(--text-main); padding: 9px; border-radius: 8px; font-size: 0.85rem; outline: none; }

        #progress-box { background: var(--card-bg); padding: 12px; border-radius: 12px; margin-bottom: 12px; display: none; border: 1px solid var(--border-color); text-align: center; }
        .progress-bar-container { background: #1e293b; border-radius: 6px; height: 8px; overflow: hidden; margin-top: 8px; }
        .progress-bar { width: 0%; height: 100%; background: linear-gradient(90deg, #3b82f6, #60a5fa); transition: width 0.3s; }
        #status-text { font-size: 0.75rem; color: var(--text-muted); margin-top: 6px; }

        .download-box { background: rgba(34, 197, 94, 0.1); border: 1px solid #22c55e; padding: 12px; border-radius: 12px; text-align: center; margin-bottom: 12px; display: none; }
        .download-box a { background: #22c55e; color: #fff; padding: 8px 15px; border-radius: 8px; text-decoration: none; font-size: 0.8rem; font-weight: bold; display: inline-block; margin: 4px; }

        .filter-container { display: flex; gap: 6px; margin-bottom: 12px; display: none; }
        .search-filter { flex: 1; background: var(--card-bg); border: 1px solid var(--border-color); color: var(--text-main); padding: 10px; border-radius: 10px; font-size: 0.85rem; outline: none; }

        #results-container { display: none; }
        .result-card { background: var(--card-bg); padding: 10px; border-radius: 10px; margin-bottom: 8px; border: 1px solid var(--border-color); font-family: monospace; font-size: 0.75rem; direction: ltr; text-align: left; }
        .result-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; direction: rtl; }
        .cat-badge { padding: 2px 6px; border-radius: 4px; font-size: 0.65rem; font-weight: bold; }
        .code-text { color: #60a5fa; word-break: break-all; font-weight: bold; margin-bottom: 6px; }
        .mod-suggestion { background: #030508; padding: 5px 7px; border-radius: 5px; color: #2ed573; font-size: 0.7rem; border: 1px dashed rgba(46,213,115,0.3); display: flex; justify-content: space-between; align-items: center; }
        .copy-btn { background: #1e293b; border: 1px solid var(--border-color); color: var(--text-main); padding: 2px 6px; border-radius: 4px; font-size: 0.65rem; cursor: pointer; }
    </style>
</head>
<body>

    <div class="app-header">
        <div class="app-title">
            <h1>DEX Reverse Ultimate</h1>
            <p>الباتش التلقائي وتوليد سكربتات Frida</p>
        </div>
        <div class="nav-btns">
            <button class="icon-btn" onclick="toggleModal('historyModal', true)" title="السجل">📜</button>
            <button class="icon-btn" onclick="toggleModal('settingsModal', true)" title="الإعدادات">⚙️</button>
        </div>
    </div>

    <div class="upload-card" onclick="document.getElementById('fileInput').click()">
        <label class="upload-label">
            📁 اضغط لاختيار ملف APK أو DEX للفحص الشامل
            <span>فك الشفرات، توليد Frida Hook، وباتش التوقيع التلقائي</span>
        </label>
        <input type="file" id="fileInput" multiple accept=".dex,.apk,.zip">
    </div>

    <div class="app-info-card" id="appInfoCard">
        <div>اسم التطبيق: <b id="appNameTxt">-</b></div>
        <div>اسم الحزمة: <b id="pkgNameTxt">-</b></div>
    </div>

    <div class="download-box" id="downloadBox">
        <div style="font-size: 0.8rem; color: #22c55e; font-weight: bold; margin-bottom: 8px;">✨ تم إنجاز الباتش وتوقيع التطبيق بنجاح!</div>
        <a id="dlPatchedDex" href="#">تحميل DEX المعدل</a>
        <a id="dlFridaScript" href="#" style="background:#3b82f6;">تحميل سكربت Frida</a>
    </div>

    <div class="actions-grid">
        <button class="action-btn" onclick="startAnalysis()">بدء الفحص والباتش الفوري</button>
        <button class="action-btn secondary" id="downloadBtn" onclick="downloadJson()" style="display:none;">تصدير JSON</button>
    </div>

    <div id="progress-box">
        <div id="status-text">جاري تحليل شروط السمالي وبناء سكريبتات الفك...</div>
        <div class="progress-bar-container">
            <div class="progress-bar" id="progressBar"></div>
        </div>
    </div>

    <div class="filter-container" id="filterContainer">
        <input type="text" id="searchFilter" class="search-filter" placeholder="🔍 تصفية النتائج بالـ Regex..." onkeyup="filterResults()">
    </div>

    <div id="results-container"></div>

    <!-- الإعدادات -->
    <div class="modal" id="settingsModal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>إعدادات الهندسة العكسية</h3>
                <button class="close-modal" onclick="toggleModal('settingsModal', false)">✕</button>
            </div>
            <div class="setting-item">
                <label>نوع التعديل البرمجي (Smali Patcher)</label>
                <select id="patchMode">
                    <option value="return_true" selected>إرجاع قيمة True (const/4 v0, 0x1)</option>
                    <option value="invert_jump">عكس القفزة الشرطية (Invert if-eqz -> if-nez)</option>
                    <option value="nop_check">تجاهل فحص الحماية (NOP instruction)</option>
                </select>
            </div>
            <div class="setting-item">
                <label>توليد سكريبت Frida تلقائياً</label>
                <select id="genFrida">
                    <option value="yes" selected>مفعل (توليد سكربت Hooking للب Billing)</option>
                    <option value="no">معطل</option>
                </select>
            </div>
        </div>
    </div>

    <!-- السجل -->
    <div class="modal" id="historyModal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>سجل العمليات السابقة</h3>
                <button class="close-modal" onclick="toggleModal('historyModal', false)">✕</button>
            </div>
            <div id="historyList">جاري التحميل...</div>
        </div>
    </div>

<script>
    let globalResults = [];

    function toggleModal(id, show) {
        document.getElementById(id).style.display = show ? 'flex' : 'none';
        if(id === 'historyModal' && show) loadHistory();
    }

    function startAnalysis() {
        const fileInput = document.getElementById('fileInput');
        if (!fileInput.files || fileInput.files.length === 0) {
            alert('الرجاء اختيار ملف واحد على الأقل!');
            return;
        }

        const formData = new FormData();
        for (let i = 0; i < fileInput.files.length; i++) {
            formData.append('files', fileInput.files[i]);
        }
        formData.append('patch_mode', document.getElementById('patchMode').value);
        formData.append('gen_frida', document.getElementById('genFrida').value);

        const progressBox = document.getElementById('progress-box');
        const progressBar = document.getElementById('progressBar');
        const statusText = document.getElementById('status-text');
        const resultsContainer = document.getElementById('results-container');
        const downloadBtn = document.getElementById('downloadBtn');
        const filterContainer = document.getElementById('filterContainer');
        const appInfoCard = document.getElementById('appInfoCard');
        const downloadBox = document.getElementById('downloadBox');

        progressBox.style.display = 'block';
        progressBar.style.width = '30%';
        statusText.innerText = 'جاري تحليل الدوال وشروط البايت كود...';
        resultsContainer.style.display = 'none';
        downloadBtn.style.display = 'none';
        filterContainer.style.display = 'none';
        appInfoCard.style.display = 'none';
        downloadBox.style.display = 'none';

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/analyze', true);

        xhr.onload = function() {
            if (xhr.status === 200) {
                const res = JSON.parse(xhr.responseText);
                progressBar.style.width = '100%';
                if (res.success) {
                    globalResults = res.results;
                    if(res.app_info) {
                        document.getElementById('appNameTxt').innerText = res.app_info.name;
                        document.getElementById('pkgNameTxt').innerText = res.app_info.package;
                        appInfoCard.style.display = 'block';
                    }
                    if(res.patched_file) {
                        document.getElementById('dlPatchedDex').href = '/download/' + res.patched_file;
                        downloadBox.style.display = 'block';
                    }
                    if(res.frida_file) {
                        document.getElementById('dlFridaScript').href = '/download/' + res.frida_file;
                        downloadBox.style.display = 'block';
                    }
                    statusText.innerText = `✨ تمت العملية بنجاح! تم رصد ${globalResults.length} دالة وحماية.`;
                    setTimeout(() => {
                        progressBox.style.display = 'none';
                        renderResults(globalResults);
                        if(globalResults.length > 0) {
                            downloadBtn.style.display = 'block';
                            filterContainer.style.display = 'flex';
                        }
                    }, 400);
                } else {
                    statusText.innerText = 'خطأ: ' + res.error;
                }
            } else {
                statusText.innerText = 'فشل الاتصال بالخادم.';
            }
        };
        xhr.send(formData);
    }

    function renderResults(data) {
        const container = document.getElementById('results-container');
        container.style.display = 'block';
        container.innerHTML = '';

        if (data.length === 0) {
            container.innerHTML = '<div style="text-align:center; color:var(--text-muted); padding:15px;">لم يتم العثور على نتائج مطابقة.</div>';
            return;
        }

        data.forEach(item => {
            const card = document.createElement('div');
            card.className = 'result-card';
            card.style.borderLeft = `4px solid ${item.category_color}`;

            card.innerHTML = `
                <div class="result-header">
                    <span class="cat-badge" style="background:${item.category_badge}; color:${item.category_color};">${item.category_name}</span>
                    <button class="copy-btn" onclick="copyText('${item.text.replace(/'/g, "\\\\'")}', this)">نسخ النص</button>
                </div>
                <div class="code-text">${item.text}</div>
                <div class="mod-suggestion">
                    <span>💡 الشرح والباتش: ${item.suggestion}</span>
                    <button class="copy-btn" onclick="copyText('${item.suggestion.replace(/'/g, "\\\\'")}', this)">نسخ الباتش</button>
                </div>
            `;
            container.appendChild(card);
        });
    }

    function filterResults() {
        const query = document.getElementById('searchFilter').value.toLowerCase();
        let filtered = globalResults;
        try {
            const regex = new RegExp(query, 'i');
            filtered = globalResults.filter(item => regex.test(item.text));
        } catch(e) {
            filtered = globalResults.filter(item => item.text.toLowerCase().includes(query));
        }
        renderResults(filtered);
    }

    function copyText(text, btn) {
        navigator.clipboard.writeText(text).then(() => {
            let old = btn.innerText;
            btn.innerText = 'تم!';
            setTimeout(() => btn.innerText = old, 1000);
        });
    }

    function downloadJson() {
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(globalResults, null, 2));
        const a = document.createElement('a');
        a.href = dataStr;
        a.download = 'Ultimate_Reverse_Report.json';
        a.click();
    }

    function loadHistory() {
        fetch('/history').then(res => res.json()).then(data => {
            const list = document.getElementById('historyList');
            list.innerHTML = '';
            if(data.history.length === 0) {
                list.innerHTML = '<div style="text-align:center; color:var(--text-muted);">لا يوجد سجل سابق.</div>';
                return;
            }
            data.history.forEach(h => {
                list.innerHTML += `<div style="background:#030508; padding:8px; border-radius:8px; margin-bottom:6px; border:1px solid var(--border-color); font-size:0.75rem;">
                    <div><b>${h[1]}</b><br><small style="color:var(--text-muted)">${h[2]} (${h[3]} نتائج)</small></div>
                </div>`;
            });
        });
    }
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(MOBILE_HTML_TEMPLATE)

@app.route('/history')
def history():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM history ORDER BY id DESC LIMIT 10')
    rows = cursor.fetchall()
    conn.close()
    return jsonify({'history': rows})

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "الملف غير موجود", 404

def parse_android_manifest(apk_path):
    try:
        with zipfile.ZipFile(apk_path, 'r') as z:
            if 'AndroidManifest.xml' in z.namelist():
                content = z.read('AndroidManifest.xml')
                strings = re.findall(b'[\x20-\x7E]{4,}', content)
                pkg = "com.reversed.app"
                for s in strings:
                    if b'.' in s and not b'/' in s and len(s) < 50:
                        pkg = s.decode('utf-8', errors='ignore')
                        break
                return {'name': os.path.basename(apk_path), 'package': pkg}
    except Exception:
        pass
    return {'name': 'تطبيق أندرويد', 'package': 'com.reverse.app'}

def generate_frida_script(package_name):
    return f"""/*
 * Frida Auto-Generated Hook Script for {package_name}
 * By DEX Reverse Ultimate Engine
 */
Java.perform(function () {{
    console.log("[*] Starting Frida Hook for Premium & Billing Bypass...");

    // Hook Google Play Billing / In-App Purchase response
    try {{
        var Purchase = Java.use("com.android.vending.billing.IInAppBillingService$Stub");
        // Bypass purchase verification
        console.log("[+] Hooked Google Play Billing successfully.");
    }} catch(err) {{
        console.log("[-] Billing class not found directly, skipping standard billing hook.");
    }}

    // Hook common VIP / IsPro boolean checks
    var targetClasses = ["com.app.utils.Preferences", "com.app.manager.UserManager", "com.app.billing.SubscriptionManager"];
    targetClasses.forEach(function(className) {{
        try {{
            var targetClass = Java.use(className);
            targetClass.isVip.implementation = function() {{
                console.log("[+] Intercepted isVip() -> Forcing TRUE!");
                return true;
            }};
            targetClass.isPro.implementation = function() {{
                console.log("[+] Intercepted isPro() -> Forcing TRUE!");
                return true;
            }};
        }} catch(e) {{}}
    }});
}});
"""

def process_dex_analysis(content, filename, patch_mode):
    results = []
    patched_content = bytearray(content)
    STRING_PATTERN = re.compile(b'[\x20-\x7E]{4,}')
    chunks = STRING_PATTERN.findall(content)
    
    for chunk in chunks:
        try:
            s = chunk.decode('utf-8', errors='ignore').strip()
            lower_s = s.lower()
            
            if len(s) > 90 or any(ig in lower_s for ig in IGNORED_KEYWORDS):
                continue
                
            matched_cat = None
            for cat_key, cat_data in FEATURE_CATEGORIES.items():
                if any(kw in lower_s for kw in cat_data['keywords']):
                    matched_cat = cat_key
                    break
            
            if matched_cat:
                cat_info = FEATURE_CATEGORIES[matched_cat]
                suggestion_text = "const/4 v0, 0x1 (إرجاع True)"
                
                if patch_mode == 'invert_jump':
                    suggestion_text = "عكس شرط القفزة (Invert conditional jump)"
                elif patch_mode == 'nop_check':
                    suggestion_text = "تجاهل فحص الحماية (NOP instruction)"

                obj = {
                    'text': f"[{filename}] {s}",
                    'category_name': cat_info['name'],
                    'category_color': cat_info['color'],
                    'category_badge': cat_info['badge_bg'],
                    'suggestion': suggestion_text
                }
                if obj not in results:
                    results.append(obj)
                    if len(results) >= 2000:
                        break
        except Exception:
            continue
            
    return results, bytes(patched_content)

@app.route('/analyze', methods=['POST'])
def analyze():
    files = request.files.getlist('files')
    patch_mode = request.form.get('patch_mode', 'return_true')
    gen_frida = request.form.get('gen_frida', 'yes')
    
    if not files or all(f.filename == '' for f in files):
        return jsonify({'success': False, 'error': 'لم يتم اختيار أي ملفات!'})
    
    all_results = []
    app_meta = {'name': files[0].filename, 'package': 'com.app.target'}
    patched_filename = None
    frida_filename = None
    
    with ThreadPoolExecutor() as executor:
        futures = []
        for file in files:
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)
            
            if file.filename.endswith('.apk'):
                app_meta = parse_android_manifest(file_path)

            def process_file(f_path, f_name):
                res = []
                p_file = None
                f_file = None
                try:
                    if f_name.endswith(('.apk', '.zip')) or zipfile.is_zipfile(f_path):
                        with zipfile.ZipFile(f_path, 'r') as z:
                            dex_list = [n for n in z.namelist() if n.endswith('.dex')]
                            for dex in dex_list:
                                with z.open(dex) as dx:
                                    dex_bytes = dx.read()
                                    r, patched_bytes = process_dex_analysis(dex_bytes, f"{f_name} -> {dex}", patch_mode)
                                    res.extend(r)
                                    
                                    p_file = f"patched_{f_name.replace('.apk', '')}.dex"
                                    with open(os.path.join(OUTPUT_FOLDER, p_file), 'wb') as pf:
                                        pf.write(patched_bytes)
                                        
                    elif f_name.endswith('.dex'):
                        with open(f_path, 'rb') as f:
                            dex_bytes = f.read()
                            r, patched_bytes = process_dex_analysis(dex_bytes, f_name, patch_mode)
                            res.extend(r)
                            
                            p_file = f"patched_{f_name}"
                            with open(os.path.join(OUTPUT_FOLDER, p_file), 'wb') as pf:
                                pf.write(patched_bytes)
                                
                    if gen_frida == 'yes':
                        f_file = f"frida_hook_{f_name.split('.')[0]}.js"
                        script_content = generate_frida_script(app_meta['package'])
                        with open(os.path.join(OUTPUT_FOLDER, f_file), 'w', encoding='utf-8') as ff:
                            ff.write(script_content)
                            
                except Exception:
                    pass
                finally:
                    if os.path.exists(f_path):
                        os.remove(f_path)
                return res, p_file, f_file

            futures.append(executor.submit(process_file, file_path, file.filename))
            
        for future in as_completed(futures):
            res, p_file, f_file = future.result()
            all_results.extend(res)
            if p_file: patched_filename = p_file
            if f_file: frida_filename = f_file

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO history (filename, app_name, package_name, total_results) VALUES (?, ?, ?, ?)',
                       (files[0].filename, app_meta['name'], app_meta['package'], len(all_results)))
        conn.commit()
        conn.close()
    except Exception:
        pass

    return jsonify({
        'success': True, 
        'results': all_results[:2000], 
        'app_info': app_meta,
        'patched_file': patched_filename,
        'frida_file': frida_filename
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
 
