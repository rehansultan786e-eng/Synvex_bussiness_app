import React, { useState, useEffect } from 'react';
import {
  MapPin, Save, CheckCircle, XCircle,
  Loader2, Navigation, Building2, Radio,
  Shield, Plus, Trash2, Wifi, ToggleLeft, ToggleRight
} from 'lucide-react';
import axios from 'axios';

const api = axios.create({ baseURL: 'http://localhost:8000' });
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

const Settings: React.FC = () => {
  // Geo-fencing state
  const [geoForm, setGeoForm] = useState({
    office_name: 'Main Office',
    latitude: '',
    longitude: '',
    radius: '100',
  });
  const [geoLoading, setGeoLoading] = useState(true);
  const [geoSaving, setGeoSaving] = useState(false);
  const [geoSuccess, setGeoSuccess] = useState('');
  const [geoError, setGeoError] = useState('');
  const [locating, setLocating] = useState(false);

  // IP settings state
  const [ipEnabled, setIpEnabled] = useState(false);
  const [allowedIps, setAllowedIps] = useState<string[]>([]);
  const [newIp, setNewIp] = useState('');
  const [ipLoading, setIpLoading] = useState(true);
  const [ipSaving, setIpSaving] = useState(false);
  const [ipSuccess, setIpSuccess] = useState('');
  const [ipError, setIpError] = useState('');
  const [currentIp, setCurrentIp] = useState('');

  useEffect(() => {
    fetchGeoSettings();
    fetchIpSettings();
    fetchCurrentIp();
  }, []);

  const fetchGeoSettings = async () => {
    try {
      const res = await api.get('/api/settings/office');
      if (res.data.data) {
        const d = res.data.data;
        setGeoForm({
          office_name: d.office_name || 'Main Office',
          latitude: String(d.latitude),
          longitude: String(d.longitude),
          radius: String(d.radius),
        });
      }
    } catch (err) { console.error(err); }
    finally { setGeoLoading(false); }
  };

  const fetchIpSettings = async () => {
    try {
      const res = await api.get('/api/ip-settings/');
      if (res.data.data) {
        setAllowedIps(res.data.data.allowed_ips || []);
        setIpEnabled(res.data.data.ip_check_enabled || false);
      }
    } catch (err) { console.error(err); }
    finally { setIpLoading(false); }
  };

  const fetchCurrentIp = async () => {
    try {
      const res = await api.post('/api/ip-settings/verify');
      setCurrentIp(res.data.client_ip);
    } catch (err) { console.error(err); }
  };

  const handleGeoSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setGeoSaving(true);
    setGeoError('');
    setGeoSuccess('');
    try {
      await api.post('/api/settings/office', {
        office_name: geoForm.office_name,
        latitude: parseFloat(geoForm.latitude),
        longitude: parseFloat(geoForm.longitude),
        radius: parseFloat(geoForm.radius),
      });
      setGeoSuccess('Office location saved successfully!');
    } catch (err: any) {
      setGeoError(err.response?.data?.detail || 'Failed to save settings');
    } finally { setGeoSaving(false); }
  };

  const getCurrentLocation = () => {
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setGeoForm({
          ...geoForm,
          latitude: String(pos.coords.latitude.toFixed(6)),
          longitude: String(pos.coords.longitude.toFixed(6)),
        });
        setLocating(false);
      },
      () => {
        setGeoError('Could not get location. Please enter manually.');
        setLocating(false);
      }
    );
  };

  const handleAddIp = () => {
    const ip = newIp.trim();
    if (!ip) return;
    const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (!ipRegex.test(ip)) {
      setIpError('Invalid IP address format');
      return;
    }
    if (allowedIps.includes(ip)) {
      setIpError('IP already exists');
      return;
    }
    setAllowedIps([...allowedIps, ip]);
    setNewIp('');
    setIpError('');
  };

  const handleRemoveIp = (ip: string) => {
    setAllowedIps(allowedIps.filter(i => i !== ip));
  };

  const handleAddCurrentIp = () => {
    if (currentIp && !allowedIps.includes(currentIp)) {
      setAllowedIps([...allowedIps, currentIp]);
    }
  };

  const handleIpSave = async () => {
    setIpSaving(true);
    setIpError('');
    setIpSuccess('');
    try {
      await api.post('/api/ip-settings/', {
        allowed_ips: allowedIps,
        ip_check_enabled: ipEnabled,
      });
      setIpSuccess('IP settings saved successfully!');
    } catch (err: any) {
      setIpError(err.response?.data?.detail || 'Failed to save IP settings');
    } finally { setIpSaving(false); }
  };

  if (geoLoading || ipLoading) return (
    <div className="flex items-center justify-center h-64">
      <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
    </div>
  );

  return (
    <div className="max-w-2xl mx-auto space-y-5">

      {/* Geo-Fencing Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center">
            <MapPin className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <h3 className="font-bold text-slate-800">Geo-Fencing Settings</h3>
            <p className="text-slate-400 text-xs">Location based attendance control</p>
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 mb-5">
          <div className="flex items-start gap-3">
            <Radio className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
            <p className="text-blue-600 text-xs leading-relaxed">
              Employees can only mark attendance when they are within the allowed radius of the office location.
            </p>
          </div>
        </div>

        {geoSuccess && (
          <div className="flex items-center gap-2 bg-green-50 border border-green-200 text-green-700 rounded-xl p-3 mb-4 text-sm">
            <CheckCircle className="w-4 h-4 flex-shrink-0" />
            {geoSuccess}
          </div>
        )}
        {geoError && (
          <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-600 rounded-xl p-3 mb-4 text-sm">
            <XCircle className="w-4 h-4 flex-shrink-0" />
            {geoError}
          </div>
        )}

        <form onSubmit={handleGeoSave} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Office Name</label>
            <div className="relative">
              <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                value={geoForm.office_name}
                onChange={(e) => setGeoForm({ ...geoForm, office_name: e.target.value })}
                className="w-full pl-9 pr-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Latitude</label>
              <input
                type="number"
                step="any"
                value={geoForm.latitude}
                onChange={(e) => setGeoForm({ ...geoForm, latitude: e.target.value })}
                placeholder="e.g. 28.300000"
                className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Longitude</label>
              <input
                type="number"
                step="any"
                value={geoForm.longitude}
                onChange={(e) => setGeoForm({ ...geoForm, longitude: e.target.value })}
                placeholder="e.g. 70.130000"
                className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                required
              />
            </div>
          </div>

          <button
            type="button"
            onClick={getCurrentLocation}
            disabled={locating}
            className="w-full flex items-center justify-center gap-2 py-2.5 border border-blue-200 bg-blue-50 hover:bg-blue-100 text-blue-600 rounded-xl text-sm font-medium transition disabled:opacity-60"
          >
            {locating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Navigation className="w-4 h-4" />}
            {locating ? 'Getting Location...' : 'Use My Current Location'}
          </button>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Allowed Radius (meters)</label>
            <input
              type="number"
              value={geoForm.radius}
              onChange={(e) => setGeoForm({ ...geoForm, radius: e.target.value })}
              min="10"
              max="10000"
              className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
              required
            />
            <p className="text-slate-400 text-xs mt-1">
              Employees within {geoForm.radius || '100'} meters can mark attendance
            </p>
          </div>

          <button
            type="submit"
            disabled={geoSaving}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-semibold text-sm transition disabled:opacity-60 flex items-center justify-center gap-2"
          >
            {geoSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            {geoSaving ? 'Saving...' : 'Save Geo-Fencing Settings'}
          </button>
        </form>
      </div>

      {/* IP Whitelist Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-50 rounded-xl flex items-center justify-center">
              <Wifi className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <h3 className="font-bold text-slate-800">IP Whitelist Settings</h3>
              <p className="text-slate-400 text-xs">Office network based access control</p>
            </div>
          </div>
          {/* Toggle */}
          <button
            onClick={() => setIpEnabled(!ipEnabled)}
            className="flex items-center gap-2 text-sm font-medium transition"
          >
            {ipEnabled
              ? <ToggleRight className="w-8 h-8 text-green-500" />
              : <ToggleLeft className="w-8 h-8 text-slate-400" />
            }
            <span className={ipEnabled ? 'text-green-600' : 'text-slate-400'}>
              {ipEnabled ? 'Enabled' : 'Disabled'}
            </span>
          </button>
        </div>

        {/* Current IP */}
        {currentIp && (
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 mb-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 mb-1">Your Current IP</p>
                <p className="font-mono font-bold text-slate-800">{currentIp}</p>
              </div>
              <button
                onClick={handleAddCurrentIp}
                disabled={allowedIps.includes(currentIp)}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-xs font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Plus className="w-3 h-3" />
                {allowedIps.includes(currentIp) ? 'Already Added' : 'Add This IP'}
              </button>
            </div>
          </div>
        )}

        {ipSuccess && (
          <div className="flex items-center gap-2 bg-green-50 border border-green-200 text-green-700 rounded-xl p-3 mb-4 text-sm">
            <CheckCircle className="w-4 h-4 flex-shrink-0" />
            {ipSuccess}
          </div>
        )}
        {ipError && (
          <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-600 rounded-xl p-3 mb-4 text-sm">
            <XCircle className="w-4 h-4 flex-shrink-0" />
            {ipError}
          </div>
        )}

        {/* Add IP */}
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            value={newIp}
            onChange={(e) => setNewIp(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAddIp()}
            placeholder="e.g. 203.128.24.136"
            className="flex-1 px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 transition font-mono"
          />
          <button
            onClick={handleAddIp}
            className="flex items-center gap-1.5 px-4 py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-sm font-semibold transition"
          >
            <Plus className="w-4 h-4" />
            Add
          </button>
        </div>

        {/* IP List */}
        {allowedIps.length > 0 ? (
          <div className="space-y-2 mb-5">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
              Whitelisted IPs ({allowedIps.length})
            </p>
            {allowedIps.map((ip) => (
              <div key={ip} className="flex items-center justify-between bg-slate-50 border border-slate-200 rounded-xl px-4 py-3">
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-green-500" />
                  <span className="font-mono text-sm text-slate-800">{ip}</span>
                  {ip === currentIp && (
                    <span className="text-xs bg-blue-100 text-blue-600 px-2 py-0.5 rounded-full">Current</span>
                  )}
                </div>
                <button
                  onClick={() => handleRemoveIp(ip)}
                  className="p-1.5 rounded-lg hover:bg-red-50 text-slate-400 hover:text-red-500 transition"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-6 mb-4 bg-slate-50 rounded-xl border border-dashed border-slate-200">
            <Wifi className="w-8 h-8 text-slate-300 mx-auto mb-2" />
            <p className="text-slate-400 text-sm">No IPs whitelisted yet</p>
          </div>
        )}

        <button
          onClick={handleIpSave}
          disabled={ipSaving}
          className="w-full py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-xl font-semibold text-sm transition disabled:opacity-60 flex items-center justify-center gap-2"
        >
          {ipSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          {ipSaving ? 'Saving...' : 'Save IP Settings'}
        </button>
      </div>
    </div>
  );
};

export default Settings;