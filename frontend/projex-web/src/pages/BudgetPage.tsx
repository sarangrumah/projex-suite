import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/services/api";
import { Modal } from "@/components/Modal";

interface BudgetItem {
  id: string;
  name: string;
  currency: string;
  total_amount: number;
  spent_amount: number;
  remaining: number;
  status: string;
  created_at: string;
}

interface BudgetDetail extends BudgetItem {
  description: string | null;
  line_items: Array<{
    id: string;
    category: string;
    description: string;
    quantity: number;
    unit_price: number;
    total_price: number;
  }>;
  invoices: Array<{
    id: string;
    invoice_number: string;
    amount: number;
    tax_amount: number;
    total_amount: number;
    status: string;
    due_date: string | null;
  }>;
}

const statusColors: Record<string, string> = {
  draft: "bg-slate-100 text-slate-600",
  active: "bg-green-100 text-green-700",
  closed: "bg-red-100 text-red-700",
  sent: "bg-blue-100 text-blue-700",
  paid: "bg-green-100 text-green-700",
  overdue: "bg-amber-100 text-amber-700",
  cancelled: "bg-red-100 text-red-700",
};

function formatCurrency(amount: number, currency: string) {
  return new Intl.NumberFormat("id-ID", { style: "currency", currency }).format(amount);
}

