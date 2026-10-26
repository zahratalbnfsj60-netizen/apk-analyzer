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
    <title>مستخرج دوال المميزات من ملفات DEX</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #121212; color: #e0e0e0; padding: 20px; text-align: center; }
        .container { max-width: 650px; background: #1e1e1e; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); margin: auto; }
        h2 { color: #4da6ff; }
        input[type="file"] { margin: 20px 0; color: #fff; }
        button { background: #007bff; color: white; border: none; padding: 12px 25px; border-radius: 8px; font-weight: bold; cursor: pointer; width: 100%; font-size: 1rem; }
        button:hover { background: #0056b3; }
        
        #progress-container { width: 100%; background: #333; border-radius: 8px; margin-top: 20px; overflow: hidden; display: none; }
        #progress-bar { width: 0%; height: 22px; background: #00ff66; text-align: center; color: #000; font-weight: bold; font-size: 0.9rem; transition: width 0.3s ease; }
        
        #status { margin-top: 10px; color: #ffca28; font-size: 0.95rem; }
        #output { text-align: left; background: #000; color: #00ff66; padding: 15px; border-radius: 8px; margin-top: 20px; max-height: 350px; overflow-y: auto; direction: ltr; font-family: monospace; white-space: pre-wrap; font-size: 0.85rem; }
    </style>
</head>
<body>
<div class="container">
    <h2>فحص ملفات DEX واستخراج دوال VIP & Pro</h2>
    <p style="color: #aaa; font-size: 0.9rem;">اختر ملف DEX (مثل classes.dex) لاستخراج دوال فتح المميزات والاشتراكات:</p>
    
    <input type="file" id="dexFile"><br>
    <button onclick="uploadAndAnalyze()">بدء تحليل ملف DEX</button>

    <div id="progress-container">
        <div id="progress-bar">0%</div>
    </div>
    <div id="status"></div>

    <div id="output">نتائج استخراج الدوال ستظهر هنا...</div>
</div>

<script>
    function uploadAndAnalyze() {
        const fileInput = document.getElementById('dexFile');
        const outputDiv = document.getElementById('output');
        const statusDiv = document.getElementById('status');
        const progressContainer = document.getElementById('progress-container');
        const progressBar = document.getElementById('progress-bar');

        if (fileInput.files.length === 0) {
            alert('الرجاء اختيار ملف DEX أولاً!');
            return;
        }

        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);

        progressContainer.style.display = 'block';
        progressBar.style.width = '0%';
        progressBar.innerText = '0%';
        statusDiv.innerText = 'جاري رفع الملف...';
        outputDiv.innerText = '';

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/analyze', true);

        xhr.upload.onprogress = function (e) {
            if (e.lengthComputable) {
                const percentComplete = Math.round((e.loaded / e.total) * 40);
                progressBar.style.width = percentComplete + '%';
                progressBar.innerText = percentComplete + '%';
                statusDiv.innerText = `جاري الرفع... (${percentComplete}%)`;
            }
        };

        let currentProgress = 40;
        const interval = setInterval(() => {
            if (currentProgress < 90) {
                currentProgress += 5;
                progressBar.style.width = currentProgress + '%';
                progressBar.innerText = currentProgress + '%';
                statusDiv.innerText = `جاري تحليل هيكل DEX واستخراج الدوال... (${currentProgress}%)`;
            }
        }, 600);

        xhr.onload = function () {
            clearInterval(interval);
            if (xhr.status === 200) {
                try {
                    const result = JSON.parse(xhr.responseText);
                    progressBar.style.width = '100%';
                    progressBar.innerText = '100%';
                    
                    if (result.success) {
                        statusDiv.innerText = `تم الانتهاء! العثور على ${result.methods.length} دالة مطابقة:`;
                        if (result.methods.length > 0) {
                            outputDiv.innerText = result.methods.join('\\n');
                        } else {
                            outputDiv.innerText = 'لم يتم العثور على دوال مطابقة لكلمات VIP/Pro في هذا الملف.';
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
</script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({'success': محل, 'error': 'لم يتم العثور على الملف'})
    
    file = request.files['file']
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    try:
        # استخدام AnalyzeAPK لقراءة ملف الـ DEX مباشرة بدون أخطاء المسارات الداخلية
        a, d, dx = AnalyzeAPK(file_path)
        
        unlock_keywords = [
            'vip', 'pro', 'premium', 'unlock', 'lock', 'sub', 'subscription', 
            'license', 'auth', 'purchase', 'pay', 'billing', 'inapp', 'gold', 'plus'
        ]
        
        matched_methods = []
        for method in dx.get_methods():
            class_name = method.get_class_name()
            method_name = method.get_name()
            full_sig = f"Class: {class_name} --> Method: {method_name}"
            
            lower_sig = full_sig.lower()
            if any(kw in lower_sig for kw in unlock_keywords):
                matched_methods.append(full_sig)
                if len(matched_methods) >= 800:
                    break
                    
        os.remove(file_path)
        return jsonify({'success': True, 'methods': matched_methods})
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
