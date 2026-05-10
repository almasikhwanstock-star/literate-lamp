import { RefreshCw, Trash2 } from 'lucide-react';

const FILTERS = [
  { key:'all',       label:'All'      },
  { key:'done',      label:'Done'     },
  { key:'error',     label:'Error'    },
  { key:'pending',   label:'Pending'  },
  { key:'analyzing', label:'Analyzing'},
];

const SORTS = [
  { key:'upload',   label:'Upload Order' },
  { key:'name_asc', label:'Name A–Z'     },
  { key:'name_desc',label:'Name Z–A'     },
  { key:'status',   label:'Status'       },
];

export default function FilterBar({ jobs, filter, sort, selected, allSelected, onFilter, onSort, onSelectAll, onDeleteSelected, onRetrySelected }) {
  const counts = FILTERS.reduce((acc, f) => {
    acc[f.key] = f.key === 'all' ? jobs.length : jobs.filter(j => j.status === f.key).length;
    return acc;
  }, {});
  const nSel = selected.length;

  return (
    <div className="card" style={{ padding:'9px 14px', display:'flex', alignItems:'center', gap:8, flexWrap:'wrap' }}>
      {/* Select all */}
      <label style={{ display:'flex', alignItems:'center', gap:6, cursor:'pointer', flexShrink:0 }}>
        <div className={`cb-box ${allSelected ? 'checked' : selected.length > 0 ? 'indeterminate' : ''}`} onClick={onSelectAll}>
          {allSelected
            ? <svg viewBox="0 0 10 8" width="9" height="9" fill="none" stroke="white" strokeWidth="2.5"><polyline points="1,4 3.5,6.5 9,1"/></svg>
            : selected.length > 0
            ? <div style={{ width:7, height:2, background:'white', borderRadius:1 }} />
            : null}
        </div>
        <span style={{ fontSize:12, color:'var(--text-secondary)', whiteSpace:'nowrap' }}>
          {nSel > 0 ? `${nSel} selected` : 'Select all'}
        </span>
      </label>

      {nSel > 0 && (
        <>
          <button className="btn btn-danger-soft btn-xs" onClick={onDeleteSelected}>
            <Trash2 size={11}/>Delete
          </button>
          <button className="btn btn-warning-soft btn-xs" onClick={onRetrySelected}>
            <RefreshCw size={11}/>Retry
          </button>
        </>
      )}

      <div style={{ width:1, height:18, background:'var(--border)', flexShrink:0, margin:'0 2px' }} />

      {/* Filter tabs */}
      <div style={{ display:'flex', gap:3, flexWrap:'wrap' }}>
        {FILTERS.map(f => (
          <button key={f.key} onClick={() => onFilter(f.key)}
            style={{
              fontSize:12, fontWeight:600, padding:'3px 10px', borderRadius:'var(--radius)', border:'1px solid transparent', cursor:'pointer',
              background: filter === f.key ? 'var(--accent-light)' : 'transparent',
              color: filter === f.key ? 'var(--accent)' : 'var(--text-secondary)',
              borderColor: filter === f.key ? 'var(--accent-border)' : 'transparent',
            }}>
            {f.label}
            {counts[f.key] > 0 && <span style={{ marginLeft:4, opacity:0.6, fontSize:10 }}>({counts[f.key]})</span>}
          </button>
        ))}
      </div>

      <div style={{ marginLeft:'auto', display:'flex', alignItems:'center', gap:6 }}>
        <span style={{ fontSize:11, fontWeight:700, color:'var(--text-tertiary)', textTransform:'uppercase', letterSpacing:'0.05em' }}>Sort</span>
        <select value={sort} onChange={e => onSort(e.target.value)}
          style={{ fontSize:12, padding:'4px 8px', border:'1px solid var(--border)', borderRadius:'var(--radius)', background:'var(--bg-surface-2)' }}>
          {SORTS.map(s => <option key={s.key} value={s.key}>{s.label}</option>)}
        </select>
      </div>
    </div>
  );
}
