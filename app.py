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
    <title>محلل دوال المميزات الذكي (VIP & Pro Analyzer)</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #121212; color: #e0e0e0; padding: 15px; margin: 0; text-align: center; }
        .container { max-width: 750px; background: #1e1e1e; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.6); margin: auto; }
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
        #methods-list { text-align: left; background: #0b0b0b; padding: 10px; border-radius: 8px; margin-top: 15px; max-height: 400px; overflow-y: auto; direction: ltr; display: none; }
        .method-card { background: #181818; padding: 10px; margin-bottom: 8px; border-radius: 6px; border-left: 5px solid #00ff66; font-family: monospace; font-size: 0.8rem; }
        .method-card.type-bool { border-left-color: #00bfff; }
        .method-card.type-limit { border-left-color: #ff9900; }
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; }
        .badge { padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; font-weight: bold; }
        .badge-bool { background: #0056b3; color: #fff; }
        .badge-limit { background: #b36b00; color: #fff; }
        .badge-feature { background: #1e7e34; color: #fff; }
        .item-text { color: #00ff66; word-break: break-all; }
        .suggestion-box { background: #111; padding: 5px 8px; margin-top: 5px; border-radius: 4px; color: #ffca28; font-size: 0.75rem; display: flex; justify-content: space-between; align-items: center; }
        .copy-btn { background: #333; color: #fff; border: none; padding: 3px 8px; border-radius: 4px; font-size: 0.7rem; cursor: pointer; }
        .copy-btn:hover { background: #007bff; }
    </style>
</head>
<body>
<div class="container">
    <h2>محلل دوال ومميزات VIP الذكي</h2>
    <p>اختر ملفات الـ DEX لاستخراج الدوال وتصنيفها مع قيم التعديل المقترحة:</p>
    
    <div class="file-box">
        <input type="file" id="dexFiles" multiple>
    </div>

    <div class="btn-group">
        <button onclick="uploadAndAnalyze()">بدء الفحص والتحليل</button>
        <button class="btn-success" id="downloadBtn" onclick="downloadTxt()" style="display:none;">تحميل النتائج TXT</button>
        <button class="btn-danger" onclick="clearAll()">تفريغ وحذف</button>
    </div>

    <div id="progress-container">
        <div id="progress-bar">0%</div>
    </div>
    <div id="status"></div>

    <input type="text" id="filterInput" class="search-box" placeholder="تصفية النتائج (مثال: isVip, date, pro)..." onkeyup="filterMethods()">
    
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
        statusDiv.innerText = 'جاري رفع الملفات والتحليل الذكي...';
        listDiv.style.display = 'none';
        listDiv.innerHTML = '';
        downloadBtn.style.display = 'none';
        filterInput.style.display =
     const query = document.getElementById('filterInput').value.toLowerCase();
        const filtered = allResults.filter(m => m.text.toLowerCase().includes(query) || m.type.toLowerCase().includes(query));
        renderMethods(filtered);
    }

    function downloadTxt() {
        const text = allResults.map(r => `[${r.type}] ${r.text} --> Suggested Mod: ${r.suggestion}`).join('\\n');
        const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'VIP_Smart_Analysis.txt';
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
    
    unlock_keywords = [
        'vip', 'pro', 'premium', 'unlock', 'lock', 'sub', 'subscription', 
        'license', 'auth', 'purchase', 'pay', 'billing', 'inapp', 'gold', 'plus', 
        'isvip', 'ispro', 'ispremium', 'issubscribed', 'checklicense', 'hasaccess', 'date', 'limit'
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
                            if any(k in lower_s for k in ['is', 'has', 'check', 'can', 'allow', 'valid']):
                                category = 'دالة تحقق (Boolean)'
                                suggestion = 'تعديل قيمة الإرجاع في Smali إلى: const/4 v0, 0x1 (True)'
                            elif 'date' in lower_s or 'time' in lower_s or 'limit' in lower_s:
                                category = 'قيود وتواريخ (Limit)'
                                suggestion = 'تجاوز الشرط أو ضبط القيمة إلى 0 أو تاريخ مستقبلي بعيد'
                            else:
                                category = 'ميزة / اشتراك (Feature)'
                                suggestion = 'تفعيل الشرط أو استبدال القيمة بـ True دائماً'
                            
                            result_obj = {
                                'file': file.filename,
                                'text': f"[{file.filename}] {s}",
                                'type': category,
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
meout(() => {
                btnElement.innerText = originalText;
                btnElement.style.background = '';
            }, 1500);
        });
    }

    function filterMethods() {
        const query = document.getElementById('filterInput').value.toLowerCase();
        const filtered = allResults.filter(m => m.text.toLowerCase().includes(query) || m.type.toLowerCase().includes(query));
        renderMethods(filtered);
    }

    function downloadTxt() {
        const text = allResults.map(r => `[${r.type}] ${r.text} --> Suggested Mod: ${r.suggestion}`).join('\\n');
        const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'VIP_Smart_Analysis.txt';
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
    
    unlock_keywords = [
        'vip', 'pro', 'premium', 'unlock', 'lock', 'sub', 'subscription', 
        'license', 'auth', 'purchase', 'pay', 'billing', 'inapp', 'gold', 'plus', 
        'isvip', 'ispro', 'ispremium', 'issubscribed', 'checklicense', 'hasaccess', 'date', 'limit'
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
                            # تصنيف ذكي وإعطاء قيمة التعديل المقترحة
                            if any(k in lower_s for k in ['is', 'has', 'check', 'can', 'allow', 'valid']):
                                category = 'دالة تحقق (Boolean)'
                                suggestion = 'تعديل قيمة الإرجاع في Smali إلى: const/4 v0, 0x1 (True)'
                            elif 'date' in lower_s or 'time' in lower_s or 'limit' in lower_s:
                                category = 'قيود وتواريخ (Limit)'
                                suggestion = 'تجاوز الشرط أو ضبط القيمة إلى 0 أو تاريخ مستقبلي بعيد'
                            else:
                                category = 'ميزة / اشتراك (Feature)'
                                suggestion = 'تفعيل الشرط أو استبدال القيمة بـ True دائماً'
                            
                            result_obj = {
                                'file': file.filename,
                                'text': f"[{file.filename}] {s}",
                                'type': category,
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
فق متصفحات الجوال
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
