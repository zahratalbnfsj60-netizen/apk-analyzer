import os
import re
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# تعبيرات منتظمة دقيقة لاستخراج النصوص البرمجية
STRING_PATTERN = re.compile(b'[\x20-\x7E]{4,}')

# تصنيف الكلمات المفتاحية مع الألوان المخصصة لكل نوع دالة
FEATURE_CATEGORIES = {
    'purchase': {
        'name': 'دوال الشراء والدفع (In-App Purchase)',
        'color': '#ff4757',  # أحمر فخم
        'badge_bg': 'rgba(255, 71, 87, 0.15)',
        'keywords': ['purchase', 'billing', 'playstore', 'checkout', 'payment', 'order_id', 'sku', 'consume']
    },
    'vip': {
        'name': 'دوال الـ VIP والاشتراكات',
        'color': '#f0b429',  # أذهبي / أصفر فاخر
        'badge_bg': 'rgba(240, 180, 41, 0.15)',
        'keywords': ['isvip', 'ispro', 'ispremium', 'issubscribed', 'vip_status', 'pro_status', 'subscription', 'pro_version']
    },
    'bypass': {
        'name': 'دوال التخطي والتراخيص (Bypass & License)',
        'color': '#2ed573',  # أخضر مضيء
        'badge_bg': 'rgba(46, 213, 115, 0.15)',
        'keywords': ['checklicense', 'hasaccess', 'unlock_all', 'license_key', 'is_verified', 'security_check', 'crack', 'bypass']
    }
}

# الكلمات المستبعدة لتنقية النتائج من الإعلانات والحزم الغير مفيدة
IGNORED_KEYWORDS = [
    'applovin', 'firebase', 'google', 'ads', 'facebook', 
    'adjust', 'ironsource', 'unityads', 'admob', 'analytics', 'androidx'
]

MOBILE_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>DEX Reverse Engine | محلل دوال العكس الذكي</title>
    <style>
        :root {
            --bg-deep: #090d16;
            --card-bg: #111827;
            --border-color: #1f293d;
            --accent: #3b82f6;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
        }
        * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
        body { font-family: system-ui, -apple-system, sans-serif; background-color: var(--bg-deep); color: var(--text-main); margin: 0; padding: 15px; }
        
        .app-header { display: flex; justify-content: space-between; align-items: center; background: var(--card-bg); padding: 15px; border-radius: 14px; border: 1px solid var(--border-color); margin-bottom: 15px; }
        .app-title h1 { font-size: 1.15rem; margin: 0; color: #60a5fa; font-weight: 800; }
        .app-title p { font-size: 0.75rem; margin: 3px 0 0; color: var(--text-muted); }
        .settings-btn { background: #1f293d; border: none; color: var(--text-main); width: 38px; height: 38px; border-radius: 10px; font-size: 1.1rem; cursor: pointer; display: flex; align-items: center; justify-content: center; }

        .upload-card { background: var(--card-bg); border: 2px dashed #374151; padding: 20px; border-radius: 14px; text-align: center; margin-bottom: 15px; transition: 0.3s; }
        .upload-card:active { border-color: var(--accent); }
        input[type="file"] { display: none; }
        .upload-label { display: block; cursor: pointer; color: var(--text-main); font-size: 0.9rem; font-weight: 600; }
        .upload-label span { display: block; font-size: 0.75rem; color: var(--text-muted); margin-top: 5px; }

        .actions-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px; }
        button.action-btn { background: var(--accent); color: white; border: none; padding: 12px; border-radius: 10px; font-weight: bold; font-size: 0.9rem; cursor: pointer; width: 100%; box-shadow: 0 4px 12px rgba(59,130,246,0.25); }
        button.action-btn.secondary { background: #374151; color: var(--text-main); box-shadow: none; }
        button.action-btn.danger { background: #ef4444; }

        /* Settings Modal */
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); backdrop-filter: blur(5px); z-index: 100; align-items: center; justify-content: center; padding: 20px; }
        .modal-content { background: var(--card-bg); width: 100%; max-width: 400px; padding: 20px; border-radius: 16px; border: 1px solid var(--border-color); }
        .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        .modal-header h3 { margin: 0; font-size: 1rem; color: var(--text-main); }
        .close-modal { background: none; border: none; color: var(--text-muted); font-size: 1.2rem; cursor: pointer; }
        
        .setting-item { margin-bottom: 15px; }
        .setting-item label { display: block; font-size: 0.85rem; margin-bottom: 5px; color: var(--text-muted); }
        .setting-item select, .setting-item input { width: 100%; background: #090d16; border: 1px solid var(--border-color); color: var(--text-main); padding: 10px; border-radius: 8px; font-size: 0.9rem; outline: none; }

        #progress-box { background: var(--card-bg); padding: 15px; border-radius: 14px; margin-bottom: 15px; display: none; border: 1px solid var(--border-color); text-align: center; }
        .progress-bar-container { background: #1f293d; border-radius: 6px; height: 10px; overflow: hidden; margin-top: 10px; }
        .progress-bar { width: 0%; height: 100%; background: linear-gradient(90deg, #3b82f6, #60a5fa); transition: width 0.3s; }
        #status-text { font-size: 0.8rem; color: var(--text-muted); margin-top: 8px; }

        .search-filter { width: 100%; background: var(--card-bg); border: 1px solid var(--border-color); color: var(--text-main); padding: 12px; border-radius: 10px; margin-bottom: 15px; font-size: 0.9rem; outline: none; display: none; }

        /* Results List */
        #results-container { display: none; }
        .result-card { background: var(--card-bg); padding: 12px; border-radius: 12px; margin-bottom: 10px; border: 1px solid var(--border-color); font-family: monospace; font-size: 0.8rem; direction: ltr; text-align: left; }
        .result-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; direction: rtl; }
        .cat-badge { padding: 2px 8px; border-radius: 6px; font-size: 0.7rem; font-weight: bold; }
        .code-text { color: #60a5fa; word-break: break-all; font-weight: bold; margin-bottom: 8px; }
        .mod-suggestion { background: #090d16; padding: 6px 8px; border-radius: 6px; color: #2ed573; font-size: 0.75rem; border: 1px dashed rgba(46,213,115,0.3); display: flex; justify-content: space-between; align-items: center; }
        .copy-btn { background: #1f293d; border: 1px solid var(--border-color); color: var(--text-main); padding: 3px 8px; border-radius: 5px; font-size: 0.7rem; cursor: pointer; }
    </style>
</head>
<body>

    <div class="app-header">
        <div class="app-title">
            <h1>DEX Reverse Pro</h1>
            <p>محلل دوال الشراء والتخطي والـ VIP الذكي</p>
        </div>
        <button class="settings-btn" onclick="toggleSettings(true)">⚙️</button>
    </div>

    <div class="upload-card" onclick="document.getElementById('fileInput').click()">
        <label class="upload-label">
            📁 اضغط لاختيار ملفات DEX أو APK
            <span>يدعم التخزين الداخلي واستخراج حزم الـ DEX تلقائياً</span>
        </label>
        <input type="file" id="fileInput" multiple accept=".dex,.apk,.zip">
    </div>

    <div class="actions-grid">
        <button class="action-btn" onclick="startAnalysis()">بدء التحليل الفوري</button>
        <button class="action-btn secondary" id="downloadBtn" onclick="downloadResults()" style="display:none;">تصدير TXT</button>
    </div>

    <div id="progress-box">
        <div id="status-text">جاري تحليل هيكل الملفات...</div>
        <div class="progress-bar-container">
            <div class="progress-bar" id="progressBar"></div>
        </div>
    </div>

    <input type="text" id="searchFilter" class="search-filter" placeholder="🔍 تصفية النتائج بالكلمات أو اسم الدالة..." onkeyup="filterResults()">

    <div id="results-container"></div>

    <!-- إعدادات التطبيق -->
    <div class="modal" id="settingsModal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>إعدادات الهندسة العكسية</h3>
                <button class="close-modal" onclick="toggleSettings(false)">✕</button>
            </div>
            <div class="setting-item">
                <label>الحد الأقصى للنتائج المستخرجة</label>
                <select id="maxResults">
                    <option value="500">500 دالة (سريع جداً)</option>
                    <option value="1500" selected>1500 دالة (موصى به)</option>
                    <option value="3000">3000 دالة (فحص عميق)</option>
                </select>
            </div>
            <div class="setting-item">
                <label>نوع التعديل المقترح التلقائي</label>
                <select id="modType">
                    <option value="const/4 v0, 0x1 (إرجاع True)">const/4 v0, 0x1 (إرجاع قيمة صحيحة)</option>
                    <option value="return-void (تخطي الدالة)">return-void (إلغاء التحقق)</option>
                </select>
            </div>
            <button class="action-btn danger" onclick="resetApp()" style="margin-top:10px;">إعادة ضبط التطبيق</button>
        </div>
    </div>

<script>
    let globalResults = [];

    function toggleSettings(show) {
        document.getElementById('settingsModal').style.display = show ? 'flex' : 'none';
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
        formData.append('max_results', document.getElementById('maxResults').value);
        formData.append('mod_type', document.getElementById('modType').value);

        const progressBox = document.getElementById('progress-box');
        const progressBar = document.getElementById('progressBar');
        const statusText = document.getElementById('status-text');
        const resultsContainer = document.getElementById('results-container');
        const downloadBtn = document.getElementById('downloadBtn');
        const searchFilter = document.getElementById('searchFilter');

        progressBox.style.display = 'block';
        progressBar.style.width = '20%';
        statusText.innerText = 'جاري رفع وفك ضغط الحزم...';
        resultsContainer.style.display = 'none';
        downloadBtn.style.display = 'none';
        searchFilter.style.display = 'none';

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/analyze', true);

        xhr.upload.onprogress = function(e) {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 50);
                progressBar.style.width = percent + '%';
            }
        };

        let interval = setInterval(() => {
            let currentW = parseInt(progressBar.style.width);
            if (currentW < 85) {
                progressBar.style.width = (currentW + 10) + '%';
                statusText.innerText = '⚡ جارٍ فحص دوال الشراء والتخطي والـ VIP...';
            }
        }, 300);

        xhr.onload = function() {
            clearInterval(interval);
            if (xhr.status === 200) {
                const res = JSON.parse(xhr.responseText);
                progressBar.style.width = '100%';
                if (res.success) {
                    globalResults = res.results;
                    statusText.innerText = `✨ تم الانتهاء! العثور على ${globalResults.length} دالة مستهدفة.`;
                    setTimeout(() => {
                        progressBox.style.display = 'none';
                        renderResults(globalResults);
                        if(globalResults.length > 0) {
                            downloadBtn.style.display = 'block';
                            searchFilter.style.display = 'block';
                        }
                    }, 500);
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
            container.innerHTML = '<div style="text-align:center; color:var(--text-muted); padding:20px;">لم يتم العثور على دوال مطابقة للمعايير.</div>';
            return;
        }

        data.forEach(item => {
            const card = document.createElement('div');
            card.className = 'result-card';
            card.style.borderLeft = `5px solid ${item.category_color}`;

            card.innerHTML = `
                <div class="result-header">
                    <span class="cat-badge" style="background:${item.category_badge}; color:${item.category_color};">${item.category_name}</span>
                    <button class="copy-btn" onclick="copyText('${item.text.replace(/'/g, "\\\\'")}', this)">نسخ الدالة</button>
                </div>
                <div class="code-text">${item.text}</div>
                <div class="mod-suggestion">
                    <span>💡 تعديل المقترح: ${item.suggestion}</span>
                    <button class="copy-btn" onclick="copyText('${item.suggestion.replace(/'/g, "\\\\'")}', this)">نسخ التعديل</button>
                </div>
            `;
            container.appendChild(card);
        });
    }

    function filterResults() {
        const query = document.getElementById('searchFilter').value.toLowerCase();
        const filtered = globalResults.filter(item => item.text.toLowerCase().includes(query));
        renderResults(filtered);
    }

    function copyText(text, btn) {
        navigator.clipboard.writeText(text).then(() => {
            let oldText = btn.innerText;
            btn.innerText = 'تم!';
            setTimeout(() => btn.innerText = oldText, 1200);
        });
    }

    function downloadResults() {
        const text = globalResults.map(r => `[${r.category_name}] ${r.text} --> Mod: ${r.suggestion}`).join('\\n');
        const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'Reversed_Functions_Report.txt';
        a.click();
    }

    function resetApp() {
        location.reload();
    }
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(MOBILE_HTML_TEMPLATE)

def analyze_dex_bytes(content, filename, max_limit, default_suggestion):
    results = []
    chunks = STRING_PATTERN.findall(content)
    
    for chunk in chunks:
        try:
            s = chunk.decode('utf-8', errors='ignore').strip()
            lower_s = s.lower()
            
            if len(s) > 80 or any(ig in lower_s for ig in IGNORED_KEYWORDS):
                continue
                
            matched_cat = None
            for cat_key, cat_data in FEATURE_CATEGORIES.items():
                if any(kw in lower_s for kw in cat_data['keywords']):
                    matched_cat = cat_key
                    break
            
            if matched_cat:
                cat_info = FEATURE_CATEGORIES[matched_cat]
                obj = {
                    'text': f"[{filename}] {s}",
                    'category_name': cat_info['name'],
                    'category_color': cat_info['color'],
                    'category_badge': cat_info['badge_bg'],
                    'suggestion': default_suggestion
                }
                if obj not in results:
                    results.append(obj)
                    if len(results) >= max_limit:
                        break
        except Exception:
            continue
    return results

@app.route('/analyze', methods=['POST'])
def analyze():
    files = request.files.getlist('files')
    max_limit = int(request.form.get('max_results', 1500))
    default_suggestion = request.form.get('mod_type', 'const/4 v0, 0x1 (إرجاع True)')
    
    if not files or all(f.filename == '' for f in files):
        return jsonify({'success': False, 'error': 'لم يتم اختيار أي ملفات!'})
    
    all_results = []
    
    with ThreadPoolExecutor() as executor:
        futures = []
        for file in files:
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)
            
            def process_file(f_path, f_name):
                res = []
                try:
                    if f_name.endswith(('.apk', '.zip')) or zipfile.is_zipfile(f_path):
                        with zipfile.ZipFile(f_path, 'r') as z:
                            dex_list = [n for n in z.namelist() if n.endswith('.dex')]
                            for dex in dex_list:
                                with z.open(dex) as dx:
                                    res.extend(analyze_dex_bytes(dx.read(), f"{f_name} -> {dex}", max_limit, default_suggestion))
                    elif f_name.endswith('.dex'):
                        with open(f_path, 'rb') as f:
                            res.extend(analyze_dex_bytes(f.read(), f_name, max_limit, default_suggestion))
                except Exception:
                    pass
                finally:
                    if os.path.exists(f_path):
                        os.remove(f_path)
                return res

            futures.append(executor.submit(process_file, file_path, file.filename))
            
        for future in as_completed(futures):
            all_results.extend(future.result())

    return jsonify({'success': True, 'results': all_results[:max_limit]})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
 