export default function BudgetPage() {
  const { spaceKey } = useParams<{ spaceKey: string }>();
  const qc = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [showAddItem, setShowAddItem] = useState(false);
  const [showInvoice, setShowInvoice] = useState(false);
  const [newName, setNewName] = useState("");
  const [itemCategory, setItemCategory] = useState("");
  const [itemDesc, setItemDesc] = useState("");
  const [itemQty, setItemQty] = useState("1");
  const [itemPrice, setItemPrice] = useState("");
  const [invAmount, setInvAmount] = useState("");

  const { data: budgets, isLoading } = useQuery({
    queryKey: ["budgets", spaceKey],
    queryFn: async () => {
      const res = await api.get(`/spaces/${spaceKey}/budgets`);
      return res.data.data as BudgetItem[];
    },
    enabled: !!spaceKey,
  });

  const { data: detail } = useQuery({
    queryKey: ["budget-detail", selectedId],
    queryFn: async () => {
      const res = await api.get(`/budgets/${selectedId}`);
      return res.data.data as BudgetDetail;
    },
    enabled: !!selectedId,
  });

  const createBudget = useMutation({
    mutationFn: async () => {
      const res = await api.post(`/spaces/${spaceKey}/budgets`, { name: newName });
      return res.data.data;
    },
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["budgets", spaceKey] });
      setSelectedId(data.id);
      setShowCreate(false);
      setNewName("");
    },
  });

  const addLineItem = useMutation({
    mutationFn: async () => {
      await api.post(`/budgets/${selectedId}/items`, {
        category: itemCategory,
        description: itemDesc,
        quantity: parseFloat(itemQty),
        unit_price: parseFloat(itemPrice),
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["budget-detail", selectedId] });
      qc.invalidateQueries({ queryKey: ["budgets", spaceKey] });
      setShowAddItem(false);
      setItemCategory("");
      setItemDesc("");
      setItemQty("1");
      setItemPrice("");
    },
  });

  const createInvoice = useMutation({
    mutationFn: async () => {
      await api.post(`/budgets/${selectedId}/invoices`, {
        amount: parseFloat(invAmount),
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["budget-detail", selectedId] });
      qc.invalidateQueries({ queryKey: ["budgets", spaceKey] });
      setShowInvoice(false);
      setInvAmount("");
    },
  });

  return (
    <div className="flex h-full">
      {/* Budget list */}
      <div className="w-64 border-r border-slate-200 bg-white flex flex-col flex-shrink-0">
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200">
          <h2 className="text-sm font-semibold text-text-primary">Budgets</h2>
          <button onClick={() => setShowCreate(true)} className="text-xs text-brand-blue hover:underline">
            + New
          </button>
        </div>
        <div className="flex-1 overflow-y-auto py-1">
          {isLoading && <p className="px-4 py-2 text-xs text-text-muted">Loading...</p>}
          {budgets?.map((b) => (
            <button
              key={b.id}
              onClick={() => setSelectedId(b.id)}
              className={`w-full text-left px-4 py-2 transition-colors ${
                selectedId === b.id ? "bg-brand-50 text-brand-blue" : "text-text-secondary hover:bg-slate-50"
              }`}
            >
              <span className="text-sm font-medium block">{b.name}</span>
              <span className="text-xs text-text-muted">{formatCurrency(b.total_amount, b.currency)}</span>
            </button>
          ))}
          {budgets && budgets.length === 0 && (
            <p className="px-4 py-4 text-xs text-text-muted text-center">No budgets yet</p>
          )}
        </div>
      </div>

      {/* Detail */}
      <div className="flex-1 overflow-y-auto p-6">
        {!selectedId && (
          <div className="flex items-center justify-center h-full text-text-muted text-sm">
            Select a budget or create a new one
          </div>
        )}

        {selectedId && detail && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h1 className="text-2xl font-bold text-text-primary">{detail.name}</h1>
                <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium mt-1 ${statusColors[detail.status]}`}>
                  {detail.status}
                </span>
              </div>
              <div className="text-right">
                <p className="text-xs text-text-muted">Total Budget</p>
                <p className="text-xl font-bold text-text-primary">{formatCurrency(detail.total_amount, detail.currency)}</p>
              </div>
            </div>

            {/* Summary cards */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <p className="text-xs text-text-muted">Spent</p>
                <p className="text-lg font-semibold text-status-warning">{formatCurrency(detail.spent_amount, detail.currency)}</p>
              </div>
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <p className="text-xs text-text-muted">Remaining</p>
                <p className="text-lg font-semibold text-status-success">{formatCurrency(detail.remaining, detail.currency)}</p>
              </div>
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <p className="text-xs text-text-muted">Utilization</p>
                <p className="text-lg font-semibold text-text-primary">
                  {detail.total_amount > 0 ? Math.round((detail.spent_amount / detail.total_amount) * 100) : 0}%
                </p>
              </div>
            </div>

            {/* Line Items */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-text-primary">Line Items</h3>
                <button onClick={() => setShowAddItem(true)} className="text-xs text-brand-blue hover:underline">+ Add</button>
              </div>
              {detail.line_items.length === 0 ? (
                <p className="text-xs text-text-muted">No line items yet</p>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 text-left text-xs text-text-muted">
                      <th className="py-2">Category</th>
                      <th>Description</th>
                      <th className="text-right">Qty</th>
                      <th className="text-right">Unit Price</th>
                      <th className="text-right">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detail.line_items.map((li) => (
                      <tr key={li.id} className="border-b border-slate-100">
                        <td className="py-2 text-text-secondary">{li.category}</td>
                        <td className="text-text-secondary">{li.description}</td>
                        <td className="text-right text-text-secondary">{li.quantity}</td>
                        <td className="text-right text-text-secondary">{formatCurrency(li.unit_price, detail.currency)}</td>
                        <td className="text-right font-medium">{formatCurrency(li.total_price, detail.currency)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {/* Invoices */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-text-primary">Invoices</h3>
                <button onClick={() => setShowInvoice(true)} className="text-xs text-brand-blue hover:underline">+ Generate</button>
              </div>
              {detail.invoices.length === 0 ? (
                <p className="text-xs text-text-muted">No invoices yet</p>
              ) : (
                <div className="flex flex-col gap-2">
                  {detail.invoices.map((inv) => (
                    <div key={inv.id} className="rounded-md border border-slate-200 bg-white p-3 flex items-center justify-between">
                      <div>
                        <span className="text-sm font-mono font-medium text-brand-blue">{inv.invoice_number}</span>
                        <span className={`ml-2 inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[inv.status]}`}>
                          {inv.status}
                        </span>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-semibold">{formatCurrency(inv.total_amount, detail.currency)}</p>
                        <p className="text-xs text-text-muted">Tax: {formatCurrency(inv.tax_amount, detail.currency)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Create Budget Modal */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Create Budget">
        <form onSubmit={(e) => { e.preventDefault(); createBudget.mutate(); }}>
          <input type="text" value={newName} onChange={(e) => setNewName(e.target.value)}
            placeholder="Budget name" required autoFocus
            className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm mb-4 focus:ring-2 focus:ring-brand-sky outline-none" />
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => setShowCreate(false)} className="rounded-md border border-slate-200 px-4 py-2 text-sm text-text-secondary">Cancel</button>
            <button type="submit" disabled={createBudget.isPending} className="rounded-md bg-brand-blue px-4 py-2 text-sm text-white disabled:opacity-50">Create</button>
          </div>
        </form>
      </Modal>

      {/* Add Line Item Modal */}
      <Modal open={showAddItem} onClose={() => setShowAddItem(false)} title="Add Line Item">
        <form onSubmit={(e) => { e.preventDefault(); addLineItem.mutate(); }} className="flex flex-col gap-3">
          <input type="text" value={itemCategory} onChange={(e) => setItemCategory(e.target.value)}
            placeholder="Category (e.g. Development)" required
            className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:ring-2 focus:ring-brand-sky outline-none" />
          <input type="text" value={itemDesc} onChange={(e) => setItemDesc(e.target.value)}
            placeholder="Description" required
            className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:ring-2 focus:ring-brand-sky outline-none" />
          <div className="flex gap-3">
            <input type="number" value={itemQty} onChange={(e) => setItemQty(e.target.value)}
              placeholder="Qty" min="0.1" step="0.1" required
              className="w-1/3 rounded-md border border-slate-200 px-3 py-2 text-sm focus:ring-2 focus:ring-brand-sky outline-none" />
            <input type="number" value={itemPrice} onChange={(e) => setItemPrice(e.target.value)}
              placeholder="Unit price" min="0" step="1000" required
              className="w-2/3 rounded-md border border-slate-200 px-3 py-2 text-sm focus:ring-2 focus:ring-brand-sky outline-none" />
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <button type="button" onClick={() => setShowAddItem(false)} className="rounded-md border border-slate-200 px-4 py-2 text-sm text-text-secondary">Cancel</button>
            <button type="submit" disabled={addLineItem.isPending} className="rounded-md bg-brand-blue px-4 py-2 text-sm text-white disabled:opacity-50">Add</button>
          </div>
        </form>
      </Modal>

      {/* Generate Invoice Modal */}
      <Modal open={showInvoice} onClose={() => setShowInvoice(false)} title="Generate Invoice">
        <form onSubmit={(e) => { e.preventDefault(); createInvoice.mutate(); }} className="flex flex-col gap-3">
          <input type="number" value={invAmount} onChange={(e) => setInvAmount(e.target.value)}
            placeholder="Invoice amount" min="1" step="1000" required autoFocus
            className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:ring-2 focus:ring-brand-sky outline-none" />
          <p className="text-xs text-text-muted">PPN 11% tax will be applied automatically</p>
          <div className="flex justify-end gap-2 pt-1">
            <button type="button" onClick={() => setShowInvoice(false)} className="rounded-md border border-slate-200 px-4 py-2 text-sm text-text-secondary">Cancel</button>
            <button type="submit" disabled={createInvoice.isPending} className="rounded-md bg-brand-blue px-4 py-2 text-sm text-white disabled:opacity-50">Generate</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
