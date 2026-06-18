import React, { useState, useEffect } from 'react';
import { Plus, FileText, Loader2 } from 'lucide-react';
import { financeService } from '../../services/financeService';
import StatusBadge from '../../components/StatusBadge';
import NewContractModal from './NewContractModal';

const Contracts = () => {
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showNewModal, setShowNewModal] = useState(false);

  const loadContracts = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await financeService.getContracts();
      setContracts(res.data || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadContracts();
  }, []);

  const milestoneSummary = (contract) => {
    const total = contract.milestones ? contract.milestones.length : 0;
    const received = contract.milestones
      ? contract.milestones.filter((m) => m.status === 'Received').length
      : 0;
    return received + '/' + total + ' milestones';
  };

  const formatValue = (value, currency) => {
    return value.toLocaleString() + ' ' + currency;
  };

  return (
    <div>
      <div className="flex items-center justify-between gap-3 mb-6">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Contracts</h1>
          <p className="text-sm text-gray-500 mt-0.5">Client contracts and milestone tracking</p>
        </div>
        <button
          onClick={() => setShowNewModal(true)}
          className="flex items-center gap-1.5 bg-primary hover:bg-primary-dark text-white px-4 py-2.5 rounded-control text-sm font-medium transition-colors shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span className="hidden sm:inline">New Contract</span>
        </button>
      </div>

      {error && (
        <div className="mb-4 px-4 py-2.5 rounded-control bg-red-50 text-red-700 text-sm">
          {error}
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center py-20 text-gray-400">
          <Loader2 className="w-6 h-6 animate-spin" />
        </div>
      )}

      {!loading && contracts.length === 0 && (
        <div className="bg-white rounded-card shadow-soft border border-gray-100 p-12 text-center">
          <FileText className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-sm text-gray-500">No contracts yet. Create your first contract to get started.</p>
        </div>
      )}

      {!loading && contracts.length > 0 && (
        <div>
          <div className="hidden md:block bg-white rounded-card shadow-soft border border-gray-100 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">
                  <th className="px-5 py-3">Client</th>
                  <th className="px-5 py-3">Project</th>
                  <th className="px-5 py-3">Value</th>
                  <th className="px-5 py-3">Milestones</th>
                  <th className="px-5 py-3">Sales Rep</th>
                  <th className="px-5 py-3"></th>
                </tr>
              </thead>
              <tbody>
                {contracts.map((c) => (
                  <tr key={c.id} className="border-b border-gray-50 last:border-0 hover:bg-surface-subtle transition-colors">
                    <td className="px-5 py-3.5 font-medium text-gray-800">{c.client_name}</td>
                    <td className="px-5 py-3.5 text-gray-600">{c.project_name}</td>
                    <td className="px-5 py-3.5 text-gray-600">{formatValue(c.total_value, c.currency)}</td>
                    <td className="px-5 py-3.5 text-gray-600">{milestoneSummary(c)}</td>
                    <td className="px-5 py-3.5 text-gray-600">{c.sales_rep_name ? c.sales_rep_name : '—'}</td>
                    <td className="px-5 py-3.5 text-right">
                      <a href={'/contracts/' + c.contract_id} className="text-primary-light text-sm font-medium hover:underline">
                        View
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="md:hidden space-y-3">
            {contracts.map((c) => (
              <a
                key={c.id}
                href={'/contracts/' + c.contract_id}
                className="block bg-white rounded-card shadow-soft border border-gray-100 p-4"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-medium text-gray-800 text-sm">{c.client_name}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{c.project_name}</p>
                  </div>
                  <p className="text-sm font-semibold text-gray-800 whitespace-nowrap">
                    {formatValue(c.total_value, c.currency)}
                  </p>
                </div>
                <div className="flex items-center justify-between mt-3 text-xs text-gray-500">
                  <span>{milestoneSummary(c)}</span>
                  <span>{c.sales_rep_name ? c.sales_rep_name : '—'}</span>
                </div>
              </a>
            ))}
          </div>
        </div>
      )}

      {showNewModal && (
        <NewContractModal
          onClose={() => setShowNewModal(false)}
          onCreated={() => {
            setShowNewModal(false);
            loadContracts();
          }}
        />
      )}
    </div>
  );
};

export default Contracts;