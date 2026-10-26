import os
from flask import Flask, request, jsonify, render_template_string
from androguard.misc import AnalyzeAPK

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

HTML_PAGE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مستخرج دوال المميزات المتقدم (DEX Analyzer)</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #121212; color: #e0e0e0; padding: 15px; margin: 0; text-align: center; }
        .container { max-width: 700px; background: #1e1e1e; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.6); margin: auto; }
        h2 { color: #4da6ff; font-size: 1.3rem; margin-bottom: 10px; }
        p { color: #aaa; font-size: 0.85rem; }
        .file-box { border: 2px dashed #444; padding: 15px; border-radius: 8px; margin: 15px 0; background: #252525; }
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
        #output { text-align: left; background: #000; color: #00ff66; padding: 12px; border-radius: 6px; margin-top: 10px; max-height: 300px; overflow-y: auto; direction: ltr; font-family: monospace; white-space: pre-wrap; font-size: 0.8rem; }
    </style>
</head>
<body>
<div class="container">
    <h2>فحص ملفات DEX متعددة واستخراج دوال VIP & Pro</h2>
    <p>اختر ملفات الـ DEX (يمكنك اختيار عدة ملفات معا مثل classes.dex و classes2.dex):</p>
    
    <div class="file-box">
        <input type="file" id="dexFiles" multiple>
    </div>

    <div class="btn-group">
        <button onclick="uploadAndAnalyze()">بدء الفحص والتحليل</button>
        <button class="btn-success" id="downloadBtn" onclick="downloadTxt()" style="display:none;">تصدير TXT</button>
        <button class="btn-danger" onclick="clearAll()">حذف وتفريغ</button>
    </div>

    <div id="progress-container">
        <div id="progress-bar">0%</div>
    </div>
    <div id="status"></div>

    <input type="text" id="filterInput" class="search-box" placeholder="ابحث داخل الدوال المستخرجة..." onkeyup="filterMethods()">
    
    <div id="output">نتائج استخراج دوال فتح المميزات ستظهر هنا...</div>
</div>

<script>
    let allMethods = [];

    function uploadAndAnalyze() {
        const fileInput = document.getElementById('dexFiles');
        const outputDiv = document.getElementById('output');
        const statusDiv = document.getElementById('status');
        const progressContainer = document.getElementById('progress-container');
        const progressBar = document.getElementById('progress-bar');
        const downloadBtn = document.getElementById('downloadBtn');
        const filterInput = document.getElementById('filterInput');

        if (fileInput.files.length === 0) {
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
        statusDiv.innerText = 'جاري رفع الملفات إلى السيرفر...';
        outputDiv.innerText = '';
        downloadBtn.style.display = 'none';
        filterInput.style.display = 'none';

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/analyze', true);

        xhr.upload.onprogress = function (e) {
            if (e.lengthComputable) {
                const percentComplete = Math.round((e.loaded / e.total) * 50);
                progressBar.style.width = percentComplete + '%';
                progressBar.innerText = percentComplete + '%';
                statusDiv.innerText = `جاري الرفع... (${percentComplete}%)`;
            }
        };

        let currentProgress = 50;
        const interval = setInterval(() => {
            if (currentProgress < 90) {
                currentProgress += 5;
                progressBar.style.width = currentProgress + '%';
                progressBar.innerText = currentProgress + '%';
                statusDiv.innerText = `جاري تحليل هيكل الملفات واستخراج دوال VIP / Pro ... (${currentProgress}%)`;
            }
        }, 500);

        xhr.onload = function () {
            clearInterval(interval);
            if (xhr.status === 200) {
                try {
                    const result = JSON.parse(xhr.responseText);
                    progressBar.style.width = '100%';
                    progressBar.innerText = '100%';
                    
                    if (result.success) {
                        allMethods = result.methods;
                        statusDiv.innerText = `تم الانتهاء بنجاح! العثور على ${allMethods.length} دالة مطابقة.`;
                        if (allMethods.length > 0) {
                            outputDiv.innerText = allMethods.join('\\n');
                            downloadBtn.style.display = 'inline-block';
                            filterInput.style.display = 'block';
                        } else {
                            outputDiv.innerText = 'لم يتم العثور على دوال مطابقة في الملفات المحددة.';
                        }
                    } else {
                        statusDiv.innerText = 'حدث خطأ أثناء التحليل.';
                        outputDiv.innerText = 'خطأ: ' + result.error;
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

    function filterMethods() {
        const query = document.getElementById('filterInput').value.toLowerCase();
        const outputDiv = document.getElementById('output');
        const filtered = allMethods.filter(m => m.toLowerCase().includes(query));
        outputDiv.innerText = filtered.length > 0 ? filtered.join('\\n') : 'لا توجد نتائج مطابقة للبحث.';
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
        document.getElementById('output').innerText = 'نتائج استخراج دوال فتح المميزات ستظهر هنا...';
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
'''

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/analyze', methods=['POST'])
def analyze():
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({'success': False, 'error': 'لم يتم اختيار أي ملفات'})
    
    unlock_keywords = [
        'vip', 'pro', 'premium', 'unlock', 'lock', 'sub', 'subscription', 
        'license', 'auth', 'purchase', 'pay', 'billing', 'inapp', 'gold', 'plus'
    ]
    
    matched_methods = []
    
    try:
        for file in files:
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)
            
            a, d, dx = AnalyzeAPK(file_path)
            
            for method in dx.get_methods():
                class_name = method.get_class_name()
                method_name = method.get_name()
                full_sig = f"[{file.filename}] Class: {class_name} --> Method: {method_name}"
                
                lower_sig = full_sig.lower()
                if any(kw in lower_sig for kw in unlock_keywords):
                    matched_methods.append(full_sig)
                    if len(matched_methods) >= 1500:
                        break
                        
            if os.path.exists(file_path):
                os.remove(file_path)
                
        return jsonify({'success': True, 'methods': matched_methods})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
