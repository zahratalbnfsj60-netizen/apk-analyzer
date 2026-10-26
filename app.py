import os
import re
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>محلل دوال VIP & Pro الذهبي الحقيقي</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #121212; color: #e0e0e0; padding: 15px; margin: 0; text-align: center; }
        .container { max-width: 750px; background: #1e1e1e; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.6); margin: auto; }
        h2 { color: #ffb700; font-size: 1.3rem; margin-bottom: 10px; text-shadow: 0 2px 4px rgba(0,0,0,0.5); }
        p { color: #aaa; font-size: 0.85rem; }
        .file-box { border: 2px dashed #ffb700; padding: 15px; border-radius: 8px; margin: 15px 0; background: #252525; }
        input[type="file"] { color: #fff; width: 100%; font-size: 0.9rem; }
        .btn-group { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px; }
        button { background: #ffb700; color: #000; border: none; padding: 10px 15px; border-radius: 6px; font-weight: bold; cursor: pointer; flex: 1; font-size: 0.9rem; min-width: 120px; }
        button:hover { background: #e0a100; }
        button.btn-danger { background: #dc3545; color: #fff; }
        button.btn-danger:hover { background: #a71d2a; }
        button.btn-success { background: #28a745; color: #fff; }
        button.btn-success:hover { background: #1e7e34; }
        
        #progress-container { width: 100%; background: #333; border-radius: 6px; margin-top: 15px; overflow: hidden; display: none; }
        #progress-bar { width: 0%; height: 22px; background: #ffb700; text-align: center; color: #000; font-weight: bold; font-size: 0.8rem; transition: width 0.3s ease; line-height: 22px; }
        #status { margin-top: 8px; color: #ffca28; font-size: 0.85rem; font-weight: bold; }
        
        .search-box { width: 100%; padding: 10px; margin-top: 15px; background: #2a2a2a; border: 1px solid #ffb700; color: #fff; border-radius: 6px; box-sizing: border-box; display: none; font-size: 0.9rem; }
        
        #methods-list { text-align: left; background: #0b0b0b; padding: 10px; border-radius: 8px; margin-top: 15px; max-height: 400px; overflow-y: auto; direction: ltr; display: none; }
        .method-card { background: #181818; padding: 10px; margin-bottom: 8px; border-radius: 6px; border-left: 5px solid #ffb700; font-family: monospace; font-size: 0.8rem; }
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; }
        .badge { padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; font-weight: bold; background: #ffb700; color: #000; }
        .item-text { color: #ffb700; word-break: break-all; font-weight: bold; }
        .suggestion-box { background: #111; padding: 5px 8px; margin-top: 5px; border-radius: 4px; color: #00ff66; font-size: 0.75rem; display: flex; justify-content: space-between; align-items: center; border: 1px dashed #ffb700; }
        .copy-btn { background: #333; color: #fff; border: none; padding: 3px 8px; border-radius: 4px; font-size: 0.7rem; cursor: pointer; }
        .copy-btn:hover { background: #ffb700; color: #000; }
    </style>
</head>
<body>
<div class="container">
    <h2>محلل دوال VIP & Pro الذهبي الحقيقي</h2>
    <p>اختر ملفات الـ DEX أو APK لاستخراج دوال فتح المميزات الحقيقية بدقة:</p>
    
    <div class="file-box">
        <input type="file" id="dexFiles" multiple>
    </div>

    <div class="btn-group">
        <button onclick="uploadAndAnalyze()">بدء الفحص الحقيقي</button>
        <button class="btn-success" id="downloadBtn" onclick="downloadTxt()" style="display:none;">تحميل TXT</button>
        <button class="btn-danger" onclick="clearAll()">حذف وتفريغ</button>
    </div>

    <div id="progress-container">
        <div id="progress-bar">0%</div>
    </div>
    <div id="status"></div>

    <input type="text" id="filterInput" class="search-box" placeholder="تصفية النتائج الذهبية..." onkeyup="filterMethods()">
    
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
        statusDiv.innerText = 'جاري رفع الملفات إلى السيرفر الخارجي...';
        listDiv.style.display = 'none';
        listDiv.innerHTML = '';
        downloadBtn.style.display = 'none';
        filterInput.style.display = 'none';

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/analyze', true);

        xhr.upload.onprogress = function (e) {
            if (e.lengthComputable) {
                const percentComplete = Math.round((e.loaded / e.total) * 60);
                progressBar.style.width = percentComplete + '%';
                progressBar.innerText = percentComplete + '%';
                statusDiv.innerText = `جاري الرفع الفعلي... (${percentComplete}%)`;
            }
        };

        let currentProgress = 60;
        const interval = setInterval(() => {
            if (currentProgress < 95) {
                currentProgress += 5;
                progressBar.style.width = currentProgress + '%';
                progressBar.innerText = currentProgress + '%';
                statusDiv.innerText = `جاري استصفاء دوال VIP & Pro الحقيقية ... (${currentProgress}%)`;
            }
        }, 300);

        xhr.onload = function () {
            clearInterval(interval);
            if (xhr.status === 200) {
                try {
                    const result = JSON.parse(xhr.responseText);
                    progressBar.style.width = '100%';
                    progressBar.innerText = '100%';
                    
                    if (result.success) {
                        allResults = result.methods;
                        statusDiv.innerText = `تم الانتهاء! العثور على ${allResults.length} دالة مميزات حقيقية.`;
                        if (allResults.length > 0) {
                            renderMethods(allResults);
                            downloadBtn.style.display = 'inline-block';
                            filterInput.style.display = 'block';
                        } else {
                            listDiv.style.display = 'block';
                            listDiv.innerHTML = '<div style="color:#aaa; text-align:center; padding:15px;">لم يتم العثور على دوال مطابقة.</div>';
                        }
                    } else {
                        statusDiv.innerText = 'حدث خطأ أثناء التحليل.';
                        listDiv.style.display = 'block';
                        listDiv.innerHTML = `<div style="color:#ff4444; padding:10px;">خطأ: ${result.error}</div>`;
                    }
                } catch (err) {
                    statusDiv.innerText = 'خطأ في معالجة الاستجابة.';
                }
            } else {
                statusDiv.innerText = 'فشل الاتصال بالسيرفر الخارجي.';
            }
        };

        xhr.send(formData);
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
                    <span class="badge">💎 دالة مميزات حقيقية</span>
                    <button class="copy-btn" onclick="copyText('${item.text.replace(/'/g, "\\\\'")}', this)">نسخ النص</button>
                </div>
                <div class="item-text">${item.text}</div>
                <div class="suggestion-box">
                    <span>💡 تعديل Smali المقترح: ${item.suggestion}</span>
                    <button class="copy-btn" style="background:#222; color:#ffb700;" onclick="copyText('${item.suggestion.replace(/'/g, "\\\\'")}', this)">نسخ القيمة</button>
                </div>
            `;
            listDiv.appendChild(card);
        });
    }

    function copyText(text, btnElement) {
        navigator.clipboard.writeText(text).then(() => {
            const originalText = btnElement.innerText;
            btnElement.innerText = 'تم!';
            btnElement.style.background = '#ffb700';
            btnElement.style.color = '#000';
            setTimeout(() => {
                btnElement.innerText = originalText;
                btnElement.style.background = '';
                btnElement.style.color = '';
            }, 1500);
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
        a.download = 'Real_Gold_VIP_Methods.txt';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }

    function clearAll() {
        document.getElementById('dexFiles').value, document.getElementById('dexFiles').value = '';
        document.getElementById('methods-list').style.display = 'none';
        document.getElementById('methods-list').innerHTML = '';
        document.getElementById('status').innerText = '';
        document.getElementById('progress-container').style.display = 'none';
        document.getElementById('downloadBtn').style.display = 'none';
        document.getElementById('filterInput').style.display = 'none';
        document.getElementById('filterInput').value = '';
        allResults = [];
    }
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/analyze', methods=['POST'])
def analyze():
    files = []
    if 'files' in request.files:
        files = request.files.getlist('files')
    elif 'file' in request.files:
        files = request.files.getlist('file')
        
    if not files or all(f.filename == '' for f in files):
        return jsonify({'success': False, 'error': 'لم يتم اختيار أي ملفات'})
    
    # قائمة الكلمات المفتاحية الدقيقة لفتح المميزات وتجنب الإعلانات العشوائية
    target_keywords = [
        'isvip', 'ispro', 'ispremium', 'issubscribed', 'hasaccess', 
        'premium_subscription', 'vip_status', 'pro_status', 'checklicense',
        'is_vip', 'is_pro', 'is_premium', 'unlock_all', 'purchased'
    ]
    
    # الكلمات المستبعدة تماماً (لتجنب شبكات الإعلانات مثل AppLovin أو Firebase)
    ignored_keywords = ['applovin', 'firebase', 'google', 'ads', 'facebook', 'adjust', 'ironsource']
    
    matched_results = []
    
    try:
        for file in files:
            if not file or file.filename == '':
                continue
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)
            
            with open(file_path, "rb") as f:
                content = f.read()
            
            text_chunks = re.findall(b'[\\x20-\\x7E]{4,}', content)
            for chunk in text_chunks:
                try:
                    s = chunk.decode('utf-8', errors='ignore').strip()
                    lower_s = s.lower()
                    
                    # التحقق من أن النص يحتوي على كلمات الـ VIP ولا ينتمي لشركات الإعلانات المستبعدة
                    if any(kw in lower_s for kw in target_keywords):
                        if not any(ig in lower_s for ig in ignored_keywords):
                            if len(s) < 70:
                                suggestion = 'const/4 v0, 0x1 (إرجاع True لتفعيل الميزة)'
                                
                                result_obj = {
                                    'file': file.filename,
                                    'text': f"[{file.filename}] {s}",
                                    'suggestion': suggestion
                                }
                                
                                if result_obj not in matched_results:
                                    matched_results.append(result_obj)
                                    if len(matched_results) >= 2000:
                                        break
                except Exception:
                    continue
                    
            if os.path.exists(file_path):
                os.remove(file_path)
                
        return jsonify({'success': True, 'methods': matched_results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
 
