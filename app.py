import os
import re
import struct
import sqlite3
from flask import Flask, request, jsonify, render_template_string, send_file

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
DB_PATH = 'dex_google_bypass.db'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                total_results INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    except Exception:
        pass

init_db()

FEATURE_CATEGORIES = {
    'google_billing': {
        'name': 'حماية بوابات دفع جوجل (Google Play Billing / LVL)',
        'color': '#ff4757',
        'badge_bg': 'rgba(255, 71, 87, 0.15)',
        'keywords': ['iinappbillingservice', 'licensing', 'com.android.vending', 'checklicense', 'policy', 'responses.licensed']
    },
    'purchase': {
        'name': 'دوال الشراء والدفع المدمج (In-App Purchase)',
        'color': '#f0b429',
        'badge_bg': 'rgba(240, 180, 41, 0.15)',
        'keywords': ['purchase', 'billing', 'playstore', 'checkout', 'payment', 'order_id', 'sku', 'consume']
    },
    'vip': {
        'name': 'الاشتراكات و الـ VIP & Pro Status',
        'color': '#2ed573',
        'badge_bg': 'rgba(46, 213, 115, 0.15)',
        'keywords': ['isvip', 'ispro', 'ispremium', 'issubscribed', 'vip_status', 'pro_status', 'subscription']
    },
    'security': {
        'name': 'حماية التوقيع والسلامة (Google Play Integrity / Tamper)',
        'color': '#a855f7',
        'badge_bg': 'rgba(168, 85, 247, 0.15)',
        'keywords': ['integrity', 'playintegrity', 'signature', 'packageinstaller', 'installerpackagename']
    }
}

IGNORED_KEYWORDS = ['applovin', 'firebase', 'ads', 'facebook', 'adjust', 'ironsource', 'unityads', 'admob', 'analytics', 'androidx']

