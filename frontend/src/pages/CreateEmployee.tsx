import React, { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Webcam from 'react-webcam';
import {
  User, Mail, Phone, Building2, Briefcase, Calendar,
  Camera, Upload, Trash2, CheckCircle, Loader2, XCircle
} from 'lucide-react';
import { employeeAPI, departmentAPI } from '../services/api';

const CreateEmployee: React.FC = () => {
  const navigate = useNavigate();
  const webcamRef = useRef<Webcam>(null);
  const [cameraOpen, setCameraOpen] = useState(false);
  const [faceImages, setFaceImages] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [departments, setDepartments] = useState<any[]>([]);

  const [form, setForm] = useState({
    employee_id: '', full_name: '', email: '', phone: '',
    department: '', designation: '', joining_date: '', status: 'active'
  });

  React.useEffect(() => {
    departmentAPI.getAll().then(res => setDepartments(res.data.data)).catch(() => {});
  }, []);

  const handleCapture = useCallback(() => {
    if (!webcamRef.current) return;
    const img = webcamRef.current.getScreenshot();
    if (img && faceImages.length < 10) {
      setFaceImages(prev => [...prev, img]);
    }
  }, [faceImages]);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;
    Array.from(files).forEach(file => {
      const reader = new FileReader();
      reader.onload = (ev) => {
        if (ev.target?.result && faceImages.length < 10) {
          setFaceImages(prev => [...prev, ev.target!.result as string]);
        }
      };
      reader.readAsDataURL(file);
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (faceImages.length < 3) {
      setError('Please capture at least 3 face images');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const empRes = await employeeAPI.create(form);
      const employeeId = empRes.data.data.employee_id;
      await employeeAPI.enrollFace(employeeId, faceImages);
      setSuccess('Employee created and face enrolled successfully!');
      setTimeout(() => navigate('/admin/employees'), 1500);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create employee');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-5">

      {error && (
        <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-600 rounded-xl p-4 text-sm">
          <XCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}
      {success && (
        <div className="flex items-center gap-2 bg-green-50 border border-green-200 text-green-700 rounded-xl p-4 text-sm">
          <CheckCircle className="w-4 h-4 flex-shrink-0" />
          {success}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">

        {/* Personal Information */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-9 h-9 bg-blue-50 rounded-xl flex items-center justify-center">
              <User className="w-4 h-4 text-blue-600" />
            </div>
            <h3 className="font-bold text-slate-800">Personal Information</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { label: 'Employee ID', key: 'employee_id', icon: User, placeholder: 'e.g. EMP001' },
              { label: 'Full Name', key: 'full_name', icon: User, placeholder: 'e.g. John Doe' },
              { label: 'Email Address', key: 'email', icon: Mail, placeholder: 'john@synvex.com', type: 'email' },
              { label: 'Phone Number', key: 'phone', icon: Phone, placeholder: '+92 300 0000000' },
            ].map(({ label, key, icon: Icon, placeholder, type }) => (
              <div key={key}>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">{label}</label>
                <div className="relative">
                  <Icon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type={type || 'text'}
                    value={(form as any)[key]}
                    onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                    placeholder={placeholder}
                    className="w-full pl-9 pr-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                    required
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Job Information */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-9 h-9 bg-purple-50 rounded-xl flex items-center justify-center">
              <Briefcase className="w-4 h-4 text-purple-600" />
            </div>
            <h3 className="font-bold text-slate-800">Job Information</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Department</label>
              <div className="relative">
                <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <select
                  value={form.department}
                  onChange={(e) => setForm({ ...form, department: e.target.value })}
                  className="w-full pl-9 pr-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition appearance-none bg-white"
                  required
                >
                  <option value="">Select department</option>
                  {departments.map((d: any) => (
                    <option key={d.id} value={d.department_name}>{d.department_name}</option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Designation</label>
              <div className="relative">
                <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  value={form.designation}
                  onChange={(e) => setForm({ ...form, designation: e.target.value })}
                  placeholder="e.g. Software Engineer"
                  className="w-full pl-9 pr-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                  required
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Joining Date</label>
              <div className="relative">
                <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="date"
                  value={form.joining_date}
                  onChange={(e) => setForm({ ...form, joining_date: e.target.value })}
                  className="w-full pl-9 pr-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                  required
                />
              </div>
            </div>
          </div>
        </div>

        {/* Face Enrollment */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 bg-green-50 rounded-xl flex items-center justify-center">
                <Camera className="w-4 h-4 text-green-600" />
              </div>
              <div>
                <h3 className="font-bold text-slate-800">Face Enrollment</h3>
                <p className="text-slate-400 text-xs">Capture 5-10 face images for recognition</p>
              </div>
            </div>
            <span className={`text-sm font-semibold px-3 py-1 rounded-full ${faceImages.length >= 3 ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
              {faceImages.length}/10 images
            </span>
          </div>

          {cameraOpen && (
            <div className="mb-4">
              <div className="relative rounded-2xl overflow-hidden bg-slate-900 mb-3" style={{ maxWidth: 400 }}>
                <Webcam
                  ref={webcamRef}
                  screenshotFormat="image/jpeg"
                  className="w-full"
                  videoConstraints={{ facingMode: 'user' }}
                />
              </div>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={handleCapture}
                  disabled={faceImages.length >= 10}
                  className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2.5 rounded-xl text-sm font-semibold transition disabled:opacity-50"
                >
                  <Camera className="w-4 h-4" />
                  Capture
                </button>
                <button
                  type="button"
                  onClick={() => setCameraOpen(false)}
                  className="px-4 py-2.5 border border-slate-200 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-50 transition"
                >
                  Close Camera
                </button>
              </div>
            </div>
          )}

          <div className="flex gap-3 mb-4">
            {!cameraOpen && (
              <button
                type="button"
                onClick={() => setCameraOpen(true)}
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2.5 rounded-xl text-sm font-semibold transition"
              >
                <Camera className="w-4 h-4" />
                Open Camera
              </button>
            )}
            <label className="flex items-center gap-2 border border-slate-200 hover:bg-slate-50 text-slate-600 px-4 py-2.5 rounded-xl text-sm font-medium cursor-pointer transition">
              <Upload className="w-4 h-4" />
              Upload Images
              <input type="file" accept="image/*" multiple onChange={handleFileUpload} className="hidden" />
            </label>
          </div>

          {/* Image Previews */}
          {faceImages.length > 0 && (
            <div className="grid grid-cols-5 gap-2">
              {faceImages.map((img, i) => (
                <div key={i} className="relative group">
                  <img src={img} alt={`face-${i}`} className="w-full aspect-square object-cover rounded-xl border border-slate-200" />
                  <button
                    type="button"
                    onClick={() => setFaceImages(faceImages.filter((_, idx) => idx !== i))}
                    className="absolute top-1 right-1 w-5 h-5 bg-red-500 text-white rounded-full items-center justify-center hidden group-hover:flex"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Submit */}
        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => navigate('/admin/employees')}
            className="flex-1 py-3 border border-slate-200 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-50 transition"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="flex-1 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold transition disabled:opacity-60 flex items-center justify-center gap-2"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
            {loading ? 'Creating...' : 'Create Employee'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateEmployee;