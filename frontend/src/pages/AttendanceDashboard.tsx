import React, { useState, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import {
  Camera, ScanFace, CheckCircle, XCircle, Clock,
  User, Building2, Hash, Send, ChevronDown, Loader2,
  MapPin, Navigation, Shield, LogIn, LogOut, Eye
} from 'lucide-react';
import { leaveAPI } from '../services/api';
import axios from 'axios';
import LivenessCheck from '../components/LivenessCheck';

const api = axios.create({ baseURL: 'http://localhost:8000' });

const ScanAnimation: React.FC = () => (
  <div className="absolute inset-0 rounded-2xl overflow-hidden pointer-events-none">
    <div className="scan-line" />
    {[0, 1, 2, 3].map((i) => (
      <div key={i} className={`corner-bracket corner-${i}`} />
    ))}
  </div>
);

type ScanMode = 'checkin' | 'checkout';
type Step = 'idle' | 'location' | 'liveness' | 'scan' | 'complete';

const AttendanceDashboard: React.FC = () => {
  const webcamRef = useRef<Webcam>(null);
  const [step, setStep] = useState<Step>('idle');
  const [scanning, setScanning] = useState(false);
  const [attendanceResult, setAttendanceResult] = useState<any>(null);
  const [error, setError] = useState('');
  const [scanMode, setScanMode] = useState<ScanMode>('checkin');
  const [locationChecking, setLocationChecking] = useState(false);
  const [distance, setDistance] = useState<number | null>(null);

  const [leaveForm, setLeaveForm] = useState({
    employee_id: '', leave_date: '', leave_type: '', reason: ''
  });
  const [leaveLoading, setLeaveLoading] = useState(false);
  const [leaveSuccess, setLeaveSuccess] = useState('');
  const [leaveError, setLeaveError] = useState('');

  const checkLocation = useCallback(async (mode: ScanMode) => {
    setLocationChecking(true);
    setStep('location');
    setError('');
    setScanMode(mode);

    // IP Check API call (Admin settings ke mutabiq backend handles it)
    try {
      const ipRes = await api.post('/api/ip-settings/verify');
      if (!ipRes.data.allowed) {
        setError(ipRes.data.message);
        setStep('idle');
        setLocationChecking(false);
        return;
      }
    } catch { 
      // API fail hone par exception handle block
    }

    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser.');
      setStep('idle');
      setLocationChecking(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const res = await api.post('/api/settings/verify-location', {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          });
          setDistance(res.data.distance);
          if (res.data.allowed) {
            setStep('liveness');
          } else {
            setError(res.data.message);
            setStep('idle');
          }
        } catch {
          setStep('liveness');
        } finally {
          setLocationChecking(false);
        }
      },
      () => {
        setError('Location access denied. Please allow location access.');
        setStep('idle');
        setLocationChecking(false);
      },
      { timeout: 5000, enableHighAccuracy: false }
    );
  }, []);

  const handleLivenessSuccess = useCallback(() => {
    setStep('scan');
  }, []);

  const handleLivenessFail = useCallback(() => {
    setError('Liveness check failed. Please try again.');
    setStep('idle');
  }, []);

  const handleScan = useCallback(async () => {
    if (!webcamRef.current) return;
    setScanning(true);
    setError('');

    const imageSrc = webcamRef.current.getScreenshot();
    if (!imageSrc) {
      setError('Could not capture image');
      setScanning(false);
      return;
    }

    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      const response = await api.post('/api/attendance/mark', {
        image_base64: imageSrc,
        mode: scanMode
      });
      setAttendanceResult({ ...response.data.data, mode: scanMode });
      setStep('complete');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Face not recognized. Please try again.');
    } finally {
      setScanning(false);
    }
  }, [scanMode]);

  const handleLeaveSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLeaveLoading(true);
    setLeaveError('');
    setLeaveSuccess('');
    try {
      await leaveAPI.submit(leaveForm);
      setLeaveSuccess('Leave request submitted successfully!');
      setLeaveForm({ employee_id: '', leave_date: '', leave_type: '', reason: '' });
    } catch (err: any) {
      setLeaveError(err.response?.data?.detail || 'Failed to submit leave request');
    } finally {
      setLeaveLoading(false);
    }
  };

  const resetAll = () => {
    setStep('idle');
    setAttendanceResult(null);
    setError('');
    setDistance(null);
    setScanning(false);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-blue-600 rounded-xl flex items-center justify-center">
            <ScanFace className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-slate-800 text-base">SYNVEX</h1>
            <p className="text-slate-400 text-xs">Attendance System</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex flex-col items-end">
            <span className="text-sm font-semibold text-slate-700">
              {new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })}
            </span>
            <span className="text-xs text-slate-400">
              {new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
            </span>
          </div>
          <button
            onClick={() => window.location.href = '/login'}
            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-sm font-medium transition"
          >
            <Shield className="w-4 h-4" />
            Admin Login
          </button>
        </div>
      </div>

      <div className="max-w-5xl mx-auto p-6 grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Attendance Card */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center">
              <Camera className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h2 className="font-bold text-slate-800">Mark Attendance</h2>
              <p className="text-slate-400 text-xs">
                {step === 'liveness' ? 'Step 2: Liveness Check' :
                 step === 'scan' ? 'Step 3: Face Scan' :
                 'Location + Liveness + Face Recognition'}
              </p>
            </div>
          </div>

          {/* Step Indicator */}
          {step !== 'idle' && step !== 'complete' && (
            <div className="flex items-center gap-2 mb-5">
              {[
                { key: 'location', label: 'Location', icon: MapPin },
                { key: 'liveness', label: 'Liveness', icon: Eye },
                { key: 'scan', label: 'Face Scan', icon: ScanFace },
              ].map(({ key, label, icon: Icon }, index) => {
                const steps = ['location', 'liveness', 'scan'];
                const currentIndex = steps.indexOf(step);
                const itemIndex = steps.indexOf(key);
                const isDone = itemIndex < currentIndex;
                const isCurrent = key === step;
                return (
                  <React.Fragment key={key}>
                    <div className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium
                      ${isCurrent ? 'bg-blue-100 text-blue-700' :
                        isDone ? 'bg-green-100 text-green-700' :
                        'bg-slate-100 text-slate-400'}`}>
                      <Icon className="w-3 h-3" />
                      {label}
                    </div>
                    {index < 2 && <div className="flex-1 h-px bg-slate-200" />}
                  </React.Fragment>
                );
              })}
            </div>
          )}

          {/* Success State */}
          {step === 'complete' && attendanceResult && (
            <div className="text-center">
              <div className={`w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4
                ${attendanceResult.mode === 'checkin' ? 'bg-green-50' : 'bg-blue-50'}`}>
                <CheckCircle className={`w-9 h-9 ${attendanceResult.mode === 'checkin' ? 'text-green-500' : 'text-blue-500'}`} />
              </div>
              <h3 className="font-bold text-slate-800 text-lg mb-1">
                {attendanceResult.mode === 'checkin' ? 'Check-In Successful!' : 'Check-Out Successful!'}
              </h3>
              <p className="text-slate-400 text-sm mb-5">
                {attendanceResult.mode === 'checkin' ? 'Your attendance has been recorded.' : 'Have a great day!'}
              </p>
              <div className="bg-slate-50 rounded-xl p-4 space-y-3 text-left mb-5">
                {[
                  { icon: User, label: 'Name', value: attendanceResult.employee_name },
                  { icon: Hash, label: 'Employee ID', value: attendanceResult.employee_id },
                  { icon: Building2, label: 'Department', value: attendanceResult.department },
                  {
                    icon: Clock,
                    label: attendanceResult.mode === 'checkin' ? 'Check-In Time' : 'Check-Out Time',
                    value: attendanceResult.mode === 'checkin' ? attendanceResult.check_in : attendanceResult.check_out
                  },
                ].map(({ icon: Icon, label, value }) => (
                  <div key={label} className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-slate-500 text-sm">
                      <Icon className="w-4 h-4" />
                      {label}
                    </div>
                    <span className="text-slate-800 font-medium text-sm">{value}</span>
                  </div>
                ))}
                {attendanceResult.mode === 'checkin' && (
                  <div className="flex items-center justify-between pt-2 border-t border-slate-200">
                    <span className="text-slate-500 text-sm">Status</span>
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold capitalize
                      ${attendanceResult.status === 'present' ? 'bg-green-100 text-green-700' :
                        attendanceResult.status === 'late' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-blue-100 text-blue-700'}`}>
                      {attendanceResult.status}
                    </span>
                  </div>
                )}
                {attendanceResult.mode === 'checkout' && attendanceResult.work_hours && (
                  <div className="flex items-center justify-between pt-2 border-t border-slate-200">
                    <span className="text-slate-500 text-sm">Total Hours</span>
                    <span className="text-slate-800 font-bold text-sm">{attendanceResult.work_hours}h</span>
                  </div>
                )}
              </div>
              <button onClick={resetAll} className="w-full py-3 border border-slate-200 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-50 transition">
                Done
              </button>
            </div>
          )}

          {/* Liveness Check Step */}
          {step === 'liveness' && (
            <LivenessCheck
              onSuccess={handleLivenessSuccess}
              onFail={handleLivenessFail}
            />
          )}

          {/* Face Scan Step */}
          {step === 'scan' && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <div className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5
                  ${scanMode === 'checkin' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>
                  {scanMode === 'checkin' ? <LogIn className="w-3.5 h-3.5" /> : <LogOut className="w-3.5 h-3.5" />}
                  {scanMode === 'checkin' ? 'Check-In Mode' : 'Check-Out Mode'}
                </div>
                {distance !== null && (
                  <span className="text-xs text-slate-400 flex items-center gap-1">
                    <MapPin className="w-3 h-3" />
                    {distance}m
                  </span>
                )}
              </div>

              <div className="relative rounded-2xl overflow-hidden bg-slate-900 mb-4" style={{ aspectRatio: '4/3' }}>
                <Webcam
                  ref={webcamRef}
                  screenshotFormat="image/jpeg"
                  className="w-full h-full object-cover"
                  videoConstraints={{ facingMode: 'user' }}
                />
                {scanning && <ScanAnimation />}
                <div className="absolute bottom-3 left-0 right-0 text-center">
                  <span className="bg-black/60 text-white text-xs px-3 py-1 rounded-full">
                    {scanning ? 'Scanning face...' : 'Position your face in the frame'}
                  </span>
                </div>
                <div className="absolute top-3 left-3">
                  <span className="flex items-center gap-1 bg-green-500/90 text-white text-xs px-2.5 py-1 rounded-full">
                    <CheckCircle className="w-3 h-3" />
                    Liveness Verified
                  </span>
                </div>
              </div>

              {error && (
                <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-600 rounded-xl p-3 mb-4 text-sm">
                  <XCircle className="w-4 h-4 flex-shrink-0" />
                  {error}
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={resetAll}
                  className="py-3 border border-slate-200 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-50 transition"
                >
                  Cancel
                </button>
                <button
                  onClick={handleScan}
                  disabled={scanning}
                  className={`py-3 text-white rounded-xl text-sm font-semibold transition disabled:opacity-60 flex items-center justify-center gap-2
                    ${scanMode === 'checkin' ? 'bg-green-600 hover:bg-green-700' : 'bg-blue-600 hover:bg-blue-700'}`}
                >
                  {scanning ? <Loader2 className="w-4 h-4 animate-spin" /> : <ScanFace className="w-4 h-4" />}
                  {scanning ? 'Scanning...' : 'Scan Face'}
                </button>
              </div>
            </div>
          )}

          {/* Default State */}
          {step === 'idle' && (
            <div className="text-center">
              <div className="w-20 h-20 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-5">
                <ScanFace className="w-10 h-10 text-blue-600" />
              </div>

              <p className="text-slate-500 text-sm mb-2 font-medium">3-Step Verification</p>
              <div className="flex items-center justify-center gap-4 mb-6 text-xs text-slate-400">
                <span className="flex items-center gap-1"><MapPin className="w-3 h-3" /> Location</span>
                <span>→</span>
                <span className="flex items-center gap-1"><Eye className="w-3 h-3" /> Liveness</span>
                <span>→</span>
                <span className="flex items-center gap-1"><ScanFace className="w-3 h-3" /> Face Scan</span>
              </div>

              {error && (
                <div className="flex items-start gap-2 bg-red-50 border border-red-200 text-red-600 rounded-xl p-3 mb-4 text-sm text-left">
                  <XCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => checkLocation('checkin')}
                  disabled={locationChecking}
                  className="flex flex-col items-center gap-2 py-5 bg-green-600 hover:bg-green-700 text-white rounded-2xl font-semibold text-sm transition disabled:opacity-60"
                >
                  <LogIn className="w-6 h-6" />
                  Check In
                </button>
                <button
                  onClick={() => checkLocation('checkout')}
                  disabled={locationChecking}
                  className="flex flex-col items-center gap-2 py-5 bg-blue-600 hover:bg-blue-700 text-white rounded-2xl font-semibold text-sm transition disabled:opacity-60"
                >
                  <LogOut className="w-6 h-6" />
                  Check Out
                </button>
              </div>

              <p className="text-slate-400 text-xs mt-3 flex items-center justify-center gap-1">
                <MapPin className="w-3 h-3" />
                Location + Liveness verification required
              </p>
            </div>
          )}

          {/* Location Loader Block */}
          {step === 'location' && (
            <div className="flex items-center justify-center gap-2 bg-blue-50 border border-blue-200 text-blue-600 rounded-xl p-6 text-sm my-4">
              <Loader2 className="w-5 h-5 animate-spin flex-shrink-0" />
              <span>Verifying location and IP settings...</span>
            </div>
          )}
        </div>

        {/* Leave Application Card */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-purple-50 rounded-xl flex items-center justify-center">
              <Send className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <h2 className="font-bold text-slate-800">Apply Leave</h2>
              <p className="text-slate-400 text-xs">Submit leave request</p>
            </div>
          </div>

          {leaveSuccess && (
            <div className="flex items-center gap-2 bg-green-50 border border-green-200 text-green-700 rounded-xl p-3 mb-4 text-sm">
              <CheckCircle className="w-4 h-4 flex-shrink-0" />
              {leaveSuccess}
            </div>
          )}
          {leaveError && (
            <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-600 rounded-xl p-3 mb-4 text-sm">
              <XCircle className="w-4 h-4 flex-shrink-0" />
              {leaveError}
            </div>
          )}

          <form onSubmit={handleLeaveSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Employee ID</label>
              <input
                type="text"
                value={leaveForm.employee_id}
                onChange={(e) => setLeaveForm({ ...leaveForm, employee_id: e.target.value })}
                placeholder="e.g. EMP001"
                className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Leave Date</label>
              <input
                type="date"
                value={leaveForm.leave_date}
                onChange={(e) => setLeaveForm({ ...leaveForm, leave_date: e.target.value })}
                className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Leave Type</label>
              <div className="relative">
                <select
                  value={leaveForm.leave_type}
                  onChange={(e) => setLeaveForm({ ...leaveForm, leave_type: e.target.value })}
                  className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition appearance-none bg-white"
                  required
                >
                  <option value="">Select leave type</option>
                  <option value="Casual Leave">Casual Leave</option>
                  <option value="Sick Leave">Sick Leave</option>
                  <option value="Annual Leave">Annual Leave</option>
                  <option value="Emergency Leave">Emergency Leave</option>
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Reason</label>
              <textarea
                value={leaveForm.reason}
                onChange={(e) => setLeaveForm({ ...leaveForm, reason: e.target.value })}
                placeholder="Briefly describe your reason..."
                rows={3}
                className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition resize-none"
                required
              />
            </div>
            <button
              type="submit"
              disabled={leaveLoading}
              className="w-full py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-xl font-semibold text-sm transition disabled:opacity-60 flex items-center justify-center gap-2"
            >
              {leaveLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              {leaveLoading ? 'Submitting...' : 'Submit Leave Request'}
            </button>
          </form>
        </div>
      </div>

      <style>{`
        .scan-line {
          position: absolute;
          left: 0; right: 0;
          height: 3px;
          background: linear-gradient(90deg, transparent, #22C55E, #22C55E, transparent);
          box-shadow: 0 0 8px #22C55E;
          animation: scan 2s ease-in-out infinite;
          border-radius: 2px;
        }
        @keyframes scan {
          0% { top: 10%; opacity: 1; }
          50% { top: 85%; opacity: 1; }
          100% { top: 10%; opacity: 1; }
        }
        .corner-bracket {
          position: absolute;
          width: 24px; height: 24px;
          border-color: #22C55E;
          border-style: solid;
        }
        .corner-0 { top: 12px; left: 12px; border-width: 3px 0 0 3px; border-radius: 3px 0 0 0; }
        .corner-1 { top: 12px; right: 12px; border-width: 3px 3px 0 0; border-radius: 0 3px 0 0; }
        .corner-2 { bottom: 12px; left: 12px; border-width: 0 0 3px 3px; border-radius: 0 0 0 3px; }
        .corner-3 { bottom: 12px; right: 12px; border-width: 0 3px 3px 0; border-radius: 0 0 3px 0; }
      `}</style>
    </div>
  );
};

export default AttendanceDashboard;