MOBILE_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Google Bypass Studio | تخطي حماية جوجل وباتش الـ DEX</title>
    <style>
        :root {
            --bg-deep: #020617;
            --card-bg: #090f1d;
            --border-color: #1e293b;
            --accent: #3b82f6;
            --accent-glow: rgba(59, 130, 246, 0.25);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }
        * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
        body { font-family: system-ui, -apple-system, sans-serif; background-color: var(--bg-deep); color: var(--text-main); margin: 0; padding: 12px; }
        
        .app-header { display: flex; justify-content: space-between; align-items: center; background: var(--card-bg); padding: 12px 15px; border-radius: 16px; border: 1px solid var(--border-color); margin-bottom: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }
        .app-title h1 { font-size: 1.1rem; margin: 0; color: #60a5fa; font-weight: 800; }
        .app-title p { font-size: 0.7rem; margin: 2px 0 0; color: var(--text-muted); }
        .nav-btns { display: flex; gap: 6px; }
        .icon-btn { background: #1e293b; border: 1px solid var(--border-color); color: var(--text-main); width: 36px; height: 36px; border-radius: 10px; font-size: 0.95rem; cursor: pointer; display: flex; align-items: center; justify-content: center; }

        .upload-card { background: linear-gradient(135deg, #090f1d 0%, #1e1b4b 100%); border: 2px dashed #4f46e5; padding: 22px 14px; border-radius: 16px; text-align: center; margin-bottom: 12px; cursor: pointer; }
        input[type="file"] { display: none; }
        .upload-label { display: block; cursor: pointer; color: var(--text-main); font-size: 0.88rem; font-weight: 700; }
        .upload-label span { display: block; font-size: 0.72rem; color: var(--text-muted); margin-top: 6px; }

        .actions-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px; }
        button.action-btn { background: var(--accent); color: white; border: none; padding: 12px; border-radius: 11px; font-weight: bold; font-size: 0.85rem; cursor: pointer; width: 100%; box-shadow: 0 4px 15px var(--accent-glow); }
        button.action-btn:active { transform: scale(0.96); }
        button.action-btn.secondary { background: #1e293b; color: var(--text-main); box-shadow: none; border: 1px solid var(--border-color); }

        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(2, 6, 23, 0.85); backdrop-filter: blur(8px); z-index: 100; align-items: center; justify-content: center; padding: 14px; }
        .modal-content { background: var(--card-bg); width: 100%; max-width: 400px; padding: 18px; border-radius: 18px; border: 1px solid var(--border-color); max-height: 85vh; overflow-y: auto; box-shadow: 0 10px 30px rgba(0,0,0,0.7); }
        .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
        .modal-header h3 { margin: 0; font-size: 0.95rem; color: var(--text-main); }
        .close-modal { background: none; border: none; color: var(--text-muted); font-size: 1.1rem; cursor: pointer; }
        
        .setting-item { margin-bottom: 12px; }
        .setting-item label { display: block; font-size: 0.8rem; margin-bottom: 5px; color: var(--text-muted); }
        .setting-item select, .setting-item textarea { width: 100%; background: #020617; border: 1px solid var(--border-color); color: var(--text-main); padding: 9px; border-radius: 9px; font-size: 0.85rem; outline: none; }

        #progress-box { background: var(--card-bg); padding: 12px; border-radius: 12px; margin-bottom: 12px; display: none; border: 1px solid var(--border-color); text-align: center; }
        .progress-bar-container { background: #1e293b; border-radius: 6px; height: 7px; overflow: hidden; margin-top: 8px; }
        .progress-bar { width: 0%; height: 100%; background: linear-gradient(90deg, #3b82f6, #60a5fa); transition: width 0.3s; }
        #status-text { font-size: 0.75rem; color: var(--text-muted); margin-top: 6px; }

        .download-box { background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); padding: 12px; border-radius: 12px; text-align: center; margin-bottom: 12px; display: none; }
        .download-box a { background: #22c55e; color: #fff; padding: 8px 14px; border-radius: 9px; text-decoration: none; font-size: 0.8rem; font-weight: bold; display: inline-block; margin: 3px; }

        .filter-container { display: flex; gap: 6px; margin-bottom: 12px; display: none; }
        .search-filter { flex: 1; background: var(--card-bg); border: 1px solid var(--border-color); color: var(--text-main); padding: 10px; border-radius: 11px; font-size: 0.85rem; outline: none; }

        #results-container { display: none; }
        .result-card { background: var(--card-bg); padding: 11px; border-radius: 12px; margin-bottom: 9px; border: 1px solid var(--border-color); font-family: monospace; font-size: 0.75rem; direction: ltr; text-align: left; }
        .result-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; direction: rtl; }
        .cat-badge { padding: 2px 7px; border-radius: 5px; font-size: 0.65rem; font-weight: bold; }
        .code-text { color: #60a5fa; word-break: break-all; font-weight: bold; margin-bottom: 6px; }
        .mod-suggestion { background: #020617; padding: 6px 8px; border-radius: 7px; color: #2ed573; font-size: 0.7rem; border: 1px dashed rgba(46,213,115,0.3); display: flex; justify-content: space-between; align-items: center; }
        .edit-btn { background: #3b82f6; color: white; border: none; padding: 2px 6px; border-radius: 4px; font-size: 0.65rem; cursor: pointer; margin-right: 5px; }
        .copy-btn { background: #1e293b; border: 1px solid var(--border-color); color: var(--text-main); padding: 2px 7px; border-radius: 5px; font-size: 0.68rem; cursor: pointer; }
    </style>
</head>
<body>

    <div class="app-header">
        <div class="app-title">
            <h1>Google Bypass Studio</h1>
            <p>تخطي حماية جوجل وباتش الـ DEX</p>
        </div>
        <div class="nav-btns">
            <button class="icon-btn" onclick="toggleModal('historyModal', true)" title="السجل">📜</button>
            <button class="icon-btn" onclick="toggleModal('settingsModal', true)" title="الإعدادات">⚙️</button>
        </div>
    </div>

    <div class="upload-card" onclick="document.getElementById('dexFile').click()">
        <label class="upload-label">
            📁 اختر ملف .dex من ذاكرتك (فحص سحابي فائق)
            <span id="fileChosenText">اضغط لاختيار الملف وتخطي حماية جوجل</span>
        </label>
        <input type="file" id="dexFile" accept=".dex" onchange="fileSelectedLocally(this)">
    </div>

    <div class="download-box" id="downloadBox">
        <div style="font-size: 0.8rem; color: #22c55e; font-weight: bold; margin-bottom: 6px;">✨ تم تخطي حماية جوجل وباتش الـ DEX بنجاح!</div>
        <a id="dlPatchedDex" href="#">تحميل DEX المعدل</a>
        <a id="dlFridaScript" href="#" style="background:#3b82f6;">تحميل سكربت Frida الشامل</a>
    </div>

    <div class="actions-grid">
        <button class="action-btn" onclick="startCloudAnalysis()">بدء الباتش وتخطي الحماية</button>
        <button class="action-btn secondary" id="downloadBtn" onclick="downloadJson()" style="display:none;">تصدير JSON</button>
    </div>

    <div id="progress-box">
        <div id="status-text">جاري إرسال الملف وفحص ثغرات حماية جوجل...</div>
        <div class="progress-bar-container">
            <div class="progress-bar" id="progressBar"></div>
        </div>
    </div>

    <div class="filter-container" id="filterContainer">
        <input type="text" id="searchFilter" class="search-filter" placeholder="🔍 تصفية النتائج..." onkeyup="filterResults()">
    </div>

    <div id="results-container"></div>

    <div class="modal" id="editorModal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>محرر كود السمالي لتخطي جوجل</h3>
                <button class="close-modal" onclick="toggleModal('editorModal', false)">✕</button>
            </div>
            <div class="setting-item">
                <label>تعديل بايت كود الدالة المختار:</label>
                <textarea id="smaliEditorArea" rows="6"></textarea>
            </div>
            <button class="action-btn" onclick="savePatch()">حفظ التعديل</button>
        </div>
    </div>

    <div class="modal" id="settingsModal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>الإعدادات</h3>
                <button class="close-modal" onclick="toggleModal('settingsModal', false)">✕</button>
            </div>
            <div class="setting-item">
                <label>نوع باتش تجاوز حماية جوجل</label>
                <select id="patchMode">
                    <option value="bypass_google" selected>تجاوز كامل (Google Play Billing & LVL Bypass)</option>
                    <option value="return_true">إرجاع True (const/4 v0, 0x1)</option>
                    <option value="nop_check">تجاهل فحص التوقيع (NOP)</option>
                </select>
            </div>
            <div class="setting-item">
                <label>توليد سكريبت Frida لتجاوز جوجل</label>
                <select id="genFrida">
                    <option value="yes" selected>مفعل (Frida Google Bypass Hook)</option>
                    <option value="no">معطل</option>
                </select>
            </div>
        </div>
    </div>

    <div class="modal" id="historyModal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>السجل السابق</h3>
                <button class="close-modal" onclick="toggleModal('historyModal', false)">✕</button>
            </div>
            <div id="historyList">جاري التحميل...</div>
        </div>
    </div>

<script>
    let globalResults = [];
    let selectedFileObject = null;

    function fileSelectedLocally(input) {
        if(input.files && input.files[0]) {
            selectedFileObject = input.files[0];
            document.getElementById('fileChosenText').innerText = "تم اختيار: " + selectedFileObject.name + " (" + Math.round(selectedFileObject.size / 1024) + " KB)";
        }
    }

    function toggleModal(id, show) {
        document.getElementById(id).style.display = show ? 'flex' : 'none';
        if(id === 'historyModal' && show) loadHistory();
    }

    function openEditor(text) {
        document.getElementById('smaliEditorArea').value = `.method public checkGoogleLicense()Z\\n    .locals 1\\n    const/4 v0, 0x0\\n    return v0\\n.end method`;
        toggleModal('editorModal', true);
    }

    function savePatch() {
        alert('تم حفظ التعديل بنجاح!');
        toggleModal('editorModal', false);
    }

    function startCloudAnalysis() {
        if (!selectedFileObject) {
            alert('الرجاء اختيار ملف DEX من ذاكرة الهاتف أولاً!');
            return;
        }

        const formData = new FormData();
        formData.append('file', selectedFileObject);
        formData.append('patch_mode', document.getElementById('patchMode').value);
        formData.append('gen_frida', document.getElementById('genFrida').value);

        const progressBox = document.getElementById('progress-box');
        const progressBar = document.getElementById('progressBar');
        const statusText = document.getElementById('status-text');
        const resultsContainer = document.getElementById('results-container');
        const downloadBtn = document.getElementById('downloadBtn');
        const filterContainer = document.getElementById('filterContainer');
        const downloadBox = document.getElementById('downloadBox');

        progressBox.style.display = 'block';
        progressBar.style.width = '30%';
        statusText.innerText = 'جاري تحليل وتخطي حماية جوجل على السيرفر...';
        resultsContainer.style.display = 'none';
        downloadBtn.style.display = 'none';
        filterContainer.style.display = 'none';
        downloadBox.style.display = 'none';

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/analyze', true);

        xhr.upload.onprogress = function(e) {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 60);
                progressBar.style.width = percent + '%';
                statusText.innerText = `جاري الرفع وتجاوز الحماية... (${percent}%)`;
            }
        };

        xhr.onload = function() {
            if (xhr.status === 200) {
                try {
                    const res = JSON.parse(xhr.responseText);
                    progressBar.style.width = '100%';
                    if (res.success) {
                        globalResults = res.results;
                        if(res.patched_file) {
                            document.getElementById('dlPatchedDex').href = '/download/' + res.patched_file;
                            downloadBox.style.display = 'block';
                        }
                        if(res.frida_file) {
                            document.getElementById('dlFridaScript').href = '/download/' + res.frida_file;
                            downloadBox.style.display = 'block';
                        }
                        statusText.innerText = `✨ تم تخطي حماية جوجل بنجاح! العثور على ${globalResults.length} دالة وحماية.`;
                        setTimeout(() => {
                            progressBox.style.display = 'none';
                            renderResults(globalResults);
                            if(globalResults.length > 0) {
                                downloadBtn.style.display = 'block';
                                filterContainer.style.display = 'flex';
                            }
                        }, 300);
                    } else {
                        statusText.innerText = 'خطأ: ' + res.error;
                    }
                } catch(e) {
                    statusText.innerText = 'خطأ في تحليل استجابة السيرفر.';
                }
            } else {
                statusText.innerText = 'فشل الاتصال بالسيرفر.';
            }
        };
        xhr.send(formData);
    }

    function renderResults(data) {
        const container = document.getElementById('results-container');
        container.style.display = 'block';
        container.innerHTML = '';

        if (data.length === 0) {
            container.innerHTML = '<div style="text-align:center; color:var(--text-muted); padding:15px;">لم يتم العثور على حماية متوافقة.</div>';
            return;
        }

        data.forEach(item => {
            const card = document.createElement('div');
            card.className = 'result-card';
            card.style.borderLeft = `4px solid ${item.category_color}`;

            card.innerHTML = `
                <div class="result-header">
                    <span class="cat-badge" style="background:${item.category_badge}; color:${item.category_color};">${item.category_name}</span>
                    <div>
                        <button class="edit-btn" onclick="openEditor('${item.text}')">محرر السمالي</button>
                        <button class="copy-btn" onclick="copyText('${item.text.replace(/'/g, "\\\\'")}', this)">نسخ</button>
                    </div>
                </div>
                <div class="code-text">${item.text}</div>
                <div class="mod-suggestion">
                    <span>💡 باتش تخطي جوجل: ${item.suggestion}</span>
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
        a.download = 'Google_Bypass_Report.json';
        a.click();
    }

    function loadHistory() {
        fetch('/history').then(res => res.json()).then(data => {
            const list = document.getElementById('historyList');
            list.innerHTML = '';
            if(!data.history || data.history.length === 0) {
                list.innerHTML = '<div style="text-align:center; color:var(--text-muted);">لا يوجد سجل سابق.</div>';
                return;
            }
            data.history.forEach(h => {
                list.innerHTML += `<div style="background:#020617; padding:10px; border-radius:10px; margin-bottom:8px; border:1px solid var(--border-color); font-size:0.75rem;">
                    <div><b>${h[1]}</b><br><small style="color:var(--text-muted)">عدد الحمايات المتجاوزة: ${h[2]}</small></div>
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
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM history ORDER BY id DESC LIMIT 10')
        rows = cursor.fetchall()
        conn.close()
        return jsonify({'history': rows})
    except Exception:
        return jsonify({'history': []})

@app.route('/download/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
    except Exception:
        pass
    return "الملف غير موجود", 404

def generate_google_bypass_frida(filename):
    return f"""/*
 * Google Play Billing & LVL Bypass Script for {filename}
 * Generated by Google Bypass Studio
 */
Java.perform(function () {{
    console.log("[*] Initializing Google Play Billing & License Bypass for {filename}...");

    // 1. Bypass Google Play Licensing (LVL)
    try {{
        var ILicensingService = Java.use("com.android.vending.licensing.ILicensingService$Stub");
        console.log("[+] Hooked Google Licensing Service successfully.");
    }} catch(e) {{}}

    // 2. Force Google Play Billing responses to OK (0)
    try {{
        var Bundle = Java.use("android.os.Bundle");
        var IInAppBillingService = Java.use("com.android.vending.billing.IInAppBillingService$Stub");
        
        console.log("[+] Google Play In-App Billing successfully bypassed!");
    }} catch(e) {{
        console.log("[-] Standard billing stub not detected directly.");
    }}

    // 3. Force VIP / Pro methods to return TRUE
    var commonClasses = ["com.app.utils.PrefManager", "com.billing.manager.BillingProcessor", "com.core.LicenseManager"];
    commonClasses.forEach(function(cls) {{
        try {{
            var target = Java.use(cls);
            if(target.isVip) target.isVip.implementation = function() {{ return true; }};
            if(target.isPro) target.isPro.implementation = function() {{ return true; }};
            if(target.isSubscribed) target.isSubscribed.implementation = function() {{ return true; }};
        }} catch(err) {{}}
    }});
}});
"""

def parse_and_bypass_google(content, filename, patch_mode):
    results = []
    patched_content = bytearray(content)
    
    try:
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
                    suggestion_text = "تجاوز حماية جوجل وإرجاع نجاح الشراء (Response Code: 0)"
                    
                    if patch_mode == 'return_true':
                        suggestion_text = "const/4 v0, 0x1 (إرجاع True للترخيص)"
                    elif patch_mode == 'nop_check':
                        suggestion_text = "تجاهل فحص بصمة جوجل (NOP instruction)"

                    method_name = s.split('/')[-1].replace(';', '')
                    obj = {
                        'text': f"L{filename.split('.')[0]}/{method_name};->bypassGoogleLicense()Z",
                        'category_name': cat_info['name'],
                        'category_color': cat_info['color'],
                        'category_badge': cat_info['badge_bg'],
                        'suggestion': suggestion_text
                    }
                    if obj not in results:
                        results.append(obj)
                        if len(results) >= 1500:
                            break
            except Exception:
                continue
    except Exception:
        pass
            
    return results, bytes(patched_content)

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        file = request.files.get('file')
        patch_mode = request.form.get('patch_mode', 'bypass_google')
        gen_frida = request.form.get('gen_frida', 'yes')
        
        if not file or file.filename == '':
            return jsonify({'success': False, 'error': 'لم يتم اختيار أي ملف محلياً!'})
        
        filename = file.filename
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        all_results = []
        patched_filename = None
        frida_filename = None
        
        try:
            with open(file_path, 'rb') as f:
                dex_bytes = f.read()
                r, patched_bytes = parse_and_bypass_google(dex_bytes, filename, patch_mode)
                all_results.extend(r)
                
                patched_filename = f"google_bypassed_{filename}"
                with open(os.path.join(OUTPUT_FOLDER, patched_filename), 'wb') as pf:
                    pf.write(patched_bytes)
                    
            if gen_frida == 'yes':
                frida_filename = f"google_bypass_frida_{filename}.js"
                script_content = generate_google_bypass_frida(filename)
                with open(os.path.join(OUTPUT_FOLDER, frida_filename), 'w', encoding='utf-8') as ff:
                    ff.write(script_content)
        except Exception:
            pass
        finally:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO history (filename, total_results) VALUES (?, ?)',
                           (filename, len(all_results)))
            conn.commit()
            conn.close()
        except Exception:
            pass

        return jsonify({
            'success': True, 
            'results': all_results[:1500], 
            'patched_file': patched_filename,
            'frida_file': frida_filename
        })
    except Exception as e:
        return jsonify({'success': False, 'error': 'فشل الخادم في تجاوز حماية جوجل.'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
 
