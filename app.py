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
    <title>مستخرج دوال المميزات (VIP & Pro)</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #121212; color: #e0e0e0; padding: 15px; margin: 0; text-align: center; }
        .container { max-width: 700px; background: #1e1e1e; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.6); margin: auto; }
        h2 { color: #4da6ff; font-size: 1.3rem; margin-bottom: 10px; }
        p { color: #aaa; font-size: 0.85rem; }
        .file-box { border: 2px dashed #007bff; padding: 15px; border-radius: 8px; margin: 15px 0; background: #252525; }
        input[type="file"] { color: #fff; width: 100%; font-size: 0.9rem; }
        .btn-group { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px; }
        button { background: #007bff; color: white; border: none; padding: 10px 15px; border-radius: 6px; font-weight: bold; cursor: pointer; flex: 1; font-size: 0.9rem; min-width: 120px; }
        button:hover { background: #0056b3; }
        button.btn-danger { background: #dc3545; }
        button.btn-danger:hover { background: #a71d2a; }
        button.btn-success { background: #28a745; }
        button.btn-success:hover { background: #1e7e34; }
        #progress-container { width: 100%; background: #333; border-radius: 6px; margin-top: 15px; overflow: hidden; display: none; }
        #progress-bar { width: 0%; height: 20px; background: #00ff66; text-align: center; color: #000; font-weight: bold; font-size: 0.8rem; transition: width 0.3s ease; }
        #status { margin-top: 8px; color: #ffca28; font-size: 0.85rem; }
        .search-box { width: 100%; padding: 10px; margin-top: 15px; background: #2a2a2a; border: 1px solid #444; color: #fff; border-radius: 6px; box-sizing: border-box; display: none; font-size: 0.9rem; }
        #methods-list { text-align: left; background: #0b0b0b; padding: 10px; border-radius: 8px; margin-top: 15px; max-height: 380px; overflow-y: auto; direction: ltr; display: none; }
        .method-item { display: flex; justify-content: space-between; align-items: center; background: #181818; padding: 8px 12px; margin-bottom: 6px; border-radius: 6px; border-left: 4px solid #00ff66; font-family: monospace; font-size: 0.8rem; color: #00ff66; }
        .copy-btn { background: #333; color: #fff; border: none; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; cursor: pointer; }
        .copy-btn:hover { background: #007bff; }
    </style>
</head>
<body>
<div class="container">
    <h2>تحليل واستخراج دوال VIP & Pro الحقيقية</h2>
    <p>اختر ملفات الـ DEX (مثل classes.dex) لبدء التحليل الفوري واستخراج الدوال:</p>
    
    <div class="file-box">
        <input type="file" id="dexFiles" multiple>
    </div>

    <div class="btn-group">
        <button onclick="uploadAndAnalyze()">بدء الفحص الحقيقي</button>
        <button class="btn-success" id="downloadBtn" onclick="downloadTxt()" style="display:none;">تحميل TXT</button>
        <button class="btn-danger" onclick="clearAll()">تفريغ وحذف</button>
    </div>

    <div id="progress-container">
        <div id="progress-bar">0%</div>
    </div>
    <div id="status"></div>

    <input type="text" id="filterInput" class="search-box" placeholder="تصفية النتائج (مثال: vip, pro, sub)..." onkeyup="filterMethods()">
    
    <div id="methods-list"></div>
</div>

<script>
    let allMethods = [];

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
        statusDiv.innerText = 'جاري رفع الملفات وتحليلها...';
        listDiv.style.display = 'none';
        listDiv.innerHTML = '';
        downloadBtn.style.display = 'none';
        filterInput.style.display = 'none';

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/analyze', true);

        xhr.upload.onprogress = function (e) {
            if (e.lengthComputable) {
                const percentComplete = Math.round((e.loaded / e.total) * 50);
                progressBar.style.width = percentComplete + '%';
                progressBar.innerText = percentComplete + '%';
                statusDiv.innerText = 'جاري الرفع... (' + percentComplete + '%)';
            }
        };

        let currentProgress = 50;
        const interval = setInterval(() => {
            if (currentProgress < 90) {
                currentProgress += 5;
                progressBar.style.width = currentProgress + '%';
                progressBar.innerText = currentProgress + '%';
                statusDiv.innerText = 'جاري مطابقة وتصنيف دوال المميزات الحقيقية ... (' + currentProgress + '%)';
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
                        allMethods = result.methods;
                        statusDiv.innerText = 'تم الانتهاء بنجاح! العثور على ' + allMethods.length + ' دالة ومميزات.';
                        if (allMethods.length > 0) {
                            renderMethods(allMethods);
                            downloadBtn.style.display = 'inline-block';
                            filterInput.style.display = 'block';
                        } else {
                            listDiv.style.display = 'block';
                            listDiv.innerHTML = '<div style="color:#aaa; text-align:center; padding:15px;">لم يتم العثور على دوال مطابقة في الملفات المحددة.</div>';
                        }
                    } else {
                        statusDiv.innerText = 'حدث خطأ أثناء التحليل.';
                        listDiv.style.display = 'block';
                        listDiv.innerHTML = '<div style="color:#ff4444; padding:10px;">خطأ: ' + result.error + '</div>';
                    }
                } catch (err) {
                    statusDiv.innerText = 'خطأ في معالجة الاستجابة.';
                }
            } else {
                statusDiv.innerText = 'فشل الاتصال بالسيرفر.';
            }
        };

        xhr.send(formData);
    }

    function renderMethods(methodsArray) {
        const listDiv = document.getElementById('methods-list');
        listDiv.style.display = 'block';
        listDiv.innerHTML = '';

        methodsArray.forEach((item) => {
            const div = document.createElement('div');
            div.className = 'method-item';
            
            const span = document.createElement('span');
            span.innerText = item;
            
            const btn = document.createElement('button');
            btn.className = 'copy-btn';
            btn.innerText = 'نسخ';
            btn.onclick = function() {
                navigator.clipboard.writeText(item).then(() => {
                    btn.innerText = 'تم النسخ!';
                    btn.style.background = '#28a745';
                    setTimeout(() => {
                        btn.innerText = 'نسخ';
                        btn.style.background = '#333';
                    }, 1500);
                });
            };

            div.appendChild(span);
            div.appendChild(btn);
            listDiv.appendChild(div);
        });
    }

    function filterMethods() {
        const query = document.getElementById('filterInput').value.toLowerCase();
        const filtered = allMethods.filter(m => m.toLowerCase().includes(query));
        renderMethods(filtered);
    }

    function downloadTxt() {
        const text = allMethods.join('\\n');
        const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'VIP_Pro_Methods.txt';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }

    function clearAll() {
        document.getElementById('dexFiles').value = '';
        document.getElementById('methods-list').style.display = 'none';
        document.getElementById('methods-list').innerHTML = '';
        document.getElementById('status').innerText = '';
        document.getElementById('progress-container').style.display = 'none';
        document.getElementById('downloadBtn').style.display = 'none';
        document.getElementById('filterInput').style.display = 'none';
        document.getElementById('filterInput').value = '';
        allMethods = [];
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
    # التحقق من وجود الملفات بأكثر من طريقة لضمان توافق متصفحات الجوال
    files = []
    if 'files' in request.files:
        files = request.files.getlist('files')
    elif 'file' in request.files:
        files = request.files.getlist('file')
        
    if not files or all(f.filename == '' for f in files):
        return jsonify({'success': False, 'error': 'لم يتم اختيار أي ملفات'})
    
    unlock_keywords = [
        'vip', 'pro', 'premium', 'unlock', 'lock', 'sub', 'subscription', 
        'license', 'auth', 'purchase', 'pay', 'billing', 'inapp', 'gold', 'plus', 
        'isvip', 'ispro', 'ispremium', 'issubscribed', 'checklicense', 'hasaccess'
    ]
    
    matched_results = []
    
    try:
        for file in files:
            if not file or file.filename == '':
                continue
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)
            
            with open(file_path, "rb") as f:
                content = f.read()
            
            text_chunks = re.findall(b'[\\x20-\\x7E]{5,}', content)
            for chunk in text_chunks:
                try:
                    s = chunk.decode('utf-8', errors='ignore').strip()
                    lower_s = s.lower()
                    if any(kw in lower_s for kw in unlock_keywords):
                        if len(s) < 100:
                            formatted_res = f"[{file.filename}] {s}"
                            if formatted_res not in matched_results:
                                matched_results.append(formatted_res)
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
