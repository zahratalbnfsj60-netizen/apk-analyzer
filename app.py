import os
import re
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# نمط دقيق لالتقاط السلاسل النصية المفيدة في ملفات الـ DEX
STRING_PATTERN = re.compile(b'[\x20-\x7E]{4,}')

# الكلمات المفتاحية المركزة حصرياً على فتح الميزات المدفوعة والاشتراكات
TARGET_KEYWORDS = [
    'isvip', 'ispro', 'ispremium', 'issubscribed', 'hasaccess', 
    'premium_subscription', 'vip_status', 'pro_status', 'checklicense',
    'is_vip', 'is_pro', 'is_premium', 'unlock_all', 'purchased',
    'subs', 'subscription', 'proversion', 'vipversion', 'unlocked'
]

# كلمات مستبعدة لتجنب المكتبات الخارجية والإعلانات
IGNORED_KEYWORDS = [
    'applovin', 'firebase', 'google', 'ads', 'facebook', 'adjust', 
    'ironsource', 'unity', 'appsflyer', 'analytics', 'crashlytics'
]

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>محلل دوال فتح المميزات الكاملة | VIP & Pro</title>
    <style>
        :root {
            --bg-color: #0d1117;
            --card-bg: #161b22;
            --border-color: #30363d;
            --gold: #f0b429;
            --gold-hover: #d99b14;
            --text-main: #c9d1d9;
            --text-muted: #8b949e;
        }
        body { font-family: system-ui, -apple-system, Tahoma, sans-serif; background-color: var(--bg-color); color: var(--text-main); padding: 20px; margin: 0; text-align: center; }
        .container { max-width: 800px; background: var(--card-bg); padding: 25px; border-radius: 16px; border: 1px solid var(--border-color); box-shadow: 0 8px 24px rgba(0,0,0,0.5); margin: auto; }
        h2 { color: var(--gold); font-size: 1.5rem; margin-bottom: 5px; font-weight: 800; }
        p { color: var(--text-muted); font-size: 0.9rem; margin-bottom: 20px; }
        
        .file-box { border: 2px dashed var(--gold); padding: 20px; border-radius: 12px; margin: 15px 0; background: rgba(240, 180, 41, 0.03); }
        input[type="file"] { color: var(--text-main); width: 100%; font-size: 0.9rem; cursor: pointer; }
        
        .btn-group { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 15px; }
        button { background: var(--gold); color: #000; border: none; padding: 12px 20px; border-radius: 8px; font-weight: bold; cursor: pointer; flex: 1; font-size: 0.95rem; min-width: 130px; transition: all 0.2s; }
        button:hover { background: var(--gold-hover); }
        button.btn-danger { background: #da3633; color: #fff; }
        button.btn-success { background: #2ea043; color: #fff; }
        
        #progress-container { width: 100%; background: #21262d; border-radius: 8px; margin-top: 20px; overflow: hidden; display: none; border: 1px solid var(--border-color); }
        #progress-bar { width: 0%; height: 24px; background: linear-gradient(90deg, #f0b429, #ffd369); text-align: center; color: #000; font-weight: bold; font-size: 0.85rem; line-height: 24px; }
        #status { margin-top: 10px; color: var(--gold); font-size: 0.9rem; font-weight: 600; }
        
        .search-box { width: 100%; padding: 12px; margin-top: 15px; background: var(--bg-color); border: 1px solid var(--border-color); color: var(--text-main); border-radius: 8px; box-sizing: border-box; display: none; font-size: 0.95rem; outline: none; }
        
        #methods-list { text-align: left; background: #010409; padding: 15px; border-radius: 10px; margin-top: 15px; max-height: 450px; overflow-y: auto; direction: ltr; display: none; border: 1px solid var(--border-color); }
        .method-card { background: var(--card-bg); padding: 12px; margin-bottom: 10px; border-radius: 8px; border-left: 5px solid var(--gold); font-family: monospace; font-size: 0.85rem; border: 1px solid var(--border-color); }
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
        .badge { padding: 3px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: bold; background: rgba(240,180,41,0.15); color: var(--gold); border: 1px solid rgba(240,180,41,0.3); }
        .item-text { color: #58a6ff; word-break: break-all; font-weight: bold; }
        .suggestion-box { background: #0d1117; padding: 8px 10px; margin-top: 8px; border-radius: 6px; color: #3fb950; font-size: 0.8rem; display: flex; justify-content: space-between; align-items: center; border: 1px dashed rgba(63, 185, 80, 0.4); }
        .copy-btn { background: #21262d; color: var(--text-main); border: 1px solid var(--border-color); padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; cursor: pointer; }
        .copy-btn:hover { background: var(--gold); color: #000; }
    </style>
</head>
<body>
<div class="container">
    <h2>محلل دوال فتح المميزات الكاملة</h2>
    <p>ارفع ملفات الـ DEX أو APK لاستخراج دوال الـ VIP والاشتراكات بدقة عالية:</p>
    
    <div class="file-box">
        <input type="file" id="dexFiles" multiple>
    </div>

    <div class="btn-group">
        <button onclick="uploadAndAnalyze()">بدء الفحص الذكي</button>
        <button class="btn-success" id="downloadBtn" onclick="downloadTxt()" style="display:none;">تحميل النتائج TXT</button>
        <button class="btn-danger" onclick="clearAll()">إعادة ضبط</button>
    </div>

    <div id="progress-container">
        <div id="progress-bar">0%</div>
    </div>
    <div id="status"></div>

    <input type="text" id="filterInput" class="search-box" placeholder="🔍 تصفية النتائج..." onkeyup="filterMethods()">
    
    <div id="methods-list"></div>
</div>

<script>
    let allResults = [];

    function uploadAndAnalyze() {
        const fileInput = document.getElementById('dexFiles');
        const listDiv = document.getElementById('methods-list');
        const statusDiv = document.getElementById('status');
        const progressContainer = document.getElementById('progress-container');
        const progressBar = document.getElementById('progress-bar');
        const downloadBtn = document.getElementById('downloadBtn');
        const filterInput = document.getElementById('filterInput');

        if (!fileInput.files || fileInput.files.length === 0) {
            alert('الرجاء اختيار ملف واحد على الأقل!');
            return;
        }

        const formData = new FormData();
        for (let i = 0; i < fileInput.files.length; i++) {
            formData.append('files', fileInput.files[i]);
        }

        progressContainer.style.display = 'block';
        progressBar.style.width = '0%';
        progressBar.innerText = '0%';
        statusDiv.innerText = 'جاري رفع الملفات...';
        listDiv.style.display = 'none';
        listDiv.innerHTML = '';
        downloadBtn.style.display = 'none';
        filterInput.style.display = 'none';

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/analyze', true);

        xhr.upload.onprogress = function (e) {
            if (e.lengthComputable) {
                const percentComplete = Math.round((e.loaded / e.total) * 45);
                progressBar.style.width = percentComplete + '%';
                progressBar.innerText = percentComplete + '%';
            }
        };

        let currentProgress = 45;
        const interval = setInterval(() => {
            if (currentProgress < 92) {
                currentProgress += 15;
                progressBar.style.width = currentProgress + '%';
                progressBar.innerText = currentProgress + '%';
                statusDiv.innerText = `⚡ جارٍ تحليل وفلترة ملفات DEX... (${currentProgress}%)`;
            }
        }, 80);

        xhr.onload = function () {
            clearInterval(interval);
            if (xhr.status === 200) {
                try {
                    const result = JSON.parse(xhr.responseText);
                    progressBar.style.width = '100%';
                    progressBar.innerText = '100%';
                    
                    if (result.success) {
                        allResults = result.methods;
                        statusDiv.innerText = `✨ تم الانتهاء بنجاح! العثور على ${allResults.length} دالة مطابقة للمميزات الكاملة.`;
                        if (allResults.length > 0) {
                            renderMethods(allResults);
                            downloadBtn.style.display = 'inline-block';
                            filterInput.style.display = 'block';
                        } else {
                            listDiv.style.display = 'block';
                            listDiv.innerHTML = '<div style="color:var(--text-muted); text-align:center; padding:20px;">لم يتم العثور على دوال مطابقة.</div>';
                        }
                    } else {
                        statusDiv.innerText = 'حدث خطأ أثناء المعالجة.';
                    }
                } catch (err) {
                    statusDiv.innerText = 'خطأ في قراءة استجابة الخادم.';
                }
            } else {
                statusDiv.innerText = 'فشل الاتصال بالخادم.';
            }
        };

        xhr.send(formData);
    }

    fn renderMethods(resultsArray) {
        // تم تصحيح بناء الوظيفة
    }

    function renderMethods(resultsArray) {
        const listDiv = document.getElementById('methods-list');
        listDiv.style.display = 'block';
        listDiv.innerHTML = '';

        resultsArray.forEach((item) => {
            const card = document.createElement('div');
            card.className = 'method-card';
            
            card.innerHTML = `
                <div class="card-header">
                    <span class="badge">💎 دالة فتح المميزات</span>
                    <button class="copy-btn" onclick="copyText('${item.text.replace(/'/g, "\\\\'")}', this)">نسخ النص</button>
                </div>
                <div class="item-text">${item.text}</div>
                <div class="suggestion-box">
                    <span>💡 التعديل المقترح: ${item.suggestion}</span>
                    <button class="copy-btn" onclick="copyText('${item.suggestion.replace(/'/g, "\\\\'")}', this)">نسخ الكود</button>
                </div>
            `;
            listDiv.appendChild(card);
        });
    }

    function copyText(text, btnElement) {
        navigator.clipboard.writeText(text).then(() => {
            const originalText = btnElement.innerText;
            btnElement.innerText = 'تم النسخ!';
            setTimeout(() => { btnElement.innerText = originalText; }, 1500);
        });
    }

    function filterMethods() {
        const query = document.getElementById('filterInput').value.toLowerCase();
        const filtered = allResults.filter(m => m.text.toLowerCase().includes(query));
        renderMethods(filtered);
    }

    function downloadTxt() {
        const text = allResults.map(r => `${r.text} --> Suggested Mod: ${r.suggestion}`).join('\\n');
        const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'Unlock_Features_Methods.txt';
        a.click();
    }

    function clearAll() {
        document.getElementById('dexFiles').value = '';
        document.getElementById('methods-list').style.display = 'none';
        document.getElementById('methods-list').innerHTML = '';
        document.getElementById('status').innerText = '';
        document.getElementById('progress-container').style.display = 'none';
        document.getElementById('downloadBtn').style.display = 'none';
        document.getElementById('filterInput').style.display = 'none';
        allResults = [];
    }
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

def process_dex_content(content, filename):
    matched = []
    text_chunks = STRING_PATTERN.findall(content)
    for chunk in text_chunks:
        try:
            s = chunk.decode('utf-8', errors='ignore').strip()
            lower_s = s.lower()
            
            # التحقق من أن النص يحتوي على الكلمات المستهدفة للمميزات حصرياً ولا يتبع مكتبات خارجية
            if any(kw in lower_s for kw in TARGET_KEYWORDS):
                if not any(ig in lower_s for ig in IGNORED_KEYWORDS):
                    if len(s) < 60:  # تقييد الطول لضمان جودة النصوص المستخرجة
                        result_obj = {
                            'file': filename,
                            'text': f"[{filename}] {s}",
                            'suggestion': 'const/4 v0, 0x1 (إرجاع True لتفعيل المميزات)'
                        }
                        if result_obj not in matched:
                            matched.append(result_obj)
                            if len(matched) >= 400:
                                break
        except Exception:
            continue
    return matched

def process_single_file(file):
    if not file or file.filename == '':
        return []
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    file_results = []
    
    try:
        if file.filename.endswith('.apk') or zipfile.is_zipfile(file_path):
            with zipfile.ZipFile(file_path, 'r') as z:
                dex_files = [name for name in z.namelist() if name.endswith('.dex')]
                with ThreadPoolExecutor() as executor:
                    futures = {executor.submit(scan_dex_from_zip, file_path, zinfo, file.filename): zinfo for zinfo in dex_files}
                    for future in as_completed(futures):
                        file_results.extend(future.result())
        else:
            with open(file_path, "rb") as f:
                content = f.read()
            file_results.extend(process_dex_content(content, file.filename))
    except Exception:
        pass
    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
    return file_results

def scan_dex_from_zip(apk_path, zinfo, filename):
    try:
        with zipfile.ZipFile(apk_path, 'r') as z:
            with z.open(zinfo) as dex_file:
                content = dex_file.read()
                return process_dex_content(content, f"{filename} -> {zinfo}")
    except Exception:
        return []

@app.route('/analyze', methods=['POST'])
def analyze():
    files = request.files.getlist('files') or request.files.getlist('file')
    if not files or all(f.filename == '' for f in files):
        return jsonify({'success': False, 'error': 'لم يتم اختيار أي ملفات للتحليل'})
    
    all_matched_results = []
    
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_single_file, file) for file in files]
        for future in as_completed(futures):
            try:
                all_matched_results.extend(future.result())
            except Exception:
                pass

    return jsonify({'success': True, 'methods': all_matched_results[:1500]})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
 
