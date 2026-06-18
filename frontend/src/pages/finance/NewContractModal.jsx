import React, { useState, useEffect } from 'react';
import { X, Plus, Trash2, Loader2 } from 'lucide-react';
import { financeService } from '../../services/financeService';

const CURRENCIES = ['PKR', 'USD', 'EUR', 'GBP'];

const emptyMilestone = () => ({
  description: '',
  due_date: '',
  amount: ''
});

const NewContractModal = ({ onClose, onCreated }) => {
  const [clientName, setClientName] = useState('');
  const [projectName, setProjectName] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [totalValue, setTotalValue] = useState('');
  const [currency, setCurrency] = useState('PKR');
  const [salesRepId, setSalesRepId] = useState('');

  const [salesReps, setSalesReps] = useState([]);
  const [repsLoading, setRepsLoading] = useState(true);

  const [milestones, setMilestones] = useState([emptyMilestone()]);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadReps = async () => {
      setRepsLoading(true);
      try {
        const res = await financeService.getSalesReps();
        setSalesReps(res.data || []);
      } catch (err) {
        setError('Could not load sales reps: ' + err.message);
      } finally {
        setRepsLoading(false);
      }
    };
    loadReps();
  }, []);

  const updateMilestone = (index, field, value) => {
    const updated = milestones.map((m, i) => {
      if (i === index) {
        return { ...m, [field]: value };
      }
      return m;
    });
    setMilestones(updated);
  };

  const addMilestoneRow = () => {
    setMilestones([...milestones, emptyMilestone()]);
  };

  const removeMilestoneRow = (index) => {
    setMilestones(milestones.filter((m, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!clientName || !projectName || !startDate || !totalValue) {
      setError('Please fill in all required fields.');
      return;
    }

    const cleanedMilestones = milestones
      .filter((m) => m.description && m.due_date && m.amount)
      .map((m) => ({
        description: m.description,
        due_date: m.due_date,
        amount: parseFloat(m.amount)
      }));

    const payload = {
      client_name: clientName,
      project_name: projectName,
      start_date: startDate,
      end_date: endDate || null,
      total_value: parseFloat(totalValue),
      currency: currency,
      sales_rep_id: salesRepId || null,
      milestones: cleanedMilestones
    };

    setSubmitting(true);
    try {
      await financeService.createContract(payload);
      onCreated();
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-card shadow-elevated w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 sticky top-0 bg-white">
          <h2 className="text-lg font-semibold text-gray-900">New Contract</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-5">
          {error && (
            <div className="px-4 py-2.5 rounded-control bg-red-50 text-red-700 text-sm">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Client Name *</label>
              <input
                type="text"
                value={clientName}
                onChange={(e) => setClientName(e.target.value)}
                className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Project Name *</label>
              <input
                type="text"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Start Date *</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">End Date</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Total Value *</label>
              <input
                type="number"
                value={totalValue}
                onChange={(e) => setTotalValue(e.target.value)}
                className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Currency</label>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
              >
                {CURRENCIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Sales Rep</label>
              <select
                value={salesRepId}
                onChange={(e) => setSalesRepId(e.target.value)}
                disabled={repsLoading}
                className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
              >
                <option value="">{repsLoading ? 'Loading...' : 'Unassigned'}</option>
                {salesReps.map((rep) => (
                  <option key={rep.id} value={rep.id}>{rep.full_name}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-xs font-medium text-gray-500">Milestones</label>
              <button
                type="button"
                onClick={addMilestoneRow}
                className="flex items-center gap-1 text-primary-light text-xs font-medium hover:underline"
              >
                <Plus className="w-3.5 h-3.5" />
                Add Milestone
              </button>
            </div>

            <div className="space-y-2.5">
              {milestones.map((m, index) => (
                <div key={index} className="grid grid-cols-1 sm:grid-cols-[2fr_1fr_1fr_auto] gap-2 bg-surface-subtle p-3 rounded-control">
                  <input
                    type="text"
                    placeholder="Description"
                    value={m.description}
                    onChange={(e) => updateMilestone(index, 'description', e.target.value)}
                    className="px-3 py-2 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
                  />
                  <input
                    type="date"
                    value={m.due_date}
                    onChange={(e) => updateMilestone(index, 'due_date', e.target.value)}
                    className="px-3 py-2 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
                  />
                  <input
                    type="number"
                    placeholder="Amount"
                    value={m.amount}
                    onChange={(e) => updateMilestone(index, 'amount', e.target.value)}
                    className="px-3 py-2 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
                  />
                  <button
                    type="button"
                    onClick={() => removeMilestoneRow(index)}
                    className="flex items-center justify-center px-2 text-gray-400 hover:text-red-500"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-2 border-t border-gray-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-control text-sm font-medium text-gray-600 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex items-center gap-1.5 bg-primary hover:bg-primary-dark text-white px-4 py-2.5 rounded-control text-sm font-medium transition-colors disabled:opacity-60"
            >
              {submitting && <Loader2 className="w-4 h-4 animate-spin" />}
              Create Contract
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default NewContractModal;