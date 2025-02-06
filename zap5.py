import os
import secrets  # لتوليد مفتاح عشوائي
from flask import Flask, render_template, send_from_directory, request, redirect, url_for, flash
import magic

app = Flask(__name__, static_folder='static')

# مسار ملف المفتاح
KEY_FILE = 'key.txt'

# وظيفة توليد وحفظ المفتاح العشوائي
def generate_secret_key():
    if not os.path.exists(KEY_FILE):
        secret_key = secrets.token_hex(32)  # توليد مفتاح عشوائي
        with open(KEY_FILE, 'w') as key_file:
            key_file.write(secret_key)
    else:
        with open(KEY_FILE, 'r') as key_file:
            secret_key = key_file.read()
    return secret_key

# إعداد المفتاح السري للتطبيق
app.secret_key = generate_secret_key()

# قائمة الأجهزة المتصلة
connected_devices = []

# تحديد مسارات المجلدات
UPLOAD_FOLDER = '/sdcard/Upload'
DOWNLOAD_FOLDER = '/sdcard/Download '
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # الحد الأقصى لحجم الملف (100 ميجابايت)

# إنشاء المجلدات إذا لم تكن موجودة
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# الصفحة الرئيسية
@app.route('/')
def home():
    files = os.listdir(app.config['UPLOAD_FOLDER'])

    # تسجيل عنوان الـ IP للجهاز الذي زار الصفحة
    ip_address = request.remote_addr
    if ip_address not in connected_devices:
        connected_devices.append(ip_address)

    print("Connected devices:")
    for ip in connected_devices:
        print(ip)

    return render_template('index.html', files=files)

# تنزيل الملفات
@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except FileNotFoundError:
        return "الملف غير موجود", 404

# رفع الملفات
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'files' not in request.files:
            flash("لم يتم إرسال ملفات")
            return redirect(url_for('home'))

        files = request.files.getlist('files')

        # تحقق من العدد الأقصى للملفات
        if len(files) > 50:
            flash("يمكنك رفع 50 ملف فقط في المرة الواحدة!")
            return redirect(url_for('home'))

        for file in files:
            if file.filename == '':
                flash("أحد الملفات بدون اسم")
                continue

            # فلترة الملفات
            mime = magic.Magic(mime=True)
            file_type = mime.from_buffer(file.stream.read(1024))  # قراءة نوع الملف
            file.stream.seek(0)  # إعادة المؤشر لبداية الملف

            if not file_type.startswith(('image/', 'text/', 'application/pdf')):
                flash(f"تم رفض الملف {file.filename}: نوع الملف غير مدعوم.")
                continue

            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))

        flash("تم رفع الملفات بنجاح!")
        return redirect(url_for('home'))

    return render_template('upload.html')

# إدارة الأجهزة المتصلة
@app.route('/admin/devices')
def manage_devices():
    return render_template('devices.html', devices=connected_devices)

@app.route('/admin/remove_device/<ip>', methods=['POST'])
def remove_device(ip):
    if ip in connected_devices:
        connected_devices.remove(ip)
        flash(f"تم إزالة الجهاز {ip}.")
        return redirect(url_for('manage_devices'))
    return "الجهاز غير موجود", 404

# إدارة الملفات
@app.route('/admin/files')
def manage_files():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('files.html', files=files)

@app.route('/admin/delete_file/<filename>', methods=['POST'])
def delete_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f"تم حذف الملف {filename}.")
        return redirect(url_for('manage_files'))
    return "الملف غير موجود", 404

# إعدادات التطبيق
@app.route('/admin/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        upload_folder = request.form.get('upload_folder')
        download_folder = request.form.get('download_folder')

        if upload_folder:
            app.config['UPLOAD_FOLDER'] = upload_folder
            os.makedirs(upload_folder, exist_ok=True)

        if download_folder:
            app.config['DOWNLOAD_FOLDER'] = download_folder
            os.makedirs(download_folder, exist_ok=True)

        flash("تم تحديث الإعدادات بنجاح!")
        return redirect(url_for('settings'))

    return render_template('settings.html', upload_folder=app.config['UPLOAD_FOLDER'], download_folder=app.config['DOWNLOAD_FOLDER'])

# التقارير
@app.route('/admin/reports')
def reports():
    total_devices = len(connected_devices)
    total_files = len(os.listdir(app.config['UPLOAD_FOLDER']))
    return render_template('reports.html', total_devices=total_devices, total_files=total_files)

# صفحة /admin
@app.route('/admin')
def admin():
    return render_template('admin.html')

# صفحة /me
@app.route('/me')
def me():
    return render_template('me.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